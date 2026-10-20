"""Record what users do with a nudge after it is delivered."""
from __future__ import annotations

from datetime import datetime

from ..analytics import track
from ..timeutil import iso


def _nudge(conn, nudge_id: str):
    row = conn.execute("SELECT * FROM nudges WHERE id = ?", (nudge_id,)).fetchone()
    if row is None:
        raise KeyError(f"no such nudge: {nudge_id}")
    return row


def mark_opened(conn, nudge_id: str, now: datetime) -> None:
    nudge = _nudge(conn, nudge_id)
    conn.execute("UPDATE nudges SET opened_at = COALESCE(opened_at, ?) WHERE id = ?", (iso(now), nudge_id))
    conn.commit()
    track(conn, nudge["user_id"], "nudge_opened", now, {"nudge_id": nudge_id})


def mark_acted_on(conn, nudge_id: str, now: datetime) -> None:
    nudge = _nudge(conn, nudge_id)
    conn.execute("UPDATE nudges SET acted_on_at = COALESCE(acted_on_at, ?) WHERE id = ?", (iso(now), nudge_id))
    conn.commit()
    track(conn, nudge["user_id"], "nudge_acted_on", now, {"nudge_id": nudge_id})
