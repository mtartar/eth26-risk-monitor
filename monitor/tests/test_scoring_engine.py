"""Integration test: ledger + real reserve config + risk model + hysteresis, wired together.

Uses hand-computed expected health factors so the assertions are a genuine
check of the arithmetic, not just "did it run."
"""

from datetime import datetime, timezone

from monitor.ingestion.event_bus import UndoSignal
from monitor.protocols.aave_risk_model import AaveRiskModel
from monitor.protocols.models import EventKind, NormalizedEvent
from monitor.scoring.price_oracle import StaticPriceOracle
from monitor.scoring.risk_state import RiskLevel
from monitor.scoring.scoring_engine import ScoringEngine

_USER = "0x1111111111111111111111111111111111111111"
_WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # liquidation_threshold=0.86, decimals=18
_USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # liquidation_threshold=0.875, decimals=6


def _event(kind: EventKind, block: int, reserve: str, amount_raw: str) -> NormalizedEvent:
    return NormalizedEvent(
        kind=kind,
        protocol="aave-v2",
        chain="ethereum",
        tx_hash=f"0xtx{block}",
        log_index=0,
        block_number=block,
        block_time=datetime.now(timezone.utc),
        user_address=_USER,
        reserve_address=reserve,
        amount_raw=amount_raw,
    )


def _engine() -> ScoringEngine:
    prices = StaticPriceOracle({_WETH: 3000.0, _USDC: 1.0})
    return ScoringEngine(price_oracle=prices, risk_model=AaveRiskModel())


def test_supplying_collateral_alone_reports_no_transition():
    """No debt means health factor is infinite — safe, no alert."""
    engine = _engine()
    supply_10_weth = _event(EventKind.SUPPLY, block=1, reserve=_WETH, amount_raw=str(10 * 10**18))
    assert engine.process_event(supply_10_weth) is None


def test_borrowing_into_warning_range_reports_the_transition():
    """10 WETH @ $3000 * 0.86 threshold = $25,800 weighted collateral.

    Borrowing $20,000 USDC: health factor = 25800 / 20000 = 1.29 -> WARNING
    (default thresholds: warning<=1.5, danger<=1.2).
    """
    engine = _engine()
    engine.process_event(
        _event(EventKind.SUPPLY, block=1, reserve=_WETH, amount_raw=str(10 * 10**18))
    )
    transition = engine.process_event(
        _event(EventKind.BORROW, block=2, reserve=_USDC, amount_raw=str(20_000 * 10**6))
    )
    assert transition is not None
    assert transition.to_level == RiskLevel.WARNING
    assert abs(transition.health_factor - 1.29) < 1e-9


def test_borrowing_further_into_danger_reports_that_transition_too():
    """Same position, borrowing to $30,000 total debt: 25800 / 30000 = 0.86 -> DANGER."""
    engine = _engine()
    engine.process_event(
        _event(EventKind.SUPPLY, block=1, reserve=_WETH, amount_raw=str(10 * 10**18))
    )
    engine.process_event(
        _event(EventKind.BORROW, block=2, reserve=_USDC, amount_raw=str(20_000 * 10**6))
    )
    transition = engine.process_event(
        _event(EventKind.BORROW, block=3, reserve=_USDC, amount_raw=str(10_000 * 10**6))
    )
    assert transition is not None
    assert transition.to_level == RiskLevel.DANGER
    assert abs(transition.health_factor - 0.86) < 1e-9


def test_repaying_back_to_safety_reports_the_recovery_transition():
    """From the $30,000-debt DANGER position, repaying $15,000 brings debt to $15,000.

    25800 / 15000 = 1.72 -> back to SAFE.
    """
    engine = _engine()
    engine.process_event(
        _event(EventKind.SUPPLY, block=1, reserve=_WETH, amount_raw=str(10 * 10**18))
    )
    engine.process_event(
        _event(EventKind.BORROW, block=2, reserve=_USDC, amount_raw=str(30_000 * 10**6))
    )
    transition = engine.process_event(
        _event(EventKind.REPAY, block=3, reserve=_USDC, amount_raw=str(15_000 * 10**6))
    )
    assert transition is not None
    assert transition.to_level == RiskLevel.SAFE
    assert abs(transition.health_factor - 1.72) < 1e-9


def test_reorg_undo_reverts_the_borrow_and_restores_the_prior_risk_level():
    """A reorg that invalidates the block-2 borrow should put the position back to SAFE.

    The hysteresis tracker isn't itself reset by process_undo — only the
    ledger is. That's correct, not a gap: the next real event recomputes the
    health factor from the (now-corrected) ledger, and since that differs
    from what was last reported (DANGER, based on the since-reorged borrow),
    hysteresis reports the correction as a genuine transition — exactly the
    behavior a real reorg should produce.
    """
    engine = _engine()
    engine.process_event(
        _event(EventKind.SUPPLY, block=1, reserve=_WETH, amount_raw=str(10 * 10**18))
    )
    engine.process_event(
        _event(EventKind.BORROW, block=2, reserve=_USDC, amount_raw=str(30_000 * 10**6))
    )  # -> DANGER

    engine.process_undo(UndoSignal(protocol="aave-v2", chain="ethereum", last_valid_block=1))

    # The chain's real block 2 turns out to have been a much smaller borrow.
    transition = engine.process_event(
        _event(EventKind.BORROW, block=2, reserve=_USDC, amount_raw=str(1_000 * 10**6))
    )
    assert transition is not None
    assert transition.from_level == RiskLevel.DANGER
    assert transition.to_level == RiskLevel.SAFE
    assert abs(transition.health_factor - 25.8) < 1e-9
