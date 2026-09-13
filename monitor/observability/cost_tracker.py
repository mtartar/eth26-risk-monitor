"""Tracks real LLM token usage and converts it to an estimated dollar cost.

Token counts come straight from each Anthropic response's `usage` field —
real, not estimated. The dollar conversion uses a documented, dated rate
(Claude Haiku 4.5: $1 / $5 per million input/output tokens — checked
Sept 2026 against multiple independent pricing-tracker sites, see
docs/phase5_findings.md) — labeled as an estimate since pricing can change;
verify against current official pricing before trusting this for real
budgeting.

GRT query fees and cloud compute cost are not tracked here: nothing in this
project talks to a live, paid Substreams endpoint or runs on paid cloud
infrastructure (see docs/phase1_findings.md), so both are genuinely $0 right
now, not omitted.
"""

from dataclasses import dataclass

_INPUT_COST_PER_MILLION_TOKENS = 1.00  # USD, Claude Haiku 4.5, checked Sept 2026
_OUTPUT_COST_PER_MILLION_TOKENS = 5.00  # USD, Claude Haiku 4.5, checked Sept 2026


@dataclass
class CostTracker:
    """Accumulates real token counts and derives an estimated USD total."""

    input_tokens: int = 0
    output_tokens: int = 0
    call_count: int = 0

    def record(self, input_tokens: int, output_tokens: int) -> None:
        """Add one real API call's token usage."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.call_count += 1

    @property
    def estimated_usd(self) -> float:
        """Estimated USD cost so far, at the documented per-token rate."""
        input_cost = self.input_tokens / 1_000_000 * _INPUT_COST_PER_MILLION_TOKENS
        output_cost = self.output_tokens / 1_000_000 * _OUTPUT_COST_PER_MILLION_TOKENS
        return input_cost + output_cost


cost_tracker = CostTracker()
