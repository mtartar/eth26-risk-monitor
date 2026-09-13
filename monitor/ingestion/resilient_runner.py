"""Retry-with-backoff wrapper around a sink's run() — the real, scoped-down fallback.

The original Phase 4/5 plan called for falling back from a dead Substreams
stream to graph-lending-mcp/Token API polling — but that integration was
never built (see docs/phase1_findings.md), so there is nothing to fall back
*to*. What's real and testable instead: a Substreams connection error
doesn't crash the whole process. It's logged, retried with exponential
backoff, and resumes from the last persisted cursor (already Phase 1's
resume guarantee) rather than restarting from scratch or taking the app
down. See docs/phase5_findings.md for why this is a deliberate scope
reduction from the original plan, not an oversight.
"""

import asyncio
import logging
from typing import Protocol

logger = logging.getLogger("monitor.ingestion")


class Runnable(Protocol):
    """Anything with an async run() — SubstreamsSink satisfies this without inheriting it."""

    async def run(self) -> None:
        """Run until the underlying stream ends or raises."""
        ...


async def run_with_retry(
    sink: Runnable,
    max_retries: int = 5,
    base_delay_seconds: float = 1.0,
) -> None:
    """Run sink.run(), retrying with exponential backoff if it raises.

    Returns normally once sink.run() completes without error (the
    underlying stream ended on its own — e.g. a finite FakeSubstreamsClient
    in tests/demo mode). Re-raises the last error once max_retries is
    exhausted, so a genuinely broken configuration still surfaces loudly
    rather than retrying forever in silence.
    """
    attempt = 0
    while True:
        try:
            await sink.run()
            return
        except Exception:
            attempt += 1
            if attempt > max_retries:
                logger.exception("Sink failed after %d retries, giving up", max_retries)
                raise
            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Sink error on attempt %d/%d, retrying in %.1fs",
                attempt,
                max_retries,
                delay,
                exc_info=True,
            )
            await asyncio.sleep(delay)
