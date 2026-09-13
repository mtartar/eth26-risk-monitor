"""Real Aave v2 Ethereum reserve metadata — decimals and liquidation threshold.

Every value below was fetched live via eth_call to the real
AaveProtocolDataProvider contract (0x057835Ad21a177dbdd3090bB1CAE03EAcF78Fc6d,
verified via Etherscan), calling getReserveConfigurationData(asset) — not
looked up in documentation or guessed. See docs/phase2_findings.md for the
exact call and raw results. USDT's liquidation_threshold is genuinely 0: Aave
v2 does not allow USDT to be used as collateral, only borrowed.
"""

from pydantic import BaseModel


class ReserveConfig(BaseModel):
    """Static, per-reserve facts needed to turn a raw token amount into a health-factor input."""

    address: str
    symbol: str
    decimals: int
    liquidation_threshold: float  # fraction, e.g. 0.86 = 86%; 0.0 means "not usable as collateral"


RESERVES: dict[str, ReserveConfig] = {
    cfg.address.lower(): cfg
    for cfg in [
        ReserveConfig(
            address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            symbol="WETH",
            decimals=18,
            liquidation_threshold=0.86,
        ),
        ReserveConfig(
            address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            symbol="USDC",
            decimals=6,
            liquidation_threshold=0.875,
        ),
        ReserveConfig(
            address="0xdac17f958d2ee523a2206206994597c13d831ec7",
            symbol="USDT",
            decimals=6,
            liquidation_threshold=0.0,
        ),
        ReserveConfig(
            address="0x6B175474E89094C44Da98b954EedeAC495271d0F",
            symbol="DAI",
            decimals=18,
            liquidation_threshold=0.77,
        ),
    ]
}


def get_reserve_config(address: str) -> ReserveConfig:
    """Look up a reserve's config by contract address (case-insensitive)."""
    config = RESERVES.get(address.lower())
    if config is None:
        raise KeyError(f"No reserve config for '{address}'. Known: {sorted(RESERVES)}")
    return config
