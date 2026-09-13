"""Tests for CursorStore's SQLite-backed persistence."""

from monitor.ingestion.cursor_store import CursorStore


def test_get_returns_none_when_never_set(tmp_path):
    """A fresh store has no cursor for a key it's never seen."""
    store = CursorStore(str(tmp_path / "cursors.sqlite3"))
    assert store.get("aave-v2-ethereum") is None


def test_set_then_get_roundtrips():
    """A persisted cursor comes back exactly as it was set."""
    store = CursorStore(":memory:")
    store.set("aave-v2-ethereum", "cursor-abc", 100)
    assert store.get("aave-v2-ethereum") == "cursor-abc"


def test_set_overwrites_previous_value_for_same_key():
    """Setting a new cursor for the same key replaces the old one, not adds a row."""
    store = CursorStore(":memory:")
    store.set("aave-v2-ethereum", "cursor-1", 100)
    store.set("aave-v2-ethereum", "cursor-2", 101)
    assert store.get("aave-v2-ethereum") == "cursor-2"


def test_survives_reopening_the_same_file(tmp_path):
    """A cursor persisted before 'closing' is still there after reopening the file.

    This is the core guarantee a resume-after-crash depends on: the process
    can die and restart, and as long as it points at the same db file, it
    picks up where it left off.
    """
    db_path = str(tmp_path / "cursors.sqlite3")
    first = CursorStore(db_path)
    first.set("aave-v2-ethereum", "cursor-xyz", 500)
    first.close()

    second = CursorStore(db_path)
    assert second.get("aave-v2-ethereum") == "cursor-xyz"
