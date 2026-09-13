"""Hands normalized events (and reorg undo signals) from the sink to whatever consumes them next.

In-process asyncio.Queue, not Redis Streams: Phase 1's sink and its one
consumer run in the same process, so a queue genuinely is the real
implementation, not a stand-in. Redis Streams becomes worth its own
operational overhead once there are multiple processes/consumers (Phase 4+,
per poc-thegraph/03_names_and_architecture.md §3.3) — EventBus is a Protocol
specifically so that swap is a new class, not a rewrite of the sink.
"""

import asyncio
from typing import Protocol

from pydantic import BaseModel

from monitor.protocols.models import NormalizedEvent


class UndoSignal(BaseModel):
    """Tells consumers to revert any state built from events after last_valid_block.

    Phase 1's sink persisted the cursor on a reorg but never told downstream
    consumers about it (see sink.py's original docstring) — this is that gap
    closed: the scoring engine (Phase 2) needs this to call
    PositionLedger.undo() at the right point.
    """

    protocol: str
    chain: str
    last_valid_block: int


BusMessage = NormalizedEvent | UndoSignal


class EventBus(Protocol):
    """Publishes normalized events and undo signals for downstream consumers to read."""

    async def publish(self, message: BusMessage) -> None:
        """Publish one message."""
        ...

    async def get(self) -> BusMessage:
        """Block until the next published message is available."""
        ...


class InMemoryEventBus:
    """A single-process EventBus backed by asyncio.Queue."""

    def __init__(self) -> None:
        """Create an unbounded in-memory queue."""
        self._queue: asyncio.Queue[BusMessage] = asyncio.Queue()

    async def publish(self, message: BusMessage) -> None:
        """Enqueue one message."""
        await self._queue.put(message)

    async def get(self) -> BusMessage:
        """Dequeue the next message, waiting if none is available yet."""
        return await self._queue.get()

    def qsize(self) -> int:
        """Return the number of messages currently queued (mainly for tests)."""
        return self._queue.qsize()
