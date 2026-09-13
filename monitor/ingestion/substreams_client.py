"""Consumes a Substreams gRPC stream: one real implementation, one fake for tests.

GrpcSubstreamsClient is written against the real, official Substreams RPC v2
spec (vendored in protos/, compiled via scripts/generate_protos.sh) and a
real, downloaded package (substreams_packages/) — but it has NOT been run
against a live endpoint, since no SUBSTREAMS_API_TOKEN was available while
building this. See docs/phase1_findings.md for exactly what is and isn't
verified. FakeSubstreamsClient exists so the rest of the pipeline (decoding,
cursor persistence, resume-after-crash) can be built and tested for real
without needing that token yet.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

import grpc

# importable via monitor/__init__.py's sys.path shim
from sf.substreams.rpc.v2 import service_pb2, service_pb2_grpc
from sf.substreams.v1 import package_pb2


@dataclass
class SubstreamsMessage:
    """One message from a Substreams stream: a new block, or a reorg undo signal."""

    kind: str  # "block" | "undo"
    cursor: str
    block_number: int
    map_output: bytes | None = None  # set when kind == "block"


class SubstreamsClient(Protocol):
    """Streams Substreams messages, resumable from a persisted cursor."""

    def stream(self, start_cursor: str | None) -> AsyncIterator[SubstreamsMessage]:
        """Yield messages starting from start_cursor, or from the configured start block."""
        ...


def load_package(package_path: str) -> package_pb2.Package:
    """Read and parse a .spkg file into its real Package protobuf message."""
    with open(package_path, "rb") as f:
        pkg = package_pb2.Package()
        pkg.ParseFromString(f.read())
    return pkg


class GrpcSubstreamsClient:
    """Real Substreams client: gRPC + Bearer auth against a live endpoint.

    NOT independently verified end-to-end against a live stream (see module
    docstring) — the request-building and response-parsing logic follows the
    real spec exactly, but "follows the spec" and "confirmed working against
    a live endpoint" are different claims, and only the first is true here.
    """

    def __init__(self, endpoint: str, api_token: str, package_path: str, output_module: str):
        """Store connection details and load the package once, up front."""
        self._endpoint = endpoint
        self._api_token = api_token
        self._package = load_package(package_path)
        self._output_module = output_module

    async def stream(self, start_cursor: str | None) -> AsyncIterator[SubstreamsMessage]:
        """Open the gRPC stream and yield decoded block/undo messages."""
        channel = grpc.aio.secure_channel(self._endpoint, grpc.ssl_channel_credentials())
        try:
            stub = service_pb2_grpc.StreamStub(channel)
            request = service_pb2.Request(
                start_cursor=start_cursor or "",
                output_module=self._output_module,
                modules=self._package.modules,
                production_mode=True,
            )
            metadata = (("authorization", f"Bearer {self._api_token}"),)
            async for response in stub.Blocks(request, metadata=metadata):
                message = self._to_message(response)
                if message is not None:
                    yield message
        finally:
            await channel.close()

    def _to_message(self, response: service_pb2.Response) -> SubstreamsMessage | None:
        """Map one Response to a SubstreamsMessage, or None for messages we don't act on."""
        which = response.WhichOneof("message")
        if which == "block_scoped_data":
            data = response.block_scoped_data
            return SubstreamsMessage(
                kind="block",
                cursor=data.cursor,
                block_number=data.clock.number,
                map_output=data.output.map_output.value,
            )
        if which == "block_undo_signal":
            undo = response.block_undo_signal
            return SubstreamsMessage(
                kind="undo",
                cursor=undo.last_valid_cursor,
                block_number=undo.last_valid_block.number,
            )
        # session/progress/fatal_error messages are metadata, not data — ignored here.
        return None


class FakeSubstreamsClient:
    """Replays a fixed, in-memory sequence of messages — for tests and local dev.

    Not "fixture data" in the fabricated-tx-hash sense flagged elsewhere in
    this project's history: this is explicitly synthetic pipeline-test data,
    labeled as such, never presented as real chain activity.
    """

    def __init__(self, messages: list[SubstreamsMessage]):
        """Store the canned message sequence to replay."""
        self._messages = messages

    async def stream(self, start_cursor: str | None) -> AsyncIterator[SubstreamsMessage]:
        """Yield messages after the one matching start_cursor, or all of them if None."""
        started = start_cursor is None
        for message in self._messages:
            if started:
                yield message
            elif message.cursor == start_cursor:
                started = True
