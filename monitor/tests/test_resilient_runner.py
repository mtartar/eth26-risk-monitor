"""Chaos test: a sink that errors gets retried, not crashed.

This is the real, scoped-down version of Phase 4/5's "graceful degradation"
requirement — see monitor/ingestion/resilient_runner.py's module docstring
for why the originally-planned fallback (to graph-lending-mcp/Token API
polling) isn't what's tested here: that integration was never built.
"""

import pytest

from monitor.ingestion.resilient_runner import run_with_retry


class _FlakySink:
    """Fails its first N calls to run(), then succeeds — simulates a real outage that clears."""

    def __init__(self, fail_times: int):
        self.fail_times = fail_times
        self.attempts = 0

    async def run(self) -> None:
        self.attempts += 1
        if self.attempts <= self.fail_times:
            raise ConnectionError("simulated Substreams outage")
        # Succeeds: represents the stream ending normally after recovering.


class _AlwaysFailsSink:
    """Never recovers — simulates a genuinely broken configuration."""

    def __init__(self):
        self.attempts = 0

    async def run(self) -> None:
        self.attempts += 1
        raise ConnectionError("simulated permanent outage")


@pytest.mark.asyncio
async def test_recovers_after_transient_failures_without_crashing():
    """An outage that clears after 2 attempts is retried, not propagated."""
    sink = _FlakySink(fail_times=2)
    await run_with_retry(sink, max_retries=5, base_delay_seconds=0.01)
    assert sink.attempts == 3  # 2 failures + 1 success


@pytest.mark.asyncio
async def test_gives_up_and_raises_after_max_retries():
    """A permanently broken sink surfaces loudly rather than retrying forever silently."""
    sink = _AlwaysFailsSink()
    with pytest.raises(ConnectionError):
        await run_with_retry(sink, max_retries=3, base_delay_seconds=0.01)
    assert sink.attempts == 4  # initial attempt + 3 retries


@pytest.mark.asyncio
async def test_succeeds_immediately_with_no_retries_needed():
    """The common case — no error at all — doesn't wait or retry."""
    sink = _FlakySink(fail_times=0)
    await run_with_retry(sink, max_retries=5, base_delay_seconds=0.01)
    assert sink.attempts == 1
