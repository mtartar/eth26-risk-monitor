"""Validates the demo event sequence's decode + scoring trajectory, without the async bus.

Fast, no API key needed: decodes each demo block via the real AaveV2EventDecoder
and feeds it straight into a ScoringEngine, bypassing the bus/consumer-loop
machinery already covered by Phase 1/2's own tests. This is specifically
about pipeline.py's own demo data being correct.
"""

from monitor.ingestion.aave_v2_decoder import AaveV2EventDecoder
from monitor.pipeline import _demo_messages
from monitor.protocols.aave_v2_ethereum import AaveV2RiskModel
from monitor.protocols.models import NormalizedEvent
from monitor.scoring.price_oracle import StaticPriceOracle
from monitor.scoring.risk_state import RiskLevel
from monitor.scoring.scoring_engine import ScoringEngine

_WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
_USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"


def _decode_all(messages) -> list[NormalizedEvent]:
    decoder = AaveV2EventDecoder()
    events = []
    for message in messages:
        assert message.map_output is not None
        events.extend(decoder.decode(message.map_output))
    return events


def test_demo_messages_decode_to_exactly_four_events():
    """One event per demo block: Deposit, Borrow, Borrow, Repay."""
    events = _decode_all(_demo_messages())
    assert len(events) == 4


def test_demo_trajectory_matches_the_hand_verified_scenario():
    """Same SAFE -> WARNING -> DANGER -> SAFE trajectory as test_scoring_engine.py.

    Reuses that already-hand-verified scenario's numbers (1.29 -> 0.86 ->
    5.16) rather than re-deriving new ones, so this test is a check that
    pipeline.py's demo data matches a known-correct sequence, not a fresh
    arithmetic claim.
    """
    engine = ScoringEngine(
        price_oracle=StaticPriceOracle({_WETH: 3000.0, _USDC: 1.0}),
        risk_model=AaveV2RiskModel(),
    )
    events = _decode_all(_demo_messages())

    supply_transition = engine.process_event(events[0])
    assert supply_transition is None  # infinite health factor, still SAFE baseline

    into_warning = engine.process_event(events[1])
    assert into_warning is not None
    assert into_warning.to_level == RiskLevel.WARNING
    assert abs(into_warning.health_factor - 1.29) < 1e-9

    into_danger = engine.process_event(events[2])
    assert into_danger is not None
    assert into_danger.to_level == RiskLevel.DANGER
    assert abs(into_danger.health_factor - 0.86) < 1e-9

    back_to_safe = engine.process_event(events[3])
    assert back_to_safe is not None
    assert back_to_safe.to_level == RiskLevel.SAFE
    assert abs(back_to_safe.health_factor - 5.16) < 1e-9


def test_demo_events_all_reference_the_same_demo_user():
    """A sanity check that the demo data is internally consistent."""
    events = _decode_all(_demo_messages())
    addresses = {e.user_address for e in events}
    assert len(addresses) == 1
