# Phase 2 findings — scoring engine

*What was built, what's real vs. illustrative, and two real infrastructure/architecture findings discovered along the way.*

## Finding 1: raw Aave v2 events carry no USD value — and that's fine

`Deposit`/`Borrow`/`Repay`/`Withdraw` events (see `protos/contract/v1/contract.proto`, extracted in Phase 1) carry only raw token amounts, never a USD value. Worse, Aave v2's own on-chain oracle is **ETH-denominated**, not USD (`getUserAccountData` returns `totalCollateralETH`/`totalDebtETH` — v3 later moved to a USD-based "base currency"). Neither Phase 1 nor Phase 2 built a real price-feed integration (that's Substreams oracle-event data or a separate Chainlink price-feed module — still open).

This turns out not to block Phase 2's math: **health factor is a ratio**, `(collateral × threshold) / debt`, and that ratio is invariant to which consistent price unit you use for both sides — ETH, USD, or anything else — as long as it's the *same* unit for every reserve involved. `price_oracle.py`'s `PriceOracle` Protocol formalizes this: it returns "a price," not specifically a USD price, and `total_collateral_usd`/`total_debt_usd` field names elsewhere in the codebase should be read as "in whatever one consistent unit the oracle returns," not literally USD. `StaticPriceOracle` is the test/dev implementation; a real feed is still a gap, tracked explicitly rather than silently assumed away.

## Finding 2: real reserve config, fetched live, not guessed

`monitor/scoring/reserve_config.py`'s decimals and `liquidation_threshold` values are not from documentation — they're the actual return values of `eth_call`-ing the real Aave v2 `AaveProtocolDataProvider` contract (`0x057835Ad21a177dbdd3090bB1CAE03EAcF78Fc6d`, verified via Etherscan) with `getReserveConfigurationData(address)` (selector `0x3e150141`, computed via real Keccak-256, not copied from a guess):

| Reserve | decimals | liquidation_threshold |
|---|---|---|
| WETH | 18 | 0.86 |
| USDC | 6 | 0.875 |
| USDT | 6 | **0.0** — not usable as collateral on Aave v2 |
| DAI | 18 | 0.77 |

USDT's `0.0` is real, not a bug: Aave v2 genuinely doesn't allow USDT as collateral, only as a borrowable asset — which is exactly its role in the first real liquidation fixture below.

This also resolves a simplification Phase 0/1 explicitly flagged as deferred (`docs/data_flow_sketch.md`): `PositionLedger.position_state()` now computes a real **collateral-value-weighted average** liquidation threshold across a user's actual reserves, not a single borrowed number.

## Finding 3: the free public RPC's "archive" cutoff is inconsistent, not a fixed window

Reproducing a full historical liquidation trajectory (every Deposit/Borrow leading up to it) requires archive-node access. Probing `ethereum.publicnode.com` (the same endpoint used throughout this project) found its free tier **does not have one fixed non-archive window** — a `eth_getLogs` query 5,000 blocks behind head failed with an archive-access error, while an 8,000-block query immediately after succeeded. This strongly suggests the "public" endpoint load-balances across multiple backend nodes with different archive capabilities, making deep historical queries unreliable regardless of how the block range is chosen.

**Decision:** rather than keep fighting a moving target, or fabricate a plausible-looking trajectory, the real historical liquidation tests below use **real end-states with clearly-labeled illustrative build-ups** — see Finding 4.

## Finding 4: two real historical liquidations, honestly reproduced

Found via `eth_getLogs` against the real Aave v2 `LendingPool` (`0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9`), filtered on the real `LiquidationCall` topic (computed via Keccak-256, cross-checked against an independently-sourced value):

1. **Block 25965977**, tx `0x0b14f71c...80d7a` — user `0xe8b49d06...b120497`, 68.527758 USDC collateral seized, 65.58018 USDT debt covered.
2. **Block 25963793**, tx `0x0ffba0fd...9f81f` — user `0x1c295f97...6c837db3`, 1.063572672952549697 WETH collateral seized, 1.012926355192904474 WETH debt covered (same-asset liquidation — a real, valid Aave v2 configuration).

Both were deliberately chosen so **no price assumption affects the result**: fixture 1 uses two dollar-pegged stablecoins (price ≈ 1.0 both sides); fixture 2 uses the same asset as both collateral and debt, so price cancels out of the ratio entirely regardless of its value (see Finding 1).

`monitor/tests/test_real_historical_liquidations.py` builds each position with an **illustrative synthetic build-up** (a Supply then a Borrow, clearly commented as such) that lands exactly on these real final amounts, then:
- confirms `current_health_factor()` is already below 1.0 *before* the liquidation event is applied — using the real fetched `liquidation_threshold`, this independently confirms these real liquidations were mathematically justified;
- applies the real `LiquidationCall` event itself and confirms both balances fully unwind to zero (health factor → infinity).

This is real end-to-end validation of the scoring math against genuine on-chain outcomes — just not a claim of full archive-reconstructed trajectories, which Finding 3 made unreliable to pursue further.

## Design notes

- **Reorg handling is undo-then-replay**, not incremental subtraction: `PositionLedger.undo(block)` drops every applied event after `block` and recomputes balances from the retained log on the next query. At this event volume, replay-from-log is simple, obviously correct, and avoids an entire class of "did I reverse that delta exactly right" bugs.
- **Hysteresis doesn't reset on undo.** `HysteresisTracker` keeps reporting based on its last-known level even after a reorg reverts the ledger — this is correct, not a gap: the next real event recomputes from the now-corrected ledger, and if that differs from what was last reported, hysteresis reports the correction as a genuine transition. Tested explicitly in `test_scoring_engine.py`.
- **A newly-tracked position that's already risky reports a transition immediately**, compared against an implicit SAFE baseline — deliberately not suppressed as "no prior state to compare against," since that's exactly the case worth surfacing first.
- **`ScoringEngine.process_event`/`process_undo` are pure** (no I/O); `run()` is a thin async wrapper reading the event bus, per the plan's own instruction to build health-factor computation "as a pure function first." `run()` isn't independently unit-tested since it's a two-line dispatch over the already-tested pure methods.
