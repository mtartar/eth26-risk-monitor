"""Sends a RiskTransition (plus its AI explanation/recommendation) to a webhook.

Uses Slack's incoming-webhook JSON format ({"text": "..."}), which Discord's
webhook endpoint also accepts as a plain message — one implementation covers
both without a payload-format branch.

No real webhook URL was available while building this (see
docs/phase4_findings.md) — the HTTP POST logic is straightforward and tested
against a mocked endpoint, but live delivery to a real Slack/Discord channel
is not independently verified. Alerter is a Protocol specifically so a
missing ALERT_WEBHOOK_URL degrades to NullAlerter rather than crashing the
pipeline — the same graceful-fallback shape used throughout this project.
"""

from typing import Protocol

import httpx

from monitor.ai.decision import RecommendedAction
from monitor.scoring.risk_state import RiskLevel, RiskTransition

_LEVEL_EMOJI = {
    RiskLevel.SAFE: "🟢",
    RiskLevel.WARNING: "🟡",
    RiskLevel.DANGER: "🔴",
}


def _format_message(
    transition: RiskTransition,
    explanation: str | None,
    recommendation: RecommendedAction | None,
) -> str:
    """Build the plain-text alert body shared by every Alerter implementation."""
    emoji = _LEVEL_EMOJI.get(transition.to_level, "⚠️")
    lines = [
        f"{emoji} *{transition.user_address}* moved "
        f"{transition.from_level.value} -> {transition.to_level.value} "
        f"(health factor {transition.health_factor:.3f}, block {transition.as_of_block})"
    ]
    if explanation:
        lines.append(explanation)
    if recommendation is not None:
        lines.append(
            f"Recommended: {recommendation.action.replace('_', ' ')} "
            f"${recommendation.amount_usd:,.2f} -> health factor "
            f"{recommendation.resulting_health_factor:.2f}. {recommendation.rationale}"
        )
    return "\n".join(lines)


class Alerter(Protocol):
    """Delivers a formatted risk alert somewhere a human will see it."""

    def send(
        self,
        transition: RiskTransition,
        explanation: str | None = None,
        recommendation: RecommendedAction | None = None,
    ) -> None:
        """Deliver one alert."""
        ...


class WebhookAlerter:
    """POSTs a formatted risk-transition alert to a Slack/Discord-compatible webhook."""

    def __init__(self, webhook_url: str, timeout: float = 10.0):
        """Store the webhook URL to post alerts to."""
        self._webhook_url = webhook_url
        self._timeout = timeout

    def send(
        self,
        transition: RiskTransition,
        explanation: str | None = None,
        recommendation: RecommendedAction | None = None,
    ) -> None:
        """POST one alert. Raises on a non-2xx response — callers decide how to handle that."""
        message = _format_message(transition, explanation, recommendation)
        response = httpx.post(self._webhook_url, json={"text": message}, timeout=self._timeout)
        response.raise_for_status()


class NullAlerter:
    """No-op Alerter for when no webhook is configured — degrade, don't crash."""

    def __init__(self) -> None:
        """Record every alert that would have been sent, for inspection in tests/logs."""
        self.sent: list[str] = []

    def send(
        self,
        transition: RiskTransition,
        explanation: str | None = None,
        recommendation: RecommendedAction | None = None,
    ) -> None:
        """Record the formatted message instead of delivering it anywhere."""
        self.sent.append(_format_message(transition, explanation, recommendation))
