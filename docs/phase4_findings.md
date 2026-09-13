# Phase 4 findings — alerting & dashboard

## The whole pipeline actually runs together for the first time here

`monitor/pipeline.py`'s `Pipeline` class is where Phases 1–3 get wired into one runnable system: ingestion (sink) → scoring (engine) → AI (explanation + recommendation) → alerting (webhook), with the dashboard's WebSocket broadcasting every real transition live. Nothing before Phase 4 had actually run end-to-end as one process.

## Demo mode exists because SUBSTREAMS_API_TOKEN still isn't available

Same gap as Phase 1: no live Substreams connection. `Pipeline._build_client()` falls back to `FakeSubstreamsClient` replaying a small, clearly-synthetic SAFE → WARNING → DANGER → SAFE narrative (`_demo_messages()`) whenever no token is configured — which is the default in this environment. The demo amounts intentionally match the already-hand-verified scenario in `monitor/tests/test_scoring_engine.py` (health factors 1.29 → 0.86 → 5.16), so the demo isn't asserting new arithmetic, just replaying a known-correct one through the real pipeline plumbing.

## A real bug found by running the demo pipeline twice in a row

The first version of `Pipeline` reused `settings.cursor_db_path` (the same SQLite file real ingestion would use) for demo mode too. Demo mode's cursor strings (`"demo-cursor-1"` etc.) aren't real chain state, but `CursorStore` doesn't know that — so a second demo run resumed from the persisted `"demo-cursor-4"` (the end of the finite sequence) and silently produced zero events. Fixed by giving demo mode an ephemeral `:memory:` cursor store instead, so every demo run replays from the start. Found via the integration test in `test_pipeline_integration.py`, which failed with `0 == 3` alerts on a second run before the fix.

## The alerter is real, delivery is not independently verified

`WebhookAlerter` posts Slack's `{"text": ...}` JSON shape, which Discord's webhook endpoint also accepts as a plain message. No real webhook URL was available while building this (same "no credential, so no live verification" pattern as `GrpcSubstreamsClient` in Phase 1) — tested against a mocked HTTP call instead. `NullAlerter` is what actually runs by default (no `ALERT_WEBHOOK_URL` configured), recording every alert it would have sent so tests and the demo can inspect them without a real webhook.

## Exit condition: verified for real, not just written

`test_pipeline_integration.py::test_demo_pipeline_produces_three_real_alerts_end_to_end` runs the actual `Pipeline`, waits (bounded, polling) for the 3 real transitions to flow through the real Anthropic API and into `NullAlerter`, then asserts on the exact alert content and final tracked-position state. Confirmed live in the running Docker container too: `/positions` returns `health_factor: 5.16` (the real final state), and the container logs show 5 real `200 OK` calls to `api.anthropic.com` — 3 explanations + 2 recommendations (only the WARNING/DANGER transitions get a recommendation; the final SAFE one doesn't need one, per `pipeline.py`'s logic).
