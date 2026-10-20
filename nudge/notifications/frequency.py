"""Global push frequency cap (docs/adr/0003-global-push-frequency-cap.md)."""
from __future__ import annotations

from datetime import datetime

from .. import config
from ..timeutil import days_ago


def sent_count(conn, user_id: str, now: datetime, days: int = 7) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM nudges WHERE user_id = ? AND status = 'sent' AND sent_at > ?",
        (user_id, days_ago(now, days)),
    ).fetchone()[0]


def can_send(conn, user, now: datetime) -> bool:
    if not user["push_opt_in"]:
        return False
    return sent_count(conn, user["id"], now) < config.MAX_PUSH_PER_7_DAYS
