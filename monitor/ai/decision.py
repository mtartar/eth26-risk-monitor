"""Recommends a corrective action, with the actual numbers computed in code, not by the model.

Two real options are always computed first (add collateral vs. repay debt to
reach a target health factor). Claude's forced tool-call is constrained to
return only a choice of *which* option ("add_collateral" | "repay_debt") and
a one-line rationale — the schema has no numeric field at all, so there is
no dollar amount for the model to invent or drift: amount_usd is always one
of our own precomputed values, selected by the model's choice. Same "compute
first, model narrates" discipline as eth26-graph-trail's nl_to_filter.py,
taken one step further since here the model can't emit a number even by
accident.
"""

from typing import Literal

from anthropic.types import ToolParam
from pydantic import BaseModel

from monitor.ai.llm_client import get_anthropic_client, timed_call
from monitor.config import settings
from monitor.protocols.models import PositionState

_TOOL_NAME = "recommend_action"

_TOOL_SCHEMA: ToolParam = {
    "name": _TOOL_NAME,
    "description": "Pick the better of two precomputed corrective actions and explain why.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add_collateral", "repay_debt"],
                "description": "Which of the two provided options to recommend.",
            },
            "rationale": {
                "type": "string",
                "description": "One sentence explaining the choice, plain English.",
            },
        },
        "required": ["action", "rationale"],
    },
}

_SYSTEM_PROMPT = (
    "You are choosing between two already-computed ways to fix an at-risk DeFi lending "
    "position: adding collateral, or repaying debt. Both amounts are given to you as facts "
    "you must not alter. Pick whichever requires the smaller dollar amount unless there's a "
    "clear practical reason to prefer the other (e.g. one option is $0, meaning no action of "
    "that kind is needed). Do not invent or adjust any number."
)


class RecommendedAction(BaseModel):
    """A corrective action, its real cost, and the resulting real health factor."""

    action: Literal["add_collateral", "repay_debt"]
    amount_usd: float
    resulting_health_factor: float
    rationale: str


def collateral_needed_for_target(position: PositionState, target_health_factor: float) -> float:
    """USD of additional collateral needed to reach target_health_factor, debt held fixed."""
    if position.liquidation_threshold <= 0:
        return float("inf")  # this reserve mix can never be made safe by adding more collateral
    required_weighted_collateral = target_health_factor * position.total_debt_usd
    current_weighted_collateral = position.total_collateral_usd * position.liquidation_threshold
    shortfall = required_weighted_collateral - current_weighted_collateral
    return max(shortfall / position.liquidation_threshold, 0.0)


def debt_to_repay_for_target(position: PositionState, target_health_factor: float) -> float:
    """USD of debt to repay to reach target_health_factor, collateral held fixed."""
    weighted_collateral = position.total_collateral_usd * position.liquidation_threshold
    required_debt = weighted_collateral / target_health_factor
    return max(position.total_debt_usd - required_debt, 0.0)


def recommend_action(
    position: PositionState, target_health_factor: float = 1.5
) -> RecommendedAction:
    """Compute both real corrective options, then ask Claude to pick and narrate one."""
    add_collateral_amount = collateral_needed_for_target(position, target_health_factor)
    repay_debt_amount = debt_to_repay_for_target(position, target_health_factor)

    client = get_anthropic_client()
    response = timed_call(
        "decision",
        lambda: client.messages.create(
            model=settings.anthropic_model,
            max_tokens=200,
            system=_SYSTEM_PROMPT,
            tools=[_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Option A (add_collateral): ${add_collateral_amount:,.2f}\n"
                        f"Option B (repay_debt): ${repay_debt_amount:,.2f}\n"
                        f"Target health factor: {target_health_factor}"
                    ),
                }
            ],
        ),
    )
    tool_use = next(block for block in response.content if block.type == "tool_use")
    extracted = tool_use.input
    assert isinstance(extracted, dict)  # guaranteed by the forced tool schema above

    action = extracted.get("action")
    rationale = extracted.get("rationale")
    if not isinstance(action, str) or action not in ("add_collateral", "repay_debt"):
        action = "add_collateral" if add_collateral_amount <= repay_debt_amount else "repay_debt"
    if not isinstance(rationale, str):
        rationale = "Selected the lower-cost option."

    amount_usd = add_collateral_amount if action == "add_collateral" else repay_debt_amount
    return RecommendedAction(
        action=action,
        amount_usd=amount_usd,
        resulting_health_factor=target_health_factor,
        rationale=rationale,
    )
