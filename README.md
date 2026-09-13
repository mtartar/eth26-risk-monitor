# Risk Monitor (working name — see naming options in `poc-thegraph/03_names_and_architecture.md`)

A real-time risk-monitoring agent for DeFi lending positions, built on The Graph's Substreams and standardized-schema products.

> **New to DeFi lending, The Graph, or this codebase's Python patterns?** Read **[docs/glossary.md](docs/glossary.md)** first — it explains health factor/liquidation/collateral, Substreams vs. Subgraphs vs. MCP, and why the code is structured around a `Protocol` + registry, all in plain English with a worked numeric example. Nothing below assumes you already know these terms.

## Full design context

- `poc-thegraph/01_context_and_mechanism.md` — the problem and theory (health factor, event-driven monitoring, reorgs)
- `poc-thegraph/02_implementation_thegraph.md` — The Graph's tech landscape and where this builder's skills fit
- `poc-thegraph/03_names_and_architecture.md` — naming, ETHOnline 2026 track-fit strategy, production architecture
- `poc-thegraph/04_implementation_plan.md` — the phased build plan this repo follows

## Status: Phase 1 (data foundation) complete

Real Substreams event data can now flow: `chain (Ethereum) → gRPC → decoder → cursor-persisted sink → event bus`, resumable after a crash with no gap and no duplicate (that's Phase 1's actual exit condition, and it's tested — `monitor/tests/test_sink_resume.py`). One important pivot happened along the way: **Phase 0 targeted Aave v3, but no verified v3 Substreams package exists** — the real, working pipeline targets **Aave v2** instead. See [docs/phase1_findings.md](docs/phase1_findings.md) for the full story, including what's real/tested vs. what's written-to-spec-but-not-live-verified (short version: everything except the actual network call to a live Substreams endpoint, since no `SUBSTREAMS_API_TOKEN` was available while building this).

## Design: generic by construction

`monitor/protocols/models.py` defines the entire protocol-agnostic interface — `ProtocolConfig`, `PositionState`, `RiskModel`, `NormalizedEvent`, `EventDecoder` — with zero Aave-specific logic. `monitor/protocols/aave_v2_ethereum.py` is the first real, working implementation (`aave_v3_ethereum.py` is a documented stub — see status above). `monitor/protocols/registry.py` is the seam: adding a second protocol or chain means one new module plus two registry entries, not touching anything that already works.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

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
