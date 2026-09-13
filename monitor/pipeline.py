"""Orchestrates the full pipeline: ingestion -> scoring -> AI -> alerting -> broadcast.

This is where Phases 1-4's pieces are wired together into one runnable
system for the first time. Demo mode (no SUBSTREAMS_API_TOKEN — the default
in this environment, see docs/phase1_findings.md) replays a small,
clearly-synthetic event sequence so the dashboard has something to show
without live credentials, using the same honesty discipline as
FakeSubstreamsClient in Phase 1: never presented as real chain activity.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

from contract.v1 import contract_pb2  # importable via monitor/__init__.py's sys.path shim

from monitor.ai.decision import recommend_action
from monitor.ai.explanation import explain_transition
from monitor.alerting.webhook_alerter import Alerter, NullAlerter, WebhookAlerter
from monitor.config import settings
from monitor.ingestion.aave_v2_decoder import AaveV2EventDecoder
from monitor.ingestion.cursor_store import CursorStore
from monitor.ingestion.event_bus import InMemoryEventBus, UndoSignal
from monitor.ingestion.resilient_runner import run_with_retry
from monitor.ingestion.sink import SubstreamsSink
from monitor.ingestion.substreams_client import (
    FakeSubstreamsClient,
    GrpcSubstreamsClient,
    SubstreamsClient,
    SubstreamsMessage,
)
from monitor.observability.metrics import (
    ALERTS_SENT,
    EVENTS_PROCESSED,
    REORGS_HANDLED,
    RISK_TRANSITIONS,
)
from monitor.protocols.aave_v2_ethereum import AAVE_V2_ETHEREUM, AaveV2RiskModel
from monitor.protocols.models import EventKind
from monitor.scoring.price_oracle import StaticPriceOracle
from monitor.scoring.risk_state import RiskLevel, RiskTransition
from monitor.scoring.scoring_engine import ScoringEngine

logger = logging.getLogger("monitor.pipeline")

_CAUSE_BY_EVENT_KIND = {
    EventKind.SUPPLY: "new_supply",
    EventKind.WITHDRAW: "withdrawal",
    EventKind.BORROW: "new_borrow",
    EventKind.REPAY: "repayment",
    EventKind.LIQUIDATION: "liquidation",
}

_WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
_USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
_DEMO_USER = "0x1111111111111111111111111111111111111111"


def _demo_block(index: int, events: "contract_pb2.Events") -> SubstreamsMessage:
    return SubstreamsMessage(
        kind="block",
        cursor=f"demo-cursor-{index}",
        block_number=index,
        map_output=events.SerializeToString(),
    )


def _demo_messages() -> list[SubstreamsMessage]:
    """A small, clearly-synthetic SAFE -> WARNING -> DANGER -> SAFE narrative.

    Not real chain activity — see module docstring. Amounts match the
    hand-verified scenario in monitor/tests/test_scoring_engine.py so the
    demo's health-factor trajectory (1.29 -> 0.86 -> 5.16) is a known,
    checked sequence, not arbitrary numbers.
    """
    user = bytes.fromhex(_DEMO_USER[2:])
    weth = bytes.fromhex(_WETH[2:])
    usdc = bytes.fromhex(_USDC[2:])

    supply = contract_pb2.Events(
        deposits=[
            contract_pb2.Deposit(
                evt_tx_hash="0xdemo1", user=user, reserve=weth, amount=str(10 * 10**18)
            )
        ]
    )
    borrow_1 = contract_pb2.Events(
        borrows=[
            contract_pb2.Borrow(
                evt_tx_hash="0xdemo2", user=user, reserve=usdc, amount=str(20_000 * 10**6)
            )
        ]
    )
    borrow_2 = contract_pb2.Events(
        borrows=[
            contract_pb2.Borrow(
                evt_tx_hash="0xdemo3", user=user, reserve=usdc, amount=str(10_000 * 10**6)
            )
        ]
    )
    repay = contract_pb2.Events(
        repays=[
            contract_pb2.Repay(
                evt_tx_hash="0xdemo4", user=user, reserve=usdc, amount=str(25_000 * 10**6)
            )
        ]
    )
    return [
        _demo_block(1, supply),
        _demo_block(2, borrow_1),
        _demo_block(3, borrow_2),
        _demo_block(4, repay),
    ]


TransitionHandler = Callable[[RiskTransition, str | None], Awaitable[None]]


class Pipeline:
    """Wires ingestion, scoring, the AI layer, and alerting into one running system."""

    def __init__(self, on_transition: TransitionHandler | None = None):
        """Build the engine and alerter from settings; on_transition feeds the dashboard's WS."""
        self._engine = ScoringEngine(
            price_oracle=StaticPriceOracle({_WETH: 3000.0, _USDC: 1.0}),
            risk_model=AaveV2RiskModel(),
        )
        self._alerter: Alerter = (
            WebhookAlerter(settings.alert_webhook_url)
            if settings.alert_webhook_url
            else NullAlerter()
        )
        # Demo mode's cursor strings ("demo-cursor-N") aren't real chain state, so they get
        # an ephemeral, in-memory store rather than the persistent one real ingestion uses —
        # otherwise a second demo run would resume past the end of the finite demo sequence
        # and silently produce zero events. Found by running this pipeline twice in a row.
        cursor_db_path = settings.cursor_db_path if settings.substreams_api_token else ":memory:"
        self._decoder = AaveV2EventDecoder()
        self._cursor_store = CursorStore(cursor_db_path)
        self._bus = InMemoryEventBus()
        self._on_transition = on_transition

    def _build_client(self) -> SubstreamsClient:
        if settings.substreams_api_token:
            return GrpcSubstreamsClient(
                endpoint=settings.substreams_endpoint,
                api_token=settings.substreams_api_token,
                package_path="substreams_packages/aave-v2-lending-pool-v0.1.4.spkg",
                output_module=AAVE_V2_ETHEREUM.substreams.output_module,
            )
        logger.info("No SUBSTREAMS_API_TOKEN configured; running demo mode with synthetic events.")
        return FakeSubstreamsClient(_demo_messages())

    async def run(self) -> None:
        """Run ingestion (with retry) and the scoring/alerting consumer loop concurrently."""
        sink = SubstreamsSink(
            "aave-v2-ethereum",
            "aave-v2",
            "ethereum",
            self._build_client(),
            self._decoder,
            self._cursor_store,
            self._bus,
        )
        ingestion_task = asyncio.create_task(run_with_retry(sink))
        try:
            await self._consume_forever()
        finally:
            ingestion_task.cancel()

    async def _consume_forever(self) -> None:
        while True:
            message = await self._bus.get()
            if isinstance(message, UndoSignal):
                self._engine.process_undo(message)
                REORGS_HANDLED.inc()
                continue
            EVENTS_PROCESSED.labels(event_kind=message.kind.value).inc()
            transition = self._engine.process_event(message)
            if transition is not None:
                await self._handle_transition(transition, message.kind)

    async def _handle_transition(self, transition: RiskTransition, event_kind: EventKind) -> None:
        RISK_TRANSITIONS.labels(
            from_level=transition.from_level.value, to_level=transition.to_level.value
        ).inc()
        cause = _CAUSE_BY_EVENT_KIND.get(event_kind, "unknown")

        explanation = None
        recommendation = None
        if settings.anthropic_api_key:
            try:
                explanation = explain_transition(transition, cause=cause)
                if transition.to_level != RiskLevel.SAFE:
                    position = self._engine.current_position(
                        transition.user_address,
                        transition.as_of_block,
                        datetime.now(timezone.utc),
                    )
                    recommendation = recommend_action(position)
            except Exception:
                logger.exception("AI layer call failed; alerting without it")

        try:
            self._alerter.send(transition, explanation, recommendation)
            ALERTS_SENT.labels(status="ok").inc()
        except Exception:
            logger.exception("Alert delivery failed")
            ALERTS_SENT.labels(status="error").inc()

        if self._on_transition is not None:
            await self._on_transition(transition, explanation)

    def tracked_positions(self) -> list[dict]:
        """A simple snapshot of every tracked user's current health factor, for the dashboard."""
        now = datetime.now(timezone.utc)
        return [
            {
                "user_address": user,
                "health_factor": self._engine.current_health_factor(user, 0, now),
            }
            for user in sorted(self._engine.tracked_users())
        ]

    @property
    def engine(self) -> ScoringEngine:
        """The underlying ScoringEngine, for the NL query endpoint."""
        return self._engine

    @property
    def alerter(self) -> Alerter:
        """The configured Alerter (real webhook or NullAlerter), for tests/inspection."""
        return self._alerter
