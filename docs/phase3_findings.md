# Phase 3 findings — AI reasoning layer

## Key reuse decision: the Anthropic key comes from eth26-graph-trail/.env

`monitor/config.py` loads `env_file=("/home/numrise/eth26-graph-trail/.env", ".env")` — the sibling Graph Trail project's already-verified working `ANTHROPIC_API_KEY` is reused directly rather than asking for a second key on the same account. This repo's own `.env` (if it sets the key itself) still takes precedence since it's loaded second. A missing sibling file is not an error — pydantic-settings skips it silently — so this stays harmless on a machine that doesn't have that other repo checked out; it just falls back to needing a local `.env` entry instead.

## Design: the decision layer's tool schema has no numeric field at all

`recommend_action()` computes both real corrective options in code first (`collateral_needed_for_target`, `debt_to_repay_for_target` — pure functions, unit-tested with hand-verified arithmetic in `test_decision_math.py`). Claude's forced tool-call schema (`monitor/ai/decision.py`) only accepts `action: "add_collateral" | "repay_debt"` and a `rationale` string — **there is no `amount_usd` field in the schema at all**. This is one step past Graph Trail's "compute first, model narrates" discipline: rather than validating the model's returned number against our own after the fact, the model is structurally incapable of returning a number, so there's nothing to invent or drift.

## Design: NL query reuses Graph Trail's two-call shape exactly

`answer_position_query()` in `monitor/ai/query.py`:
1. A forced tool-call classifies the question into one of two known intents (`riskiest_position` | `position_for_user`) — not open-ended query generation.
2. The real answer is computed from `ScoringEngine.tracked_users()` + `current_health_factor()` — actual engine state, not anything the model asserts.
3. A second plain-text call narrates only those real numbers.

This required two small additions to `ScoringEngine`/`PositionLedger` that Phase 2 didn't need: `tracked_users()` (every address with at least one applied event) and a public `current_position()` (Phase 2 only exposed `current_health_factor()`, which now calls `current_position()` internally rather than duplicating the lookup).

## Exit condition: verified against the real API, not mocks

`monitor/tests/test_ai_integration.py`, run with `pytest -m integration` (excluded from the default suite, matching Graph Trail's exact pattern — `pyproject.toml`'s `addopts` keeps `pytest` alone free of API cost):

- `test_recommend_action_picks_a_real_precomputed_option` — confirms the returned amount is always exactly one of the two precomputed values, never something else.
- Three distinct scenarios for `explain_transition`, as the plan specifically asked for:
  - **Price crash** — a `RiskTransition` constructed directly (no live price-feed event exists yet in the pipeline — see `docs/phase2_findings.md` Finding 1 — so this scenario is deliberately fed as a fact rather than produced by `process_event`).
  - **New large borrow** — a real `BORROW` event through the actual `ScoringEngine`.
  - **Partial repayment** — a real `REPAY` event through the actual `ScoringEngine`.
- `test_answer_position_query_identifies_the_riskier_of_two_tracked_users` — two real tracked positions (one DANGER, one SAFE), asked "which is riskiest," and the real Claude response correctly names the risky user's address.

All 5 passed against the live API in this session (`pytest -v -m integration` → `5 passed in 8.74s`).

## A real finding from non-deterministic runs: the model needs to be told which direction is "risky"

On one run, `test_answer_position_query_identifies_the_riskier_of_two_tracked_users` failed — not because the pipeline was broken, but because Claude **correctly declined to guess**: given two raw health-factor numbers and no stated convention, it said it lacked "sufficient data... need information about what health factor thresholds constitute risk levels" rather than assume lower-is-riskier. That's good caution, not a bug in the model — the actual bug was an under-specified prompt on our side, silently relying on the model happening to infer a convention it wasn't told.

Fixed by adding the domain fact explicitly to `_ANSWER_SYSTEM_PROMPT`: "A LOWER health factor means a RISKIER position (a value below 1.0 is eligible for liquidation)." Re-ran the previously-flaky test 3 additional times after the fix to confirm it wasn't luck — all passed. Lesson: any fact a domain expert would consider obvious still needs to be stated explicitly in the prompt; the model won't reliably infer a convention just because it's standard in the field.
