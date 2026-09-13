# Risk Monitor (working name — see naming options in `poc-thegraph/03_names_and_architecture.md`)

A real-time risk-monitoring agent for DeFi lending positions, built on The Graph's Substreams and standardized-schema products.

> **New to DeFi lending, The Graph, or this codebase's Python patterns?** Read **[docs/glossary.md](docs/glossary.md)** first — it explains health factor/liquidation/collateral, Substreams vs. Subgraphs vs. MCP, and why the code is structured around a `Protocol` + registry, all in plain English with a worked numeric example. Nothing below assumes you already know these terms.

## Full design context

- `poc-thegraph/01_context_and_mechanism.md` — the problem and theory (health factor, event-driven monitoring, reorgs)
- `poc-thegraph/02_implementation_thegraph.md` — The Graph's tech landscape and where this builder's skills fit
- `poc-thegraph/03_names_and_architecture.md` — naming, ETHOnline 2026 track-fit strategy, production architecture
- `poc-thegraph/04_implementation_plan.md` — the phased build plan this repo follows

## Status: Phase 0 (scoping) complete

No live data yet — this phase established the **generic protocol/chain interface** and confirmed the concrete Aave v3/Ethereum details against real documentation (not assumptions). See [docs/data_flow_sketch.md](docs/data_flow_sketch.md) for the full writeup, citations, and what's still unverified going into Phase 1.

## Design: generic by construction

`monitor/protocols/models.py` defines the entire protocol-agnostic interface — `ProtocolConfig`, `PositionState`, `RiskModel` — with zero Aave-specific logic. `monitor/protocols/aave_v3_ethereum.py` is the first concrete implementation. `monitor/protocols/registry.py` is the seam: adding a second protocol or chain means one new module plus two registry entries, not touching anything that already works.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Development

```bash
pip install -r requirements-dev.txt
ruff check . --fix && ruff format .
ty check .
```

## AI assistance

Scaffolding and iteration on this repo were assisted by Claude Code. Architecture decisions, source verification, and what's marked "TBD" vs. confirmed were driven and checked by me.
