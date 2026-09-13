"""Plain-English explanation of why a position's risk level changed.

One plain-text call (no tool use, nothing to select) — same "narrate real
data, don't invent any" discipline as eth26-graph-trail's narrative.py. The
cause and every number are facts computed elsewhere and handed in; the model
is asked to explain, not to determine what happened.
"""

from monitor.ai.llm_client import get_anthropic_client, timed_call
from monitor.config import settings
from monitor.scoring.risk_state import RiskTransition

_SYSTEM_PROMPT = (
    "You explain, in one or two plain-English sentences, why a DeFi lending position's "
    "risk level changed. You are given the real cause and real supporting numbers below — "
    "use only those; don't invent additional figures, causes, or hedge with speculation."
)


def explain_transition(
    transition: RiskTransition, cause: str, context: dict[str, str] | None = None
) -> str:
    """Narrate a real RiskTransition, given its real cause and any supporting facts."""
    facts = [
        f"Risk level changed from {transition.from_level.value} to {transition.to_level.value}.",
        f"New health factor: {transition.health_factor:.3f}.",
        f"Cause: {cause}.",
    ]
    for key, value in (context or {}).items():
        facts.append(f"{key}: {value}")

    client = get_anthropic_client()
    response = timed_call(
        "explanation",
        lambda: client.messages.create(
            model=settings.anthropic_model,
            max_tokens=150,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": "\n".join(facts)}],
        ),
    )
    return "".join(block.text for block in response.content if block.type == "text")
