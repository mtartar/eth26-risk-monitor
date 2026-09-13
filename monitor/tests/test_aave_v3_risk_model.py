"""Tests for AaveV3RiskModel against Aave's documented health-factor formula."""

from datetime import datetime, timezone

from monitor.protocols.aave_v3_ethereum import AaveV3RiskModel
from monitor.protocols.models import PositionState


def _position(collateral: float, debt: float, threshold: float) -> PositionState:
    """Build a PositionState with the fields this test suite varies."""
    return PositionState(
        protocol="aave-v3",
        chain="ethereum",
        user_address="0x0000000000000000000000000000000000dEaD",
        total_collateral_usd=collateral,
        total_debt_usd=debt,
        liquidation_threshold=threshold,
        as_of_block=1,
        as_of_timestamp=datetime.now(timezone.utc),
    )


def test_healthy_position_scores_above_one():
    """(10000 * 0.8) / 4000 = 2.0 — well above the liquidation line."""
    model = AaveV3RiskModel()
    position = _position(collateral=10_000, debt=4_000, threshold=0.8)
    assert model.compute_health_factor(position) == 2.0


def test_position_at_exact_liquidation_threshold_scores_one():
    """(10000 * 0.8) / 8000 = 1.0 — exactly the liquidation boundary."""
    model = AaveV3RiskModel()
    position = _position(collateral=10_000, debt=8_000, threshold=0.8)
    assert model.compute_health_factor(position) == 1.0


def test_undercollateralized_position_scores_below_one():
    """(10000 * 0.8) / 9000 < 1.0 — eligible for liquidation."""
    model = AaveV3RiskModel()
    position = _position(collateral=10_000, debt=9_000, threshold=0.8)
    assert model.compute_health_factor(position) < 1.0


def test_debt_free_position_has_infinite_health_factor():
    """No debt means no liquidation risk, regardless of collateral."""
    model = AaveV3RiskModel()
    position = _position(collateral=10_000, debt=0, threshold=0.8)
    assert model.compute_health_factor(position) == float("inf")
