# Phase 1 findings — data foundation

*What was actually confirmed, what changed from the Phase 0 plan, and what's still not independently verified. Read alongside `docs/data_flow_sketch.md` (Phase 0's writeup, which this supersedes in a few places).*

## The single biggest finding: no verified Aave v3 Substreams package exists

Phase 0 targeted Aave v3 on Ethereum. Phase 1 searched substreams.dev for a published v3-specific package and found none — only **Aave v2** has a real, downloadable, maintained package (`aave-v2-lending-pool` v0.1.4, by streamingfast). Rather than build a custom Substreams module from scratch (a much bigger undertaking, and against this project's own "reuse before building" principle), Phase 1's real, working pipeline targets **`aave-v2-ethereum`** instead. `aave-v3-ethereum` is a stub raising `NotImplementedError` until a real package is found or built — see `monitor/protocols/aave_v3_ethereum.py`.

This is exactly what the generic `ProtocolConfig`/registry architecture from Phase 0 was for: switching the concrete target didn't touch `models.py`, the ingestion pipeline, or any test for something else.

## How the real Aave v2 config was verified (not guessed)

1. Found the package page: `substreams.dev/packages/aave-v2-lending-pool/v0.1.4`.
2. Found its actual binary download at `https://spkg.io/streamingfast/aave-v2-lending-pool-v0.1.4.spkg` (vendored into `substreams_packages/` — 553KB, small enough to commit).
3. **Decoded it as what it actually is**: a `.spkg` file is itself a serialized `sf.substreams.v1.Package` protobuf message. Fetching the real proto definitions from `github.com/streamingfast/substreams` and parsing the file directly (not reading about it — parsing it) gave real, load-bearing facts:
   - `network: "mainnet"` — Ethereum mainnet, confirming Phase 0's chain choice.
   - Module `map_events` (kind: map), `output_type: "proto:contract.v1.Events"`, `initial_block: 11367463` — the real starting block, the real output module name to request, and the real output message type.
   - The package's embedded `FileDescriptorProto` set contains the **exact schema** for `contract.v1.Events` and its 15 sub-messages (`Borrow`, `Deposit`, `Withdraw`, `Repay`, `LiquidationCall`, etc.) — extracted field-by-field into `protos/contract/v1/contract.proto`, not written from documentation or guessed.
4. The Aave V2 `LendingPool` contract address (`0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9`) was separately verified via Etherscan.

## Correction to Phase 0's assumption about event topics

Phase 0's `SubstreamsSource` model assumed we'd need raw EVM log topic hashes (`event_topics: dict[EventKind, str]`) to filter undecoded logs ourselves. Finding #3 above showed this was wrong: the real package's `map_events` module already emits **fully decoded, structured events** — Rust/WASM code inside the Substreams module does the log-parsing, not us. `SubstreamsSource` was revised to drop `event_topics` entirely in favor of `output_module`/`network`/`initial_block`. This is a real example of why Phase 0 flagged its own assumptions as unverified rather than final.

## What's real vs. what still needs a live token

**Real and tested, without needing a live connection:**
- The compiled gRPC stubs (`monitor/substreams_pb/`), generated from the actual official `.proto` files (vendored in `protos/`), not hand-written.
- `AaveV2EventDecoder`, tested against real, serialized `contract.v1.Events` messages built with the real schema (`monitor/tests/test_aave_v2_decoder.py`).
- `CursorStore` (SQLite-backed persistence) and `InMemoryEventBus`, both fully tested.
- **The actual Phase 1 exit condition** — resume-after-crash with no gap and no duplicate — tested end-to-end via `FakeSubstreamsClient` replaying real-schema messages (`monitor/tests/test_sink_resume.py`). This is the pipeline's real logic (decode → cursor persist → publish → resume), exercised for real; only the network transport underneath is swapped for a deterministic fake.

**Written against the real spec, but NOT independently verified against a live stream:** `GrpcSubstreamsClient` in `monitor/ingestion/substreams_client.py`. No `SUBSTREAMS_API_TOKEN` was available while building this. The request-building (auth metadata, `Request.modules` from the real loaded package, `output_module="map_events"`) and response-parsing (`BlockScopedData`/`BlockUndoSignal` field names) follow the real, fetched RPC v2 spec exactly — but "follows the spec" and "confirmed against a live endpoint" are different claims. Get a token (see below) and run it for real before trusting it in anything higher-stakes than a manual smoke test.

## Getting a real SUBSTREAMS_API_TOKEN

1. Follow `substreams.streamingfast.io/reference-and-specs/authentication` to generate a token (StreamingFast/Pinax auth).
2. Set it in `.env` (`cp .env.example .env` first): `SUBSTREAMS_API_TOKEN=...`
3. Manual smoke test once you have one:
   ```python
   import asyncio, monitor
   from monitor.config import settings
   from monitor.ingestion.substreams_client import GrpcSubstreamsClient


   async def main():
       client = GrpcSubstreamsClient(
           endpoint=settings.substreams_endpoint,
           api_token=settings.substreams_api_token,
           package_path="substreams_packages/aave-v2-lending-pool-v0.1.4.spkg",
           output_module="map_events",
       )
       async for message in client.stream(start_cursor=None):
           print(message.kind, message.block_number)
           break  # just prove one real message arrives


   asyncio.run(main())
   ```
   If this prints one real block/message, `GrpcSubstreamsClient` is confirmed live — update this doc to move it into the "real and tested" list above.

## A bug worth remembering (process note, not a code note)

The resume-after-crash test hung indefinitely on first attempt: `range(bus.qsize() + 1)` called one extra blocking `.get()` on an already-empty queue, deadlocking the test forever with the event loop idling in `select()`. Isolating it required bisecting file-by-file, then reproducing the exact test logic in a standalone script (which worked fine!) before spotting that the actual test file still had the bug in a *second*, easy-to-miss occurrence that an earlier fix had only applied to the first. Lesson: when a targeted string-replace fix is applied to one of several near-identical occurrences, explicitly check for the others rather than assuming a single match was the only one.
