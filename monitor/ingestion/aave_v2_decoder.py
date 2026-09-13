"""Decodes the Aave v2 Substreams package's raw output into NormalizedEvents.

Only the five lending-lifecycle events relevant to health-factor scoring are
decoded (Deposit, Withdraw, Borrow, Repay, LiquidationCall) — the package
also emits Paused/Swap/Upgraded/etc., left unnormalized for now. Narrower
scope now is a correctness strategy, not just less work: fewer fields to get
wrong, matching the same principle already applied to picking one protocol
and one chain for Phase 1.
"""

from contract.v1 import contract_pb2  # importable via monitor/__init__.py's sys.path shim

from monitor.protocols.models import EventKind, NormalizedEvent


def _address(raw: bytes) -> str:
    """Render a raw 20-byte address as the usual 0x-prefixed hex string."""
    return "0x" + raw.hex()


def _tx_hash(raw: str) -> str:
    """The package already emits tx hashes as 0x-prefixed strings; pass through."""
    return raw


class AaveV2EventDecoder:
    """Decodes one block's contract.v1.Events payload into NormalizedEvents."""

    def decode(self, raw_output: bytes) -> list[NormalizedEvent]:
        """Parse raw_output as contract.v1.Events and map each event to a NormalizedEvent."""
        events = contract_pb2.Events()
        events.ParseFromString(raw_output)

        normalized: list[NormalizedEvent] = []
        normalized.extend(self._deposits(events))
        normalized.extend(self._withdraws(events))
        normalized.extend(self._borrows(events))
        normalized.extend(self._repays(events))
        normalized.extend(self._liquidations(events))
        return normalized

    def _deposits(self, events: contract_pb2.Events) -> list[NormalizedEvent]:
        return [
            NormalizedEvent(
                kind=EventKind.SUPPLY,
                protocol="aave-v2",
                chain="ethereum",
                tx_hash=_tx_hash(e.evt_tx_hash),
                log_index=e.evt_index,
                block_number=e.evt_block_number,
                block_time=e.evt_block_time.ToDatetime(),
                user_address=_address(e.user),
                reserve_address=_address(e.reserve),
                amount_raw=e.amount,
            )
            for e in events.deposits
        ]

    def _withdraws(self, events: contract_pb2.Events) -> list[NormalizedEvent]:
        return [
            NormalizedEvent(
                kind=EventKind.WITHDRAW,
                protocol="aave-v2",
                chain="ethereum",
                tx_hash=_tx_hash(e.evt_tx_hash),
                log_index=e.evt_index,
                block_number=e.evt_block_number,
                block_time=e.evt_block_time.ToDatetime(),
                user_address=_address(e.user),
                reserve_address=_address(e.reserve),
                amount_raw=e.amount,
            )
            for e in events.withdraws
        ]

    def _borrows(self, events: contract_pb2.Events) -> list[NormalizedEvent]:
        return [
            NormalizedEvent(
                kind=EventKind.BORROW,
                protocol="aave-v2",
                chain="ethereum",
                tx_hash=_tx_hash(e.evt_tx_hash),
                log_index=e.evt_index,
                block_number=e.evt_block_number,
                block_time=e.evt_block_time.ToDatetime(),
                user_address=_address(e.user),
                reserve_address=_address(e.reserve),
                amount_raw=e.amount,
            )
            for e in events.borrows
        ]

    def _repays(self, events: contract_pb2.Events) -> list[NormalizedEvent]:
        return [
            NormalizedEvent(
                kind=EventKind.REPAY,
                protocol="aave-v2",
                chain="ethereum",
                tx_hash=_tx_hash(e.evt_tx_hash),
                log_index=e.evt_index,
                block_number=e.evt_block_number,
                block_time=e.evt_block_time.ToDatetime(),
                user_address=_address(e.user),
                reserve_address=_address(e.reserve),
                amount_raw=e.amount,
            )
            for e in events.repays
        ]

    def _liquidations(self, events: contract_pb2.Events) -> list[NormalizedEvent]:
        return [
            NormalizedEvent(
                kind=EventKind.LIQUIDATION,
                protocol="aave-v2",
                chain="ethereum",
                tx_hash=_tx_hash(e.evt_tx_hash),
                log_index=e.evt_index,
                block_number=e.evt_block_number,
                block_time=e.evt_block_time.ToDatetime(),
                user_address=_address(e.user),
                reserve_address=_address(e.debt_asset),
                amount_raw=e.debt_to_cover,
                extra={
                    "collateral_asset": _address(e.collateral_asset),
                    "liquidated_collateral_amount": e.liquidated_collateral_amount,
                    "liquidator": _address(e.liquidator),
                },
            )
            for e in events.liquidation_calls
        ]
