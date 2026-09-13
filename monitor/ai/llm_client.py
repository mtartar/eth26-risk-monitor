"""Shared Anthropic client construction for decision, explanation, and query services.

Same pattern as eth26-graph-trail/backend/services/llm_client.py: one place
that builds the client from settings, so every caller fails the same clear
way if the key is missing, rather than each duplicating the check.
"""

import time
from collections.abc import Callable
from typing import TypeVar

import anthropic

from monitor.config import settings
from monitor.observability.cost_tracker import cost_tracker
from monitor.observability.metrics import LLM_CALL_DURATION

_ResponseT = TypeVar("_ResponseT")


def get_anthropic_client() -> anthropic.Anthropic:
    """Build an Anthropic client from the configured API key."""
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY must be set to use the AI layer — this repo reuses "
            "eth26-graph-trail/.env for it by default, see monitor/config.py."
        )
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def timed_call(kind: str, make_request: Callable[[], _ResponseT]) -> _ResponseT:
    """Run one real API call, recording its duration and real token cost.

    kind labels the Prometheus histogram (e.g. "decision", "explanation",
    "query_classify") so /metrics can break down latency per call type.
    """
    start = time.monotonic()
    response = make_request()
    LLM_CALL_DURATION.labels(kind=kind).observe(time.monotonic() - start)
    usage = getattr(response, "usage", None)
    if usage is not None:
        cost_tracker.record(usage.input_tokens, usage.output_tokens)
    return response
