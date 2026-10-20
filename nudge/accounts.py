from __future__ import annotations

from datetime import datetime

from .analytics import track
from .timeutil import iso


def link_account(conn, account_id: str, user_id: str, account_type: str, institution: str, now: datetime) -> None:
    conn.execute(
        "INSERT INTO accounts (id, user_id, type, institution, linked_at) VALUES (?, ?, ?, ?, ?)",
        (account_id, user_id, account_type, institution, iso(now)),
    )
    conn.commit()
    track(conn, user_id, "account_linked", now, {"account_id": account_id, "type": account_type})


def accounts_for(conn, user_id: str) -> list:
    return conn.execute("SELECT * FROM accounts WHERE user_id = ? ORDER BY id", (user_id,)).fetchall()
