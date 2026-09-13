"""Phase 1's actual exit condition: kill the sink mid-stream, restart, no gap, no duplicate.

Uses FakeSubstreamsClient (deterministic, in-memory) rather than a live
Substreams connection — no SUBSTREAMS_API_TOKEN is available in this
environment (see docs/phase1_findings.md). What's tested here is real: the
cursor-persistence and resume logic in SubstreamsSink itself, exercised
end-to-end with real (de)serialized contract_pb2.Events payloads.
"""

import pytest
from contract.v1 import contract_pb2  # importable via monitor/__init__.py's sys.path shim

from monitor.ingestion.aave_v2_decoder import AaveV2EventDecoder
from monitor.ingestion.cursor_store import CursorStore
from monitor.ingestion.event_bus import InMemoryEventBus
from monitor.ingestion.sink import SubstreamsSink
from monitor.ingestion.substreams_client import FakeSubstreamsClient, SubstreamsMessage
from monitor.protocols.models import NormalizedEvent

_KEY = "aave-v2-ethereum"


async def _drain_tx_hashes(bus: InMemoryEventBus) -> set[str]:
    """Pull every currently-queued message off the bus and return its tx hashes.

    Snapshotting qsize() once up front (rather than looping with a sentinel)
    is what caused a real deadlock earlier in this project when a stray `+ 1`
    crept into this exact pattern — kept as one shared helper now so that bug
    class can't recur in more than one place.
    """
    count = bus.qsize()
    hashes = set()
    for _ in range(count):
        message = await bus.get()
        assert isinstance(message, NormalizedEvent)
        hashes.add(message.tx_hash)
    return hashes


def _block_message(index: int) -> SubstreamsMessage:
    """Build a real, serialized single-Deposit block message with a distinct tx hash."""
    deposit = contract_pb2.Deposit(
        evt_tx_hash=f"0xtx{index}", user=b"\x11" * 20, reserve=b"\x22" * 20
    )
    events = contract_pb2.Events(deposits=[deposit])
    return SubstreamsMessage(
        kind="block",
        cursor=f"cursor-{index}",
        block_number=index,
        map_output=events.SerializeToString(),
    )


@pytest.mark.asyncio
async def test_resume_after_crash_has_no_gap_and_no_duplicate(tmp_path):
    """Processing 1..5 in two runs (crash after 2) yields exactly tx1..tx5, once each."""
    all_messages = [_block_message(i) for i in range(1, 6)]  # blocks 1..5
    db_path = str(tmp_path / "cursors.sqlite3")

    # Run 1: only the first 2 messages exist for this run — simulates a crash
    # after processing block 2 (i.e. the process never saw blocks 3-5 yet).
    cursor_store_1 = CursorStore(db_path)
    bus_1 = InMemoryEventBus()
    sink_1 = SubstreamsSink(
        _KEY,
        "aave-v2",
        "ethereum",
        FakeSubstreamsClient(all_messages[:2]),
        AaveV2EventDecoder(),
        cursor_store_1,
        bus_1,
    )
    await sink_1.run()
    cursor_store_1.close()

    seen_after_run_1 = await _drain_tx_hashes(bus_1)
    assert seen_after_run_1 == {"0xtx1", "0xtx2"}

    # Run 2: a fresh process (fresh CursorStore connection to the same file,
    # fresh in-memory event bus) with the FULL message list available. It
    # must resume from the persisted cursor, not from the beginning.
    cursor_store_2 = CursorStore(db_path)
    bus_2 = InMemoryEventBus()
    sink_2 = SubstreamsSink(
        _KEY,
        "aave-v2",
        "ethereum",
        FakeSubstreamsClient(all_messages),
        AaveV2EventDecoder(),
        cursor_store_2,
        bus_2,
    )
    await sink_2.run()

    seen_after_run_2 = await _drain_tx_hashes(bus_2)
    assert seen_after_run_2 == {"0xtx3", "0xtx4", "0xtx5"}

    # No gap (all 5 seen across both runs) and no duplicate (no overlap between them).
    assert seen_after_run_1 | seen_after_run_2 == {"0xtx1", "0xtx2", "0xtx3", "0xtx4", "0xtx5"}
    assert seen_after_run_1.isdisjoint(seen_after_run_2)
    assert cursor_store_2.get(_KEY) == "cursor-5"
