"""Ties the ledger, price oracle, risk model, and hysteresis into one engine.

process_event/process_undo are the pure core (no I/O, directly testable in
isolation) — matching poc-thegraph/04_implementation_plan.md Phase 2's own
instruction to build health-factor computation "as a pure function first."
run() is the thin async wrapper that does the actual I/O (reading the event
bus) for real usage; it isn't itself unit-tested since it's a two-line
dispatch over already-tested pure methods.
"""

from collections.abc import AsyncIterator
from datetime import datetime

from monitor.ingestion.event_bus import EventBus, UndoSignal
from monitor.protocols.models import NormalizedEvent, RiskModel
from monitor.scoring.position_ledger import PositionLedger
from monitor.scoring.price_oracle import PriceOracle
from monitor.scoring.risk_state import HysteresisTracker, RiskTransition


class ScoringEngine:
    """Consumes events/undo signals, maintains position state, reports risk-level transitions."""

    def __init__(
        self,
        price_oracle: PriceOracle,
        risk_model: RiskModel,
        hysteresis: HysteresisTracker | None = None,
    ):
        """Wire up collaborators; hysteresis defaults to the standard 1.5/1.2 thresholds."""
        self._price_oracle = price_oracle
        self._risk_model = risk_model
        self._hysteresis = hysteresis or HysteresisTracker()
        self._ledger = PositionLedger()

    def process_event(self, event: NormalizedEvent) -> RiskTransition | None:
        """Apply one event to the ledger; return a transition if the user's risk level changed."""
        if event.user_address is None:
            return None
        self._ledger.apply(event)
        position = self._ledger.position_state(
            event.user_address,
            self._price_oracle,
            as_of_block=event.block_number,
            as_of_timestamp=event.block_time,
            protocol=event.protocol,
            chain=event.chain,
        )
        health_factor = self._risk_model.compute_health_factor(position)
        return self._hysteresis.update(event.user_address, health_factor, event.block_number)

    def process_undo(self, undo: UndoSignal) -> None:
        """Revert the ledger to its state as of last_valid_block."""
        self._ledger.undo(undo.last_valid_block)

    def current_health_factor(
        self, user_address: str, as_of_block: int, as_of_timestamp: datetime
    ) -> float:
        """Compute a user's current health factor without applying a new event.

        For inspecting state between events (e.g. in tests confirming a
        position was already liquidatable before the liquidation event
        itself is applied) — doesn't touch hysteresis, since no new
        observation is being "reported."
        """
        position = self._ledger.position_state(
            user_address, self._price_oracle, as_of_block, as_of_timestamp
        )
        return self._risk_model.compute_health_factor(position)

    async def run(self, event_bus: EventBus) -> AsyncIterator[RiskTransition]:
        """Consume the bus forever, yielding only actual risk-level transitions."""
        while True:
            message = await event_bus.get()
            if isinstance(message, UndoSignal):
                self.process_undo(message)
                continue
            transition = self.process_event(message)
            if transition is not None:
                yield transition
