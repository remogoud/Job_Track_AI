"""
Job_Track_AI - SQLite connection + schema initialisation.

Thread-safe via `check_same_thread=False` + a connection lock, so the Tkinter
UI and worker threads can share the DB. The path is configurable so a user can
move the database anywhere (offline control) or point at a file on a sync mount.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Iterator

from config.settings import settings

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")

_lock = threading.RLock()
_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """Return a shared connection, creating the DB + schema on first use."""
    global _connection
    with _lock:
        if _connection is None:
            db_path = settings.effective_db_path
            db_path.parent.mkdir(parents=True, exist_ok=True)
            _connection = sqlite3.connect(str(db_path), check_same_thread=False)
            _connection.row_factory = sqlite3.Row
            _connection.execute("PRAGMA foreign_keys = ON;")
            _connection.execute("PRAGMA journal_mode = WAL;")
            _connection.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
            _connection.commit()
        return _connection


def close() -> None:
    global _connection
    with _lock:
        if _connection is not None:
            _connection.close()
            _connection = None


def transaction() -> sqlite3.Connection:
    """Use as a context manager for explicit transactions."""
    return get_connection()


def execute(sql: str, params: tuple = ()) -> int:
    """Execute a single statement, returning lastrowid."""
    with _lock:
        cur = get_connection().execute(sql, params)
        get_connection().commit()
        return cur.lastrowid


def executemany(sql: str, rows: list[tuple]) -> None:
    with _lock:
        get_connection().executemany(sql, rows)
        get_connection().commit()


def fetchall(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with _lock:
        return get_connection().execute(sql, params).fetchall()


def fetchone(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    with _lock:
        return get_connection().execute(sql, params).fetchone()


def query(sql: str, params: tuple = ()) -> Iterator[sqlite3.Row]:
    with _lock:
        yield from get_connection().execute(sql, params)
