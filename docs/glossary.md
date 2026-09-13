# Glossary — for newcomers to DeFi and The Graph

*Read this before `03_names_and_architecture.md` or the code if any of these terms are new to you. Everything here is explained in plain English first, with the precise technical detail after.*

---

## The DeFi lending concepts

### Collateral, debt, and why this project exists

DeFi ("Decentralized Finance") lending protocols — Aave, Compound, Morpho — let you borrow crypto without a bank. To borrow $100, you must first lock up *more* than $100 worth of a different asset as **collateral** (e.g. lock up $150 of ETH to borrow $100 of USDC). There's no credit check and no legal recourse if you don't repay — the protocol's only protection is requiring you to always hold more collateral value than debt value.

### Liquidation

Crypto prices move fast. If your collateral's price drops enough, its value can fall too close to your debt's value. When that happens, the protocol doesn't wait — it **liquidates** you: it automatically sells your collateral (usually at a discount, to reward whoever triggers the liquidation) to repay your debt. This can happen within minutes, often with a real financial penalty on top of losing your position.

### Health factor

The number every lending protocol computes to answer "how close to liquidation is this position?":

```
health_factor = (collateral value × liquidation threshold) / debt value
```

- **Liquidation threshold** is a safety margin set by the protocol per asset (e.g. 80%) — only 80% of your collateral's value "counts" toward safety, as a buffer.
- **Health factor > 1** → safe. **Health factor ≤ 1** → eligible for liquidation.

**Worked example:** you've deposited $10,000 of ETH as collateral (liquidation threshold 80%) and borrowed $4,000 of USDC.
```
health_factor = (10,000 × 0.80) / 4,000 = 2.0   →  safe, well above 1
```
If ETH's price then drops so your collateral is worth only $5,000:
```
health_factor = (5,000 × 0.80) / 4,000 = 1.0   →  now exactly at the liquidation line
```
This is the exact formula implemented in `monitor/protocols/aave_v3_ethereum.py`'s `AaveV3RiskModel`, and the exact scenario the four test cases in `test_aave_v3_risk_model.py` walk through numerically.

### Why "real-time" matters here

Most people check a lending dashboard once a day. A health factor can cross 1.0 in minutes during a sharp price move. **Polling** (checking every N seconds) always has a lag equal to the polling interval; **event-driven** monitoring reacts the instant a relevant event happens on-chain. This project is event-driven — see "Substreams" below for how that's technically possible.

### Reorgs (reorganizations)

A blockchain occasionally revises its most recent history — a few recently-produced blocks get replaced by a different set. This is normal, expected behavior, not an error. It means an event this system just processed might need to be **retracted** (undone). Any real-time system built on live chain data has to handle this correctly, or it risks scoring a position based on data that later turned out to be wrong. See `PositionState`/`RiskModel` in the code — the scoring engine (Phase 2, not built yet) is designed around apply/undo deltas specifically because of this.

---

## The Graph's ecosystem

The Graph is a set of tools for getting data off a blockchain and into a queryable form. This project uses two of them together:

### Substreams

A way to **stream** blockchain events in real time (and process historical ones in parallel, at high speed) using modules written in Rust, compiled to WebAssembly. Think of it as "subscribe to a live feed of everything that happens to this smart contract," with built-in handling for the reorg problem above (it tells you explicitly when to undo something). This project consumes an **existing, published** Substreams package for Aave rather than writing one from scratch — see `substreams.dev`.

### Subgraphs

The more traditional Graph Protocol tool: you define a schema, and a **Subgraph** indexes historical + current contract data into a GraphQL API you can query (`{ borrows(first: 10) { amount, user } }`-style queries). Unlike Substreams, this is normally **pull-based** (you ask, you get an answer) rather than a live push feed — fine for "what happened," less ideal for "tell me the instant something happens."

### Messari standardized schema

Different lending protocols structure their data completely differently by default — Aave's subgraph and Compound's subgraph don't share field names or shapes, even though both are "a lending protocol." Messari (with The Graph's backing) publishes a **standardized schema** — a shared set of entity names and fields — that many protocols' subgraphs now implement. The payoff: **one query pattern works across dozens of different lending protocols**, instead of writing custom queries for each one.

### MCP (Model Context Protocol) / `graph-lending-mcp`

MCP is a protocol that lets an AI assistant call external tools/data sources directly. `graph-lending-mcp` is an existing open-source MCP server that uses the Messari standardized schema to let an AI (or a script) ask one question — "compare USDC borrow rates across all protocols" — and get an answer assembled from **40+ different lending protocols' subgraphs at once**. This project reuses it for cross-protocol context rather than reimplementing that fan-out logic.

---

## Python patterns used in this codebase (for newer Python developers)

### Pydantic `BaseModel`

A class that validates its own fields automatically. `PositionState(total_collateral_usd="not a number")` would raise an error immediately, rather than silently propagating a bad value deep into the scoring logic. Every data shape in this project (`ProtocolConfig`, `PositionState`, `SubstreamsSource`) is a Pydantic model for exactly this reason.

### `typing.Protocol`

`RiskModel` in `models.py` isn't a base class you inherit from — it's a **structural interface**: any class with a matching `compute_health_factor` method automatically satisfies it, with no explicit `class Foo(RiskModel):` declaration needed. This is what lets `AaveV3RiskModel` (and any future `CompoundV2RiskModel`) plug into the same registry without a shared parent class.

### Why a "registry" file

`monitor/protocols/registry.py` is a plain dictionary mapping a string key (`"aave-v3-ethereum"`) to a config and a risk model. This is a common, simple pattern for "pluggable" systems: the rest of the codebase never needs an `if protocol == "aave"` conditional anywhere — it just looks up whatever protocol/chain key it's been asked to handle.

---

## Where to go next

- `README.md` — how to run what's built so far
- `docs/data_flow_sketch.md` — what's confirmed vs. still unverified about Aave v3 specifically
- `../poc-thegraph/03_names_and_architecture.md` — the full production architecture (now with a glossary pointer at the top)
- `../poc-thegraph/04_implementation_plan.md` — the phased build plan this repo follows
