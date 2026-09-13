"""Phase 4's exit condition: a real threshold crossing produces a real alert, end to end.

Runs the actual Pipeline (demo mode, since no SUBSTREAMS_API_TOKEN is set)
as a background task and waits a bounded amount of time for the 3 expected
real risk transitions (WARNING, DANGER, SAFE — see pipeline.py's demo
narrative) to flow all the way through scoring, the real AI explanation
call, and NullAlerter (no ALERT_WEBHOOK_URL configured in this environment).

Marked integration since it makes real Anthropic API calls (one explanation
per transition, plus one recommendation for the two at-risk transitions).
Run with: pytest -m integration
"""

import asyncio

import pytest

from monitor.alerting.webhook_alerter import NullAlerter
from monitor.config import settings
from monitor.pipeline import Pipeline

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not settings.anthropic_api_key, reason="ANTHROPIC_API_KEY not set"),
]


@pytest.mark.asyncio
async def test_demo_pipeline_produces_three_real_alerts_end_to_end():
    """WARNING, DANGER, then SAFE — each with a real AI explanation attached."""
    pipeline = Pipeline()
    assert isinstance(pipeline.alerter, NullAlerter)  # no webhook configured in this environment

    task = asyncio.create_task(pipeline.run())
    try:
        for _ in range(100):  # poll up to ~10s for the 3 demo transitions to finish processing
            if len(pipeline.alerter.sent) >= 3:
                break
            await asyncio.sleep(0.1)
    finally:
        task.cancel()

    alerts = pipeline.alerter.sent
    assert len(alerts) == 3
    assert "-> warning" in alerts[0]
    assert "-> danger" in alerts[1]
    assert "-> safe" in alerts[2]

    positions = pipeline.tracked_positions()
    assert len(positions) == 1
    assert abs(positions[0]["health_factor"] - 5.16) < 1e-6  # final state: back to safe
