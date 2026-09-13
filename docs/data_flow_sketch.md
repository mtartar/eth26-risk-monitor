# Phase 0 data-flow sketch — Aave v3 on Ethereum

*Exit-condition deliverable for Phase 0 (see `04_implementation_plan.md` in `poc-thegraph/`): a written data-flow sketch reviewed against real Aave v3 documentation, not assumptions. Everything below is either confirmed against a cited source or explicitly marked as an open question for Phase 1 — nothing here is guessed.*

## Inputs

**Events** (confirmed against Aave v3 documentation and the Substreams "Lending" dataset registry, which explicitly states it covers "AAVE V2/V3 and Compound V2 ... supply, borrow, repay, and liquidation events" — [substreams.dev/datasets/lending](https://substreams.dev/datasets/lending)):

| Event | Meaning | Confirmed? |
|---|---|---|
| `Supply` | User deposits collateral | ✅ named in Aave v3 docs |
| `Withdraw` | User removes collateral | ✅ named in Aave v3 docs |
| `Borrow` | User takes on debt | ✅ named in Aave v3 docs |
| `Repay` | User pays down debt | ✅ named in Aave v3 docs |
| `LiquidationCall` | A liquidator closes an unhealthy position | ✅ named in Aave v3 docs; also has a dedicated Substreams package, `aave-liquidation-bot-eth` |
| `ReserveDataUpdated` | Per-asset rate/index update | ✅ named in Aave v3 docs |

**Open question for Phase 1**: whether oracle price updates arrive as their own event or are only reflected indirectly through `ReserveDataUpdated`/USD-valuation fields the Lending dataset already computes. The dataset's own description says it surfaces "on-chain USD valuations via oracle lookups" — if that's accurate, a separate Chainlink price-feed Substreams module (originally assumed necessary in `03_names_and_architecture.md`) may not be needed at all. **Confirm this by inspecting real Substreams output before building anything extra.**

**Per-user aggregate state** (confirmed against Aave v3's `getUserAccountData()` view function, documented at [aave.com/docs/aave-v3/smart-contracts/pool](https://aave.com/docs/aave-v3/smart-contracts/pool)):
- `totalCollateralBase`, `totalDebtBase`, `availableBorrowsBase`, `currentLiquidationThreshold`, `ltv`, `healthFactor` — Aave computes and exposes health factor itself, which is also our own independent cross-check target once real data flows (Phase 1/2).

**Per-asset reserve config** (confirmed against `getReserveConfigurationData()`, same doc):
- `decimals`, `ltv`, `liquidationThreshold`, `liquidationBonus`, `reserveFactor`, plus collateral/borrow/active/frozen flags.

**Contract address** (confirmed via Etherscan, not assumed): Aave v3 Pool on Ethereum mainnet is `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`.

## Scoring

Health factor formula, confirmed against the same `getUserAccountData()` documentation:

```
health_factor = (total_collateral_usd × liquidation_threshold) / total_debt_usd
```

This matches `01_context_and_mechanism.md`'s original theoretical description exactly — Aave's own real formula is the same shape, not an approximation of it. Implemented as `AaveV3RiskModel.compute_health_factor()` in `monitor/protocols/aave_v3_ethereum.py`, tested against 4 cases (healthy, exactly-at-threshold, undercollateralized, debt-free) in `monitor/tests/test_aave_v3_risk_model.py`.

`liquidation_threshold` in Aave is actually a **weighted average across all of a user's supplied collateral assets** (each asset has its own `liquidationThreshold` from its reserve config) — the current `PositionState` model takes this as a single pre-computed field, deferring the per-asset weighting logic to Phase 1/2 once real multi-asset positions are being processed. This is a known simplification, not an oversight.

## Outputs (forward reference — built in later phases, not Phase 0)

- Threshold-crossing alerts (Slack/Discord) — Phase 4
- Live dashboard — Phase 4
- AI-generated explanation + recommendation — Phase 3

## What's genuinely unverified — do not treat these as settled

1. **Exact Substreams package version and output module name** to consume from the Lending dataset. `ProtocolConfig.substreams.version`/`.module` are placeholder `"TBD"` values in `aave_v3_ethereum.py` — filling these with a guessed-but-plausible string would be worse than leaving them explicit placeholders, since a wrong value fails silently (no events matched) rather than erroring.
2. **Exact topic0 event-signature hashes** per event kind — same reasoning. A mistyped hash matches nothing and produces an empty, misleadingly "successful" stream.
3. **How the Lending dataset's oracle/USD-valuation fields are actually shaped** in a real response — needs eyes on real output, not just the registry's prose description.

Phase 1's first task is closing these three gaps with real inspected output, not documentation-reading alone — matching the "get one end-to-end event flowing... before adding scoring" discipline from `02_implementation_thegraph.md`.

## Genericity check

`ProtocolConfig`, `PositionState`, and the `RiskModel` protocol (`monitor/protocols/models.py`) contain zero Aave-specific logic — `aave_v3_ethereum.py` is the only file that knows Aave exists. `monitor/protocols/registry.py` demonstrates the intended extension pattern: a second protocol (e.g. Compound v2 on Ethereum) would be one new module plus two registry entries, with no changes to `models.py`, `registry.py`'s structure, or any already-passing test.
