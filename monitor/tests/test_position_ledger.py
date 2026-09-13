"""Tests for PositionLedger: applying events, deriving balances, and reorg undo."""

from datetime import datetime, timezone

from monitor.protocols.models import EventKind, NormalizedEvent
from monitor.scoring.position_ledger import PositionLedger

_USER = "0x1111111111111111111111111111111111111111"
_RESERVE_A = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
_RESERVE_B = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def _event(kind: EventKind, block: int, reserve: str = _RESERVE_A, amount: str = "0", extra=None):
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
        amount_raw=amount,
        extra=extra or {},
    )


def test_supply_increases_collateral():
    """A Supply (SUPPLY kind) event adds to the reserve's raw collateral balance."""
    ledger = PositionLedger()
    ledger.apply(_event(EventKind.SUPPLY, block=1, amount="1000"))
    balances = ledger.raw_balances(_USER)
    assert balances[_RESERVE_A]["collateral_raw"] == 1000
    assert balances[_RESERVE_A]["debt_raw"] == 0


def test_withdraw_decreases_collateral():
    """A Withdraw fully or partially reverses prior Supply amounts."""
    ledger = PositionLedger()
    ledger.apply(_event(EventKind.SUPPLY, block=1, amount="1000"))
    ledger.apply(_event(EventKind.WITHDRAW, block=2, amount="400"))
    assert ledger.raw_balances(_USER)[_RESERVE_A]["collateral_raw"] == 600


def test_borrow_then_repay_nets_debt_to_zero():
    """Borrow increases debt; a matching Repay brings it back to zero."""
    ledger = PositionLedger()
    ledger.apply(_event(EventKind.BORROW, block=1, amount="500"))
    ledger.apply(_event(EventKind.REPAY, block=2, amount="500"))
    assert ledger.raw_balances(_USER)[_RESERVE_A]["debt_raw"] == 0


def test_tracks_multiple_reserves_independently():
    """Collateral in one reserve doesn't affect debt tracked in another."""
    ledger = PositionLedger()
    ledger.apply(_event(EventKind.SUPPLY, block=1, reserve=_RESERVE_A, amount="1000"))
    ledger.apply(_event(EventKind.BORROW, block=2, reserve=_RESERVE_B, amount="300"))
    balances = ledger.raw_balances(_USER)
    assert balances[_RESERVE_A] == {"collateral_raw": 1000, "debt_raw": 0}
    assert balances[_RESERVE_B] == {"collateral_raw": 0, "debt_raw": 300}


def test_liquidation_reduces_debt_reserve_and_seizes_collateral_reserve():
    """A liquidation can reduce debt in one reserve while seizing collateral in another."""
    ledger = PositionLedger()
    ledger.apply(_event(EventKind.SUPPLY, block=1, reserve=_RESERVE_A, amount="1000"))
    ledger.apply(_event(EventKind.BORROW, block=2, reserve=_RESERVE_B, amount="800"))
    ledger.apply(
        _event(
            EventKind.LIQUIDATION,
            block=3,
            reserve=_RESERVE_B,  # debt_asset
            amount="400",  # debt_to_cover
            extra={"collateral_asset": _RESERVE_A, "liquidated_collateral_amount": "450"},
        )
    )
    balances = ledger.raw_balances(_USER)
    assert balances[_RESERVE_A]["collateral_raw"] == 1000 - 450
    assert balances[_RESERVE_B]["debt_raw"] == 800 - 400


def test_ignores_events_for_other_users():
    """Another user's events never leak into this user's balances."""
    ledger = PositionLedger()
    other_user = "0x9999999999999999999999999999999999999999"
    other_event = _event(EventKind.SUPPLY, block=1, amount="1000")
    other_event = other_event.model_copy(update={"user_address": other_user})
    ledger.apply(other_event)
    assert ledger.raw_balances(_USER) == {}


def test_undo_reverts_events_after_the_given_block():
    """Reorg handling: undo(N) drops every applied event with block_number > N."""
    ledger = PositionLedger()
    ledger.apply(_event(EventKind.SUPPLY, block=1, amount="1000"))
    ledger.apply(_event(EventKind.SUPPLY, block=2, amount="500"))
    ledger.apply(_event(EventKind.SUPPLY, block=3, amount="200"))
    assert ledger.raw_balances(_USER)[_RESERVE_A]["collateral_raw"] == 1700

    ledger.undo(last_valid_block=2)

    assert ledger.raw_balances(_USER)[_RESERVE_A]["collateral_raw"] == 1500


def test_undo_then_reapply_matches_a_clean_run():
    """A reorg's corrected replay matches a clean run that never saw the bad block.

    After a reorg, replaying the corrected chain of events gives the same
    result as if the bad block had never been seen at all.
    """
    ledger_with_reorg = PositionLedger()
    ledger_with_reorg.apply(_event(EventKind.SUPPLY, block=1, amount="1000"))
    ledger_with_reorg.apply(_event(EventKind.SUPPLY, block=2, amount="999"))  # will be reorged out
    ledger_with_reorg.undo(last_valid_block=1)
    ledger_with_reorg.apply(_event(EventKind.SUPPLY, block=2, amount="500"))  # the real block 2

    clean_ledger = PositionLedger()
    clean_ledger.apply(_event(EventKind.SUPPLY, block=1, amount="1000"))
    clean_ledger.apply(_event(EventKind.SUPPLY, block=2, amount="500"))

    assert ledger_with_reorg.raw_balances(_USER) == clean_ledger.raw_balances(_USER)
