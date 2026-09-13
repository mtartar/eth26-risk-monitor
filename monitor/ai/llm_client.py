"""Shared Anthropic client construction for decision, explanation, and query services.

Same pattern as eth26-graph-trail/backend/services/llm_client.py: one place
that builds the client from settings, so every caller fails the same clear
way if the key is missing, rather than each duplicating the check.
"""

import anthropic

from monitor.config import settings


def get_anthropic_client() -> anthropic.Anthropic:
    """Build an Anthropic client from the configured API key."""
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY must be set to use the AI layer — this repo reuses "
            "eth26-graph-trail/.env for it by default, see monitor/config.py."
        )
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)
