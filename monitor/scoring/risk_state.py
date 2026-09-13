"""Hysteresis: only report a risk-level change, never every recomputed health factor.

Without this, a health factor wobbling around 1.5 would fire an alert on
every single recompute — the classic alert-fatigue failure mode flagged in
01_context_and_mechanism.md §4 step 4. HysteresisTracker remembers each
user's last reported level and only returns a RiskTransition when the level
actually changes.
"""

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    """Three-tier risk classification, coarser than the raw health factor."""

    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"


@dataclass
class RiskTransition:
    """One user's risk level actually changing, worth alerting on."""

    user_address: str
    from_level: RiskLevel
    to_level: RiskLevel
    health_factor: float
    as_of_block: int


class HysteresisTracker:
    """Classifies a health factor into a RiskLevel and reports only real transitions.

    A user's first-ever observation is compared against an implicit SAFE
    baseline: if a position is already WARNING/DANGER the moment it's first
    tracked, that's reported as a transition too — a newly-tracked risky
    position is exactly the case worth surfacing immediately, not suppressing
    as "no prior state to compare against."
    """

    def __init__(self, warning_threshold: float = 1.5, danger_threshold: float = 1.2):
        """Set the two health-factor cutoffs; danger_threshold must be <= warning_threshold."""
        self._warning_threshold = warning_threshold
        self._danger_threshold = danger_threshold
        self._last_level: dict[str, RiskLevel] = {}

    def _classify(self, health_factor: float) -> RiskLevel:
        """Map a raw health factor onto one of the three risk levels."""
        if health_factor <= self._danger_threshold:
            return RiskLevel.DANGER
        if health_factor <= self._warning_threshold:
            return RiskLevel.WARNING
        return RiskLevel.SAFE

    def update(
        self, user_address: str, health_factor: float, as_of_block: int
    ) -> RiskTransition | None:
        """Record this observation and return a RiskTransition only if the level changed."""
        new_level = self._classify(health_factor)
        old_level = self._last_level.get(user_address, RiskLevel.SAFE)
        self._last_level[user_address] = new_level

        if new_level == old_level:
            return None
        return RiskTransition(
            user_address=user_address,
            from_level=old_level,
            to_level=new_level,
            health_factor=health_factor,
            as_of_block=as_of_block,
        )
