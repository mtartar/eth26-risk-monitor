"""Aave v3 on Ethereum mainnet — the first concrete ProtocolConfig + RiskModel.

What's confirmed against real sources (see docs/data_flow_sketch.md for the
full writeup and citations):
- Event names (Supply, Borrow, Withdraw, Repay, LiquidationCall) and the
  health-factor formula, against aave.com/docs/aave-v3.
- The Aave v3 Pool contract address, against Etherscan.
- That a Substreams "Lending" dataset covering Aave v2/v3 exists on
  substreams.dev.

What's NOT yet verified (marked "TBD" below) — do this in Phase 1, not by
guessing a plausible-looking value now:
- The exact published package/version/module name to consume from the
  Lending dataset.
- The exact topic0 hashes for each event. A wrong hash here would silently
  match nothing rather than error, which is worse than an honest TBD.
"""

from monitor.protocols.models import EventKind, PositionState, ProtocolConfig, SubstreamsSource

AAVE_V3_ETHEREUM = ProtocolConfig(
    protocol="aave-v3",
    chain="ethereum",
    substreams=SubstreamsSource(
        package="lending",
        version="TBD",  # confirm exact published version on substreams.dev in Phase 1
        endpoint="https://substreams.dev/datasets/lending",
        module="TBD",  # confirm exact output module name in Phase 1
        event_topics={
            EventKind.SUPPLY: "TBD",
            EventKind.WITHDRAW: "TBD",
            EventKind.BORROW: "TBD",
            EventKind.REPAY: "TBD",
            EventKind.LIQUIDATION: "TBD",  # Aave's LiquidationCall event
        },
    ),
    contract_addresses={
        # Aave v3 Pool, Ethereum mainnet — verified via Etherscan.
        "pool": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    },
    notes=(
        "The Substreams 'Lending' dataset's own registry description says it "
        "already surfaces on-chain USD valuations via oracle lookups, so a "
        "separate Chainlink price-feed module may not be needed — confirm "
        "this by inspecting real output before building one in Phase 1."
    ),
)


class AaveV3RiskModel:
    """Aave v3's health factor: (collateral * liquidationThreshold) / debt.

    Confirmed against Aave v3 docs' getUserAccountData() description
    (aave.com/docs/aave-v3/smart-contracts/pool): totalCollateralBase,
    totalDebtBase, and currentLiquidationThreshold combine exactly this way.
    """

    def compute_health_factor(self, position: PositionState) -> float:
        """Return infinity for a debt-free position rather than dividing by zero."""
        if position.total_debt_usd == 0:
            return float("inf")
        weighted_collateral = position.total_collateral_usd * position.liquidation_threshold
        return weighted_collateral / position.total_debt_usd
