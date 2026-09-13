"""Health-factor math shared by every Aave version (v2, v3, ...).

The formula itself is Aave-family-wide, not version-specific — confirmed
against Aave v3's getUserAccountData() docs (aave.com/docs/aave-v3/smart-contracts/pool)
and structurally unchanged since v2. One shared implementation avoids the two
Aave configs silently drifting out of sync with each other.
"""

from monitor.protocols.models import PositionState


class AaveRiskModel:
    """Aave's health factor: (collateral * liquidationThreshold) / debt."""

    def compute_health_factor(self, position: PositionState) -> float:
        """Return infinity for a debt-free position rather than dividing by zero."""
        if position.total_debt_usd == 0:
            return float("inf")
        weighted_collateral = position.total_collateral_usd * position.liquidation_threshold
        return weighted_collateral / position.total_debt_usd
