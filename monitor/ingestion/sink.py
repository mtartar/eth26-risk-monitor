"""Orchestrates one protocol/chain's ingestion: client -> decoder -> cursor -> bus."""

from monitor.ingestion.cursor_store import CursorStore
from monitor.ingestion.event_bus import EventBus, UndoSignal
from monitor.ingestion.substreams_client import SubstreamsClient
from monitor.protocols.models import EventDecoder


class SubstreamsSink:
    """Consumes one protocol/chain's Substreams stream and publishes normalized events."""

    def __init__(
        self,
        protocol_chain_key: str,
        protocol: str,
        chain: str,
        client: SubstreamsClient,
        decoder: EventDecoder,
        cursor_store: CursorStore,
        event_bus: EventBus,
    ):
        """Wire up the collaborators this sink coordinates."""
        self._key = protocol_chain_key
        self._protocol = protocol
        self._chain = chain
        self._client = client
        self._decoder = decoder
        self._cursor_store = cursor_store
        self._event_bus = event_bus

    async def run(self) -> None:
        """Resume from the last persisted cursor (if any) and process until the stream ends."""
        cursor = self._cursor_store.get(self._key)
        async for message in self._client.stream(cursor):
            if message.kind == "block":
                assert message.map_output is not None
                for event in self._decoder.decode(message.map_output):
                    await self._event_bus.publish(event)
            elif message.kind == "undo":
                await self._event_bus.publish(
                    UndoSignal(
                        protocol=self._protocol,
                        chain=self._chain,
                        last_valid_block=message.block_number,
                    )
                )
            self._cursor_store.set(self._key, message.cursor, message.block_number)
