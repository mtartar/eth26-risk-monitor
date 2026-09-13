"""Tests for InMemoryEventBus."""

from datetime import datetime, timezone

import pytest

from monitor.ingestion.event_bus import InMemoryEventBus
from monitor.protocols.models import EventKind, NormalizedEvent


def _event(tx_hash: str) -> NormalizedEvent:
    return NormalizedEvent(
        kind=EventKind.SUPPLY,
        protocol="aave-v2",
        chain="ethereum",
        tx_hash=tx_hash,
        log_index=0,
        block_number=1,
        block_time=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_publish_then_get_roundtrips():
    """An event published is the same event received."""
    bus = InMemoryEventBus()
    await bus.publish(_event("0xabc"))
    received = await bus.get()
    assert isinstance(received, NormalizedEvent)
    assert received.tx_hash == "0xabc"


@pytest.mark.asyncio
async def test_events_are_delivered_in_publish_order():
    """The bus is a queue, not a set — order is preserved."""
    bus = InMemoryEventBus()
    await bus.publish(_event("0x1"))
    await bus.publish(_event("0x2"))
    first = await bus.get()
    second = await bus.get()
    assert isinstance(first, NormalizedEvent)
    assert isinstance(second, NormalizedEvent)
    assert first.tx_hash == "0x1"
    assert second.tx_hash == "0x2"


@pytest.mark.asyncio
async def test_qsize_reflects_unconsumed_events():
    """Qsize is a plain read of how many events are waiting."""
    bus = InMemoryEventBus()
    await bus.publish(_event("0x1"))
    await bus.publish(_event("0x2"))
    assert bus.qsize() == 2
    await bus.get()
    assert bus.qsize() == 1
