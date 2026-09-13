"""Tests for HysteresisTracker: report real transitions, suppress noise."""

from monitor.scoring.risk_state import HysteresisTracker, RiskLevel

_USER = "0x1111111111111111111111111111111111111111"


def test_first_observation_at_safe_level_reports_no_transition():
    """Starting out safe is the implicit baseline — nothing to report."""
    tracker = HysteresisTracker()
    assert tracker.update(_USER, health_factor=2.0, as_of_block=1) is None


def test_first_observation_already_risky_reports_a_transition():
    """A newly-tracked, already-risky position should alert immediately.

    Not be suppressed as 'no prior state to compare against'.
    """
    tracker = HysteresisTracker()
    transition = tracker.update(_USER, health_factor=1.1, as_of_block=1)
    assert transition is not None
    assert transition.from_level == RiskLevel.SAFE
    assert transition.to_level == RiskLevel.DANGER


def test_small_fluctuation_within_the_same_level_reports_nothing():
    """Wobbling between 1.8 and 1.6 (both SAFE, default threshold 1.5) fires no alert."""
    tracker = HysteresisTracker()
    assert tracker.update(_USER, health_factor=1.8, as_of_block=1) is None
    assert tracker.update(_USER, health_factor=1.6, as_of_block=2) is None
    assert tracker.update(_USER, health_factor=1.9, as_of_block=3) is None


def test_crossing_into_warning_then_back_to_safe_reports_both_transitions():
    """A real round trip through WARNING reports exactly two transitions, not zero or four."""
    tracker = HysteresisTracker()
    assert tracker.update(_USER, health_factor=2.0, as_of_block=1) is None

    into_warning = tracker.update(_USER, health_factor=1.4, as_of_block=2)
    assert into_warning is not None
    assert (into_warning.from_level, into_warning.to_level) == (RiskLevel.SAFE, RiskLevel.WARNING)

    # still WARNING, no new transition
    assert tracker.update(_USER, health_factor=1.3, as_of_block=3) is None

    back_to_safe = tracker.update(_USER, health_factor=1.8, as_of_block=4)
    assert back_to_safe is not None
    assert (back_to_safe.from_level, back_to_safe.to_level) == (RiskLevel.WARNING, RiskLevel.SAFE)


def test_dropping_straight_into_danger_reports_one_transition_not_two():
    """SAFE -> DANGER in one step is one transition, skipping WARNING entirely.

    Not two separate SAFE->WARNING and WARNING->DANGER events.
    """
    tracker = HysteresisTracker()
    tracker.update(_USER, health_factor=2.0, as_of_block=1)
    transition = tracker.update(_USER, health_factor=0.9, as_of_block=2)
    assert transition is not None
    assert (transition.from_level, transition.to_level) == (RiskLevel.SAFE, RiskLevel.DANGER)


def test_tracks_multiple_users_independently():
    """One user's risk level never affects another user's tracked state."""
    tracker = HysteresisTracker()
    user_a = _USER
    user_b = "0x2222222222222222222222222222222222222222"

    tracker.update(user_a, health_factor=0.9, as_of_block=1)  # A is now DANGER
    transition_b = tracker.update(user_b, health_factor=2.0, as_of_block=1)  # B stays SAFE

    assert transition_b is None
