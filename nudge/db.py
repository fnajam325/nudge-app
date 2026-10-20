"""SQLite connection and a small forward-only migration runner."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from . import config
from .timeutil import iso, utcnow

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def connect(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn: sqlite3.Connection) -> list[str]:
    """Apply any migrations not yet recorded. Returns the names applied."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    applied = {row["name"] for row in conn.execute("SELECT name FROM schema_migrations")}
    ran = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in applied:
            continue
        conn.executescript(path.read_text())
        conn.execute("INSERT INTO schema_migrations (name, applied_at) VALUES (?, ?)", (path.name, iso(utcnow())))
        conn.commit()
        ran.append(path.name)
    return ran
