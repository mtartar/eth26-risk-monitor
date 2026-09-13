# Risk Monitor (working name — see naming options in `poc-thegraph/03_names_and_architecture.md`)

A real-time risk-monitoring agent for DeFi lending positions, built on The Graph's Substreams and standardized-schema products.

> **New to DeFi lending, The Graph, or this codebase's Python patterns?** Read **[docs/glossary.md](docs/glossary.md)** first — it explains health factor/liquidation/collateral, Substreams vs. Subgraphs vs. MCP, and why the code is structured around a `Protocol` + registry, all in plain English with a worked numeric example. Nothing below assumes you already know these terms.

## Full design context

- `poc-thegraph/01_context_and_mechanism.md` — the problem and theory (health factor, event-driven monitoring, reorgs)
- `poc-thegraph/02_implementation_thegraph.md` — The Graph's tech landscape and where this builder's skills fit
- `poc-thegraph/03_names_and_architecture.md` — naming, ETHOnline 2026 track-fit strategy, production architecture
- `poc-thegraph/04_implementation_plan.md` — the phased build plan this repo follows

## Status: Phase 5 (observability & hardening) complete — the whole system runs together

Phases 1–3 built ingestion, scoring, and an AI reasoning layer. **Phase 4** (`monitor/pipeline.py`) wires them into one running system for the first time — ingestion → scoring → AI → webhook alerting — with a live dashboard (`monitor/dashboard/`, WebSocket push + REST + NL query box). **Phase 5** adds Prometheus metrics, structured JSON logging, real-token-based LLM cost tracking, and retry-with-backoff resilience around ingestion, all wrapped in a Docker Compose stack (app + Prometheus + Grafana) that was actually built, run, and verified in this environment — not just written. See [docs/phase4_findings.md](docs/phase4_findings.md) and [docs/phase5_findings.md](docs/phase5_findings.md) for the full story, including a real bug (demo mode's cursor colliding with production's) caught by running the demo pipeline twice in a row, and the deliberate scope cuts (no Redis/Postgres, no OpenTelemetry, no ECS/K8s docs) made for this phase's "keep it simple" mandate.

No `SUBSTREAMS_API_TOKEN` is available in this environment, so the running system operates in **demo mode**: a small, clearly-synthetic SAFE → WARNING → DANGER → SAFE event sequence (reusing Phase 2's hand-verified numbers) flows through the real pipeline, producing real Anthropic API calls, real Prometheus metrics, and real dashboard updates — everything is real except the chain data itself, which is honestly labeled as synthetic throughout.

Earlier pivots carry forward: **Phase 0 targeted Aave v3, but no verified v3 Substreams package exists** — the real, working pipeline targets **Aave v2** instead ([docs/phase1_findings.md](docs/phase1_findings.md)); raw Aave events carry no USD price, resolved by recognizing health factor is a ratio invariant to a consistently-applied price unit ([docs/phase2_findings.md](docs/phase2_findings.md)).

## Running the full stack

```bash
docker compose up -d --build
```

(This environment needed `DOCKER_BUILDKIT=0 docker compose up -d --build` — the `docker-buildx` plugin wasn't wired up for this user; try without it first.)

- Dashboard: **http://localhost:8098**
- Prometheus: **http://localhost:9099**
- Grafana: **http://localhost:3033** (`admin` / `admin`) — the "Risk Monitor" dashboard and Prometheus datasource are auto-provisioned, no manual setup needed
- `docker compose down` to stop everything

Ports were chosen to avoid several unrelated services already running on this shared machine on 8000/9090/3030.

## Design: generic by construction

`monitor/protocols/models.py` defines the entire protocol-agnostic interface — `ProtocolConfig`, `PositionState`, `RiskModel`, `NormalizedEvent`, `EventDecoder` — with zero Aave-specific logic. `monitor/protocols/aave_v2_ethereum.py` is the first real, working implementation (`aave_v3_ethereum.py` is a documented stub — see status above). `monitor/protocols/registry.py` is the seam: adding a second protocol or chain means one new module plus two registry entries, not touching anything that already works. `monitor/scoring/` extends the same discipline: `PriceOracle` and the reserve-config lookup are the two pluggable seams a new protocol's pricing/thresholds would need, without touching the ledger or hysteresis logic.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

`ANTHROPIC_API_KEY` for the AI layer (`monitor/ai/`) is reused from `eth26-graph-trail/.env` automatically if that sibling repo is checked out — see `monitor/config.py`. To run the AI layer's real integration tests: `pytest -m integration` (excluded from the default `pytest` run since it costs real API credit).

To run against a real, live Substreams stream (optional — everything above works and is tested without this): copy `.env.example` to `.env`, get a token per [docs/phase1_findings.md](docs/phase1_findings.md), and follow the manual smoke test there.

## Regenerating the protobuf/gRPC stubs

Only needed if you change a `.proto` file in `protos/`:

```bash
pip install -r requirements-dev.txt  # includes grpcio-tools
bash scripts/generate_protos.sh
```

## Development

```bash
pip install -r requirements-dev.txt
ruff check . --fix && ruff format .
ty check .
```

## AI assistance

Scaffolding and iteration on this repo were assisted by Claude Code. Architecture decisions, source verification, and what's marked "TBD" vs. confirmed were driven and checked by me.
