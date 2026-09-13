"""Tests for AaveV2EventDecoder against real contract_pb2 messages.

These build actual contract.v1.Events protobuf messages (the real, extracted
schema — see protos/contract/v1/contract.proto) and serialize/parse them for
real, rather than mocking the protobuf layer — this is what would otherwise
be the least-trustworthy part of the pipeline if left untested.
"""

from contract.v1 import contract_pb2  # importable via monitor/__init__.py's sys.path shim

from monitor.ingestion.aave_v2_decoder import AaveV2EventDecoder
from monitor.protocols.models import EventKind

_USER = b"\x11" * 20
_RESERVE = b"\x22" * 20


def test_decode_maps_deposit_to_supply_event():
    """A real Deposit event decodes to a NormalizedEvent with kind=SUPPLY."""
    events = contract_pb2.Events(
        deposits=[
            contract_pb2.Deposit(
                evt_tx_hash="0xabc",
                evt_index=3,
                evt_block_number=100,
                reserve=_RESERVE,
                user=_USER,
                amount="5000000",
            )
        ]
    )

    normalized = AaveV2EventDecoder().decode(events.SerializeToString())

    assert len(normalized) == 1
    event = normalized[0]
    assert event.kind == EventKind.SUPPLY
    assert event.protocol == "aave-v2"
    assert event.tx_hash == "0xabc"
    assert event.log_index == 3
    assert event.block_number == 100
    assert event.user_address == "0x" + _USER.hex()
    assert event.reserve_address == "0x" + _RESERVE.hex()
    assert event.amount_raw == "5000000"


def test_decode_maps_all_five_lifecycle_event_kinds():
    """Each of the five decoded event lists maps to its expected EventKind."""
    events = contract_pb2.Events(
        deposits=[contract_pb2.Deposit(evt_tx_hash="0x1", user=_USER, reserve=_RESERVE)],
        withdraws=[contract_pb2.Withdraw(evt_tx_hash="0x2", user=_USER, reserve=_RESERVE)],
        borrows=[contract_pb2.Borrow(evt_tx_hash="0x3", user=_USER, reserve=_RESERVE)],
        repays=[contract_pb2.Repay(evt_tx_hash="0x4", user=_USER, reserve=_RESERVE)],
        liquidation_calls=[
            contract_pb2.LiquidationCall(
                evt_tx_hash="0x5",
                user=_USER,
                debt_asset=_RESERVE,
                collateral_asset=_RESERVE,
                liquidator=_USER,
            )
        ],
    )

    normalized = AaveV2EventDecoder().decode(events.SerializeToString())

    kinds_by_tx = {e.tx_hash: e.kind for e in normalized}
    assert kinds_by_tx == {
        "0x1": EventKind.SUPPLY,
        "0x2": EventKind.WITHDRAW,
        "0x3": EventKind.BORROW,
        "0x4": EventKind.REPAY,
        "0x5": EventKind.LIQUIDATION,
    }


def test_decode_liquidation_carries_collateral_details_in_extra():
    """Liquidation-specific fields land in `extra` rather than being dropped."""
    events = contract_pb2.Events(
        liquidation_calls=[
            contract_pb2.LiquidationCall(
                evt_tx_hash="0x5",
                user=_USER,
                debt_asset=_RESERVE,
                collateral_asset=b"\x33" * 20,
                liquidated_collateral_amount="42",
                liquidator=b"\x44" * 20,
            )
        ]
    )

    normalized = AaveV2EventDecoder().decode(events.SerializeToString())

    assert normalized[0].extra["collateral_asset"] == "0x" + (b"\x33" * 20).hex()
    assert normalized[0].extra["liquidated_collateral_amount"] == "42"
    assert normalized[0].extra["liquidator"] == "0x" + (b"\x44" * 20).hex()


def test_decode_ignores_unmapped_event_types():
    """Event types outside the five lifecycle ones (e.g. Paused) are simply skipped."""
    events = contract_pb2.Events(pauseds=[contract_pb2.Paused(evt_tx_hash="0x1")])

    normalized = AaveV2EventDecoder().decode(events.SerializeToString())

    assert normalized == []
