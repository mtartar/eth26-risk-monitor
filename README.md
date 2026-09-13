# Risk Monitor (working name — see naming options in `poc-thegraph/03_names_and_architecture.md`)

A real-time risk-monitoring agent for DeFi lending positions, built on The Graph's Substreams and standardized-schema products.

> **New to DeFi lending, The Graph, or this codebase's Python patterns?** Read **[docs/glossary.md](docs/glossary.md)** first — it explains health factor/liquidation/collateral, Substreams vs. Subgraphs vs. MCP, and why the code is structured around a `Protocol` + registry, all in plain English with a worked numeric example. Nothing below assumes you already know these terms.

## Full design context

- `poc-thegraph/01_context_and_mechanism.md` — the problem and theory (health factor, event-driven monitoring, reorgs)
- `poc-thegraph/02_implementation_thegraph.md` — The Graph's tech landscape and where this builder's skills fit
- `poc-thegraph/03_names_and_architecture.md` — naming, ETHOnline 2026 track-fit strategy, production architecture
- `poc-thegraph/04_implementation_plan.md` — the phased build plan this repo follows

## Status: Phase 3 (AI reasoning layer) complete

Phase 1 built real event ingestion (`chain → gRPC → decoder → cursor-persisted sink → event bus`), resumable after a crash with no gap and no duplicate. Phase 2 turned those events into a live health factor per user (`monitor/scoring/`), reorg-safe and alert-fatigue-safe, validated against two real historical Aave v2 liquidations. Phase 3 adds the AI layer (`monitor/ai/`): a corrective-action recommendation (real math computed first — Claude can only choose *which* precomputed option, not invent a number), plain-English explanations of *why* risk changed, and a natural-language query interface over live tracked positions. All three are verified against the real Anthropic API, not just mocks — `pytest -m integration` → 5 passed, covering the plan's required 3 distinct scenarios (price crash, new large borrow, partial repayment). See [docs/phase3_findings.md](docs/phase3_findings.md).

Two pivots from earlier phases carry forward: **Phase 0 targeted Aave v3, but no verified v3 Substreams package exists** — the real, working pipeline targets **Aave v2** instead ([docs/phase1_findings.md](docs/phase1_findings.md)); and raw Aave events carry no USD price, resolved by recognizing health factor is a ratio invariant to a consistently-applied price unit ([docs/phase2_findings.md](docs/phase2_findings.md)).

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
