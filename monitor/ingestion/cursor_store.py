"""SQLite-backed cursor persistence — how the sink survives a restart.

SQLite, not Postgres: a cursor is one small row per protocol/chain, written
once per block at single-digit-events/sec throughput (see
poc-thegraph/03_names_and_architecture.md §3.3) — a file-backed database is
plenty, and it means Phase 1 doesn't depend on a running Postgres service.
Swapping to Postgres later (for multi-instance deployments) means changing
this one file, not anything that calls it.
"""

import sqlite3
from pathlib import Path


class CursorStore:
    """Persists the last-processed Substreams cursor per protocol/chain key."""

    def __init__(self, db_path: str):
        """Open (creating if needed) the SQLite file and its one table."""
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cursors (
                protocol_chain TEXT PRIMARY KEY,
                cursor TEXT NOT NULL,
                block_number INTEGER NOT NULL
            )
            """
        )
        self._conn.commit()

    def get(self, protocol_chain: str) -> str | None:
        """Return the last-persisted cursor for this key, or None if never set."""
        row = self._conn.execute(
            "SELECT cursor FROM cursors WHERE protocol_chain = ?", (protocol_chain,)
        ).fetchone()
        return row[0] if row else None

    def set(self, protocol_chain: str, cursor: str, block_number: int) -> None:
        """Persist the cursor for this key, replacing any previous value."""
        self._conn.execute(
            """
            INSERT INTO cursors (protocol_chain, cursor, block_number) VALUES (?, ?, ?)
            ON CONFLICT(protocol_chain) DO UPDATE SET cursor = excluded.cursor,
                block_number = excluded.block_number
            """,
            (protocol_chain, cursor, block_number),
        )
        self._conn.commit()

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self._conn.close()
