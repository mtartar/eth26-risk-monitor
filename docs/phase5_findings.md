# Phase 5 findings — observability & hardening

## Scope reductions, stated upfront

The original plan called for Redis/Postgres, OpenTelemetry tracing, ECS/Kubernetes deployment docs, and a fallback from a dead Substreams stream to `graph-lending-mcp`/Token API polling. None of those are built. Each is a deliberate, documented reduction given this project's "keep it simple, docker compose" mandate for this phase — not a missed requirement:

- **Position state stays in-memory** (Phase 2's `PositionLedger`) — no Redis/Postgres. Real gap for genuine multi-process production use; fine at this event volume and for a single-process demo.
- **No OpenTelemetry.** Full distributed tracing needs a collector and an exporter backend — real infrastructure this phase's scope doesn't justify. Structured JSON logging (`monitor/observability/logging_config.py`) is the substitute: one parseable JSON object per log line, to stdout, which is what a container already expects.
- **No ECS/Kubernetes docs.** Docker Compose is the only deployment story here, and it's real and tested (see below) — a heavier path can be documented later if this ever needs to run somewhere Compose doesn't fit.
- **The fallback is retry-with-backoff, not a second data source.** The original plan's fallback target (`graph-lending-mcp`/Token API) was never built (Phase 1 finding). What's real instead: `monitor/ingestion/resilient_runner.py`'s `run_with_retry()` — a Substreams connection error is logged and retried with exponential backoff rather than crashing the process, resuming from the last persisted cursor (Phase 1's guarantee). Chaos-tested in `test_resilient_runner.py` with a sink that fails N times then recovers, and one that never recovers (confirms it still raises loudly rather than retrying forever in silence).

## Cost tracking uses real token counts, with a dated, sourced rate for the dollar conversion

`monitor/observability/cost_tracker.py` records `usage.input_tokens`/`usage.output_tokens` straight from each real Anthropic response — not estimated. The USD conversion uses Claude Haiku 4.5's $1/$5 per-million-token rate, cross-checked across several independent pricing-tracker sites in September 2026 — labeled as an estimate since pricing can change, not asserted as authoritative. GRT query fees and cloud compute cost are genuinely $0, not omitted: nothing in this project talks to a live paid Substreams endpoint or runs on paid cloud infrastructure.

## The full stack was actually stood up and verified, not just written

```bash
docker compose up -d --build
```

(Note: this environment's `docker compose` build needed `DOCKER_BUILDKIT=0` — the `docker-buildx` plugin wasn't wired up for this user. `docker compose build` alone may work fine elsewhere.)

Verified for real against the running containers:
- `curl http://localhost:8098/metrics` — real Prometheus exposition format, including custom metrics (`monitor_events_processed_total`, `monitor_risk_transitions_total`, `monitor_alerts_sent_total`, `monitor_llm_call_duration_seconds`, `monitor_sink_retries_total`) with real values from the demo pipeline run.
- Prometheus target `risk-monitor` → `"health": "up"`.
- Grafana's Prometheus datasource and the "Risk Monitor" dashboard (5 panels: events by kind, risk transitions, alerts sent, sink retries, LLM call duration) are auto-provisioned — confirmed on a **clean rebuild** (`docker compose down -v && up -d --build`), not just the first run. An earlier version pinned the dashboard's datasource UID to one Grafana happened to generate, which would have broken on a fresh volume; fixed by pinning an explicit, stable `uid: prometheus` in the datasource provisioning file instead.
- Every panel's PromQL query confirmed against Prometheus's own query API to return real, correct values (e.g. `monitor_events_processed_total` → 3 series matching the demo's Supply/Borrow/Borrow/Repay sequence).

Ports (chosen to avoid several unrelated services already running on this shared machine on 8000/9090/3030): app `8098`, Prometheus `9099`, Grafana `3033` (`admin`/`admin`).

## Exit condition

**A Grafana dashboard showing live pipeline health**: done, provisioned and verified above. **A documented, tested recovery procedure for both a sink crash and a Substreams stream outage**: `run_with_retry()` + `test_resilient_runner.py` cover the "connection raises mid-stream" case with real, passing tests; a full live-outage drill against a real Substreams endpoint isn't possible without `SUBSTREAMS_API_TOKEN` (same gap as Phase 1).
