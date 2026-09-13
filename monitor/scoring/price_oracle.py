"""Turns a reserve address into a price, in one consistent unit across all reserves.

Aave v2's own oracle is ETH-denominated, not USD (v3 moved to a USD "base
currency"). This doesn't actually matter for the health-factor *ratio*
computed downstream: (collateral * threshold) / debt is invariant to which
consistent unit prices are expressed in, as long as every reserve uses the
same one. So "usd" in field names elsewhere in this codebase really means
"whatever one consistent unit this PriceOracle returns" — no real price feed
integration exists yet (see docs/phase2_findings.md): that's Substreams
oracle-event data or a Chainlink price-feed module, neither built in Phase 2.
"""

from typing import Protocol


class PriceOracle(Protocol):
    """Returns a reserve's price in some consistent unit; only the ratio matters downstream."""

    def get_price(self, reserve_address: str) -> float:
        """Return the price of one whole token of this reserve."""
        ...


class StaticPriceOracle:
    """Fixed prices for tests and local dev — NOT a real price feed.

    Stablecoins default to 1.0 (accurate enough for their peg). Non-pegged
    assets need an explicit price passed in; there's no sensible universal
    default for those.
    """

    def __init__(self, prices: dict[str, float]):
        """Store a lowercased address -> price map."""
        self._prices = {addr.lower(): price for addr, price in prices.items()}

    def get_price(self, reserve_address: str) -> float:
        """Return the configured price, raising if this reserve has none set."""
        price = self._prices.get(reserve_address.lower())
        if price is None:
            raise KeyError(f"No static price configured for '{reserve_address}'")
        return price
