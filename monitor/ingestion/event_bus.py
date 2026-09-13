"""Hands normalized events from the sink to whatever consumes them next.

In-process asyncio.Queue, not Redis Streams: Phase 1's sink and its one
consumer run in the same process, so a queue genuinely is the real
implementation, not a stand-in. Redis Streams becomes worth its own
operational overhead once there are multiple processes/consumers (Phase 4+,
per poc-thegraph/03_names_and_architecture.md §3.3) — EventBus is a Protocol
specifically so that swap is a new class, not a rewrite of the sink.
"""

import asyncio
from typing import Protocol

from monitor.protocols.models import NormalizedEvent


class EventBus(Protocol):
    """Publishes normalized events for downstream consumers to read."""

    async def publish(self, event: NormalizedEvent) -> None:
        """Publish one event."""
        ...

    async def get(self) -> NormalizedEvent:
        """Block until the next published event is available."""
        ...


class InMemoryEventBus:
    """A single-process EventBus backed by asyncio.Queue."""

    def __init__(self) -> None:
        """Create an unbounded in-memory queue."""
        self._queue: asyncio.Queue[NormalizedEvent] = asyncio.Queue()

    async def publish(self, event: NormalizedEvent) -> None:
        """Enqueue one event."""
        await self._queue.put(event)

    async def get(self) -> NormalizedEvent:
        """Dequeue the next event, waiting if none is available yet."""
        return await self._queue.get()

    def qsize(self) -> int:
        """Return the number of events currently queued (mainly for tests)."""
        return self._queue.qsize()
