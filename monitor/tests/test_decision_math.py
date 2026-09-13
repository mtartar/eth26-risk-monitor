"""Tests for the pure math in decision.py — no LLM call, no mocking needed."""

from datetime import datetime, timezone

from monitor.ai.decision import collateral_needed_for_target, debt_to_repay_for_target
from monitor.protocols.models import PositionState


def _position(collateral: float, debt: float, threshold: float) -> PositionState:
    return PositionState(
        protocol="aave-v2",
        chain="ethereum",
        user_address="0x1111111111111111111111111111111111111111",
        total_collateral_usd=collateral,
        total_debt_usd=debt,
        liquidation_threshold=threshold,
        as_of_block=1,
        as_of_timestamp=datetime.now(timezone.utc),
    )


def test_collateral_needed_for_target_matches_hand_calculation():
    """collateral=$25,714.29 weighted, debt=$20,000 -> hf=1.286; target 1.5 needs more collateral.

    target_hf * debt = 1.5 * 20000 = 30000 required weighted collateral.
    current weighted = 30000/1.5*0.86... use round numbers instead: collateral=$30,000,
    threshold=0.86, debt=$20,000 -> weighted=25800, hf=1.29. To reach hf=1.5 needs
    weighted=30000, so shortfall=4200, extra_collateral = 4200/0.86 = 4883.72...
    """
    position = _position(collateral=30_000, debt=20_000, threshold=0.86)
    extra = collateral_needed_for_target(position, target_health_factor=1.5)
    assert abs(extra - (4200 / 0.86)) < 1e-6


def test_collateral_needed_for_target_is_zero_when_already_safe():
    """A position already above the target needs no additional collateral."""
    position = _position(collateral=100_000, debt=1_000, threshold=0.86)
    assert collateral_needed_for_target(position, target_health_factor=1.5) == 0.0


def test_collateral_needed_for_target_is_infinite_with_zero_threshold():
    """A reserve mix with liquidation_threshold=0 can never be made safe this way.

    E.g. all-USDT collateral — that's a real, not a divide-by-zero-crash, case.
    """
    position = _position(collateral=10_000, debt=5_000, threshold=0.0)
    assert collateral_needed_for_target(position, target_health_factor=1.5) == float("inf")


def test_debt_to_repay_for_target_matches_hand_calculation():
    """Same $30,000/0.86/$20,000 position: required_debt = 25800/1.5 = 17200.

    repay = 20000 - 17200 = 2800.
    """
    position = _position(collateral=30_000, debt=20_000, threshold=0.86)
    repay = debt_to_repay_for_target(position, target_health_factor=1.5)
    assert abs(repay - 2800) < 1e-6


def test_debt_to_repay_for_target_is_zero_when_already_safe():
    """A position already above the target needs no repayment."""
    position = _position(collateral=100_000, debt=1_000, threshold=0.86)
    assert debt_to_repay_for_target(position, target_health_factor=1.5) == 0.0


def test_both_options_reach_exactly_the_target_health_factor():
    """Applying either computed option should land exactly at the target health factor.

    The real cross-check that these formulas are actually inverses of the HF formula.
    """
    position = _position(collateral=30_000, debt=20_000, threshold=0.86)
    target = 1.5

    extra_collateral = collateral_needed_for_target(position, target)
    new_collateral = position.total_collateral_usd + extra_collateral
    hf_via_collateral = new_collateral * 0.86 / position.total_debt_usd
    assert abs(hf_via_collateral - target) < 1e-9

    repay = debt_to_repay_for_target(position, target)
    hf_via_repay = position.total_collateral_usd * 0.86 / (position.total_debt_usd - repay)
    assert abs(hf_via_repay - target) < 1e-9
