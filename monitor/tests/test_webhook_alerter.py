"""Tests for WebhookAlerter/NullAlerter — HTTP mocked, no real webhook needed.

Live delivery to a real Slack/Discord channel is not independently verified
(no webhook URL was available while building this) — see
docs/phase4_findings.md. What's tested here is real: the payload shape and
the raise-on-failure behavior.
"""

from unittest.mock import Mock, patch

from monitor.ai.decision import RecommendedAction
from monitor.alerting.webhook_alerter import NullAlerter, WebhookAlerter
from monitor.scoring.risk_state import RiskLevel, RiskTransition

_TRANSITION = RiskTransition(
    user_address="0x1111111111111111111111111111111111111111",
    from_level=RiskLevel.SAFE,
    to_level=RiskLevel.DANGER,
    health_factor=0.86,
    as_of_block=100,
)


def test_webhook_alerter_posts_slack_compatible_json_payload():
    """The POST body is Slack's {"text": ...} shape, which Discord also accepts."""
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None

    with patch("monitor.alerting.webhook_alerter.httpx.post", return_value=mock_response) as post:
        WebhookAlerter("https://example.com/webhook").send(_TRANSITION)

    args, kwargs = post.call_args
    assert args[0] == "https://example.com/webhook"
    assert "text" in kwargs["json"]
    assert "0x1111111111111111111111111111111111111111" in kwargs["json"]["text"]
    assert "SAFE" in kwargs["json"]["text"] or "safe" in kwargs["json"]["text"]


def test_webhook_alerter_includes_explanation_and_recommendation_when_given():
    """Extra context, when provided, ends up in the alert body."""
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    recommendation = RecommendedAction(
        action="add_collateral", amount_usd=1234.56, resulting_health_factor=1.5, rationale="test"
    )

    with patch("monitor.alerting.webhook_alerter.httpx.post", return_value=mock_response) as post:
        WebhookAlerter("https://example.com/webhook").send(
            _TRANSITION, explanation="ETH price dropped.", recommendation=recommendation
        )

    text = post.call_args.kwargs["json"]["text"]
    assert "ETH price dropped." in text
    assert "1,234.56" in text


def test_webhook_alerter_raises_on_a_failed_delivery():
    """A non-2xx response propagates — the caller (pipeline.py) decides how to handle it."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = RuntimeError("simulated 500")

    with patch("monitor.alerting.webhook_alerter.httpx.post", return_value=mock_response):
        try:
            WebhookAlerter("https://example.com/webhook").send(_TRANSITION)
            raised = False
        except RuntimeError:
            raised = True
    assert raised


def test_null_alerter_records_instead_of_sending():
    """NullAlerter never makes a network call — it just remembers what would have been sent."""
    alerter = NullAlerter()
    alerter.send(_TRANSITION)
    assert len(alerter.sent) == 1
    assert "0x1111111111111111111111111111111111111111" in alerter.sent[0]
