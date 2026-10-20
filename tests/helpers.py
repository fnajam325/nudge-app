from __future__ import annotations

from datetime import datetime, timedelta, timezone

from nudge import accounts, db, goals, users
from nudge.timeutil import iso

# A Monday, inside the send hour.
NOW = datetime(2026, 2, 2, 15, 0, tzinfo=timezone.utc)


def make_conn():
    conn = db.connect(":memory:")
    db.migrate(conn)
    return conn


def add_user(conn, user_id="u1", days_old=10, active_days_ago=0, **kwargs):
    """Create a user. By default they were active today, so they are not a re-engagement candidate."""
    user = users.create_user(conn, user_id, NOW - timedelta(days=days_old), **kwargs)
    users.touch_active(conn, user_id, NOW - timedelta(days=active_days_ago))
    return user


def add_account(conn, user_id="u1", account_type="checking", account_id=None):
    account_id = account_id or f"{user_id}-{account_type}"
    accounts.link_account(conn, account_id, user_id, account_type, "Test Bank", NOW - timedelta(days=9))
    return account_id


def add_goal(conn, user_id="u1", goal_id=None, name="vacation", target_cents=100_000, saved_cents=0):
    goal_id = goal_id or f"g-{user_id}"
    goals.create_goal(conn, goal_id, user_id, name, target_cents, NOW - timedelta(days=8))
    if saved_cents:
        goals.record_saving(conn, goal_id, saved_cents)
    return goal_id


def add_txn(conn, txn_id, user_id, account_id, days_ago, amount_cents, merchant="Whole Foods", category=None):
    conn.execute(
        "INSERT INTO transactions (id, account_id, user_id, posted_at, amount_cents, merchant, category) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (txn_id, account_id, user_id, iso(NOW - timedelta(days=days_ago)), amount_cents, merchant, category),
    )
    conn.commit()


def add_nudge(conn, user_id, nudge_type, days_ago, status="sent", payload="{}"):
    conn.execute(
        "INSERT INTO nudges (id, user_id, nudge_type, status, payload, sent_at) VALUES (?, ?, ?, ?, ?, ?)",
        (f"n-{user_id}-{nudge_type}-{days_ago}-{status}", user_id, nudge_type, status, payload, iso(NOW - timedelta(days=days_ago))),
    )
    conn.commit()


def event_names(conn, user_id=None):
    sql = "SELECT name FROM events" + (" WHERE user_id = ?" if user_id else "") + " ORDER BY id"
    return [r["name"] for r in conn.execute(sql, (user_id,) if user_id else ())]
