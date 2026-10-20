from __future__ import annotations

from datetime import datetime

from .timeutil import iso


def create_user(
    conn,
    user_id: str,
    now: datetime,
    platform: str = "ios",
    timezone: str = "America/New_York",
    channel: str = "organic",
    push_opt_in: bool = True,
):
    conn.execute(
        "INSERT INTO users (id, created_at, timezone, platform, acquisition_channel, push_opt_in, last_active_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, iso(now), timezone, platform, channel, int(push_opt_in), iso(now)),
    )
    conn.commit()
    return get_user(conn, user_id)


def get_user(conn, user_id: str):
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise KeyError(f"no such user: {user_id}")
    return row


def touch_active(conn, user_id: str, now: datetime) -> None:
    conn.execute("UPDATE users SET last_active_at = ? WHERE id = ?", (iso(now), user_id))
    conn.commit()
