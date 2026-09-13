"""Per-user, per-reserve raw balance tracking, replay-based for reorg safety.

Reorgs are handled by undo-then-replay rather than incremental subtraction:
at this event volume (single-digit/sec, tiny per-user history), replaying
the retained log from scratch on every undo is simple, obviously correct,
and avoids an entire class of "did I reverse that delta exactly right" bugs
that incremental undo arithmetic invites — a deliberate simplicity choice,
not a missed optimization.
"""

from collections.abc import Callable
from datetime import datetime

from monitor.protocols.models import EventKind, NormalizedEvent, PositionState
from monitor.scoring.price_oracle import PriceOracle
from monitor.scoring.reserve_config import get_reserve_config

# reserve_address (lowercase) -> {"collateral_raw": int, "debt_raw": int}
RawBalances = dict[str, dict[str, int]]


class PositionLedger:
    """Maintains every applied event and derives raw/USD-ish balances from it on demand."""

    def __init__(self) -> None:
        """Start with an empty applied-event log."""
        self._events: list[NormalizedEvent] = []

    def apply(self, event: NormalizedEvent) -> None:
        """Record one more event as applied."""
        self._events.append(event)

    def undo(self, last_valid_block: int) -> None:
        """Drop every applied event strictly after last_valid_block (a reorg occurred)."""
        self._events = [e for e in self._events if e.block_number <= last_valid_block]

    def tracked_users(self) -> set[str]:
        """Return every user address with at least one applied event, lowercased."""
        return {e.user_address.lower() for e in self._events if e.user_address is not None}

    def raw_balances(self, user_address: str) -> RawBalances:
        """Recompute this user's per-reserve raw collateral/debt balances from the full log."""
        balances: RawBalances = {}

        def bucket(reserve_address: str) -> dict[str, int]:
            default = {"collateral_raw": 0, "debt_raw": 0}
            return balances.setdefault(reserve_address.lower(), default)

        for event in self._events:
            if event.user_address is None or event.user_address.lower() != user_address.lower():
                continue
            if event.kind == EventKind.LIQUIDATION:
                self._apply_liquidation(bucket, event)
                continue
            if event.reserve_address is None or event.amount_raw is None:
                continue
            amount = int(event.amount_raw)
            b = bucket(event.reserve_address)
            if event.kind == EventKind.SUPPLY:
                b["collateral_raw"] += amount
            elif event.kind == EventKind.WITHDRAW:
                b["collateral_raw"] -= amount
            elif event.kind == EventKind.BORROW:
                b["debt_raw"] += amount
            elif event.kind == EventKind.REPAY:
                b["debt_raw"] -= amount
        return balances

    def _apply_liquidation(
        self, bucket: Callable[[str], dict[str, int]], event: NormalizedEvent
    ) -> None:
        """A liquidation reduces debt in one reserve, seizes collateral in another (or the same)."""
        if event.reserve_address is not None and event.amount_raw is not None:
            bucket(event.reserve_address)["debt_raw"] -= int(event.amount_raw)
        collateral_asset = event.extra.get("collateral_asset")
        collateral_amount = event.extra.get("liquidated_collateral_amount")
        if collateral_asset and collateral_amount is not None:
            bucket(collateral_asset)["collateral_raw"] -= int(collateral_amount)

    def position_state(
        self,
        user_address: str,
        price_oracle: PriceOracle,
        as_of_block: int,
        as_of_timestamp: datetime,
        protocol: str = "aave-v2",
        chain: str = "ethereum",
    ) -> PositionState:
        """Build a PositionState by pricing this user's raw balances across all their reserves.

        liquidation_threshold is the collateral-value-weighted average across
        reserves, resolving the simplification flagged as deferred in
        docs/data_flow_sketch.md (Phase 0/1): a real per-reserve threshold is
        now used, not a single borrowed number.
        """
        total_collateral = 0.0
        total_debt = 0.0
        weighted_threshold_numerator = 0.0

        for reserve_address, balances in self.raw_balances(user_address).items():
            config = get_reserve_config(reserve_address)
            price = price_oracle.get_price(reserve_address)
            collateral_value = (balances["collateral_raw"] / 10**config.decimals) * price
            debt_value = (balances["debt_raw"] / 10**config.decimals) * price
            total_collateral += collateral_value
            total_debt += debt_value
            weighted_threshold_numerator += collateral_value * config.liquidation_threshold

        liquidation_threshold = (
            weighted_threshold_numerator / total_collateral if total_collateral > 0 else 0.0
        )

        return PositionState(
            protocol=protocol,
            chain=chain,
            user_address=user_address,
            total_collateral_usd=total_collateral,
            total_debt_usd=total_debt,
            liquidation_threshold=liquidation_threshold,
            as_of_block=as_of_block,
            as_of_timestamp=as_of_timestamp,
        )
