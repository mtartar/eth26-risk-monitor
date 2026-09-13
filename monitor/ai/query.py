"""Natural-language questions over live tracked positions.

Same two-call shape as eth26-graph-trail's nl_to_filter.py + narrative.py:
a forced tool-call classifies intent into a narrow, known set (not
open-ended query generation), the real answer is computed from the engine's
actual tracked state, then a second plain-text call narrates only that real
data.
"""

from datetime import datetime

from anthropic.types import ToolParam

from monitor.ai.llm_client import get_anthropic_client
from monitor.config import settings
from monitor.scoring.scoring_engine import ScoringEngine

_TOOL_NAME = "classify_position_query"

_TOOL_SCHEMA: ToolParam = {
    "name": _TOOL_NAME,
    "description": "Classify a question about tracked DeFi lending positions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["riskiest_position", "position_for_user"],
                "description": (
                    "riskiest_position: asking which tracked position is riskiest "
                    "overall. position_for_user: asking about one specific address."
                ),
            },
            "user_address": {
                "type": ["string", "null"],
                "description": "The 0x address asked about, if position_for_user. Null otherwise.",
            },
        },
        "required": ["intent"],
    },
}

_CLASSIFY_SYSTEM_PROMPT = (
    "You classify a question about tracked DeFi lending positions into one of two known "
    "intents. Extract only what's explicitly stated or clearly implied."
)

_ANSWER_SYSTEM_PROMPT = (
    "Answer the question using only the real data provided below — don't invent positions, "
    "addresses, or health factors not listed. A LOWER health factor means a RISKIER position "
    "(a value below 1.0 is eligible for liquidation); a higher value is safer. One or two "
    "plain-English sentences, naming the specific address(es) the answer is about."
)


def answer_position_query(
    question: str, engine: ScoringEngine, as_of_block: int, as_of_timestamp: datetime
) -> str:
    """Answer a plain-English question about tracked positions using real engine state."""
    client = get_anthropic_client()
    classify_response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=200,
        system=_CLASSIFY_SYSTEM_PROMPT,
        tools=[_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": _TOOL_NAME},
        messages=[{"role": "user", "content": question}],
    )
    tool_use = next(block for block in classify_response.content if block.type == "tool_use")
    extracted = tool_use.input
    assert isinstance(extracted, dict)  # guaranteed by the forced tool schema above

    user_address = extracted.get("user_address")
    if extracted.get("intent") == "position_for_user" and isinstance(user_address, str):
        users_to_check = [user_address]
    else:
        users_to_check = sorted(engine.tracked_users())

    if not users_to_check:
        return "No positions are currently being tracked."

    health_factors = [
        (user, engine.current_health_factor(user, as_of_block, as_of_timestamp))
        for user in users_to_check
    ]
    facts = "\n".join(f"{user}: health factor {hf:.3f}" for user, hf in health_factors)

    answer_response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=150,
        system=_ANSWER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Question: {question}\n\nReal data:\n{facts}"}],
    )
    return "".join(block.text for block in answer_response.content if block.type == "text")
