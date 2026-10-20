"""Home feed card builders. Each returns a JSON-ready dict, or None when there is nothing to show."""
from __future__ import annotations

from datetime import datetime

from .. import config, goals
from ..accounts import accounts_for
from ..timeutil import days_ago
from ..transactions.sync import is_stale


def balance_card(conn, user, now: datetime) -> dict | None:
    spendable = [a for a in accounts_for(conn, user["id"]) if a["type"] in ("checking", "savings")]
    if not spendable:
        return None
    synced = [a["last_synced_at"] for a in spendable if a["last_synced_at"]]
    return {
        "type": "balance",
        "total_cents": sum(a["balance_cents"] for a in spendable),
        "as_of": max(synced) if synced else None,
        "stale": any(is_stale(a, now) for a in spendable),
    }


def recent_transactions_card(conn, user, now: datetime) -> dict | None:
    rows = conn.execute(
        "SELECT merchant, amount_cents, posted_at, category FROM transactions "
        "WHERE user_id = ? ORDER BY posted_at DESC, id LIMIT ?",
        (user["id"], config.RECENT_TRANSACTIONS_LIMIT),
    ).fetchall()
    if not rows:
        return None
    return {"type": "recent_transactions", "items": [dict(r) for r in rows]}


def spending_by_category_card(conn, user, now: datetime) -> dict | None:
    rows = conn.execute(
        "SELECT COALESCE(category, 'uncategorized') AS category, SUM(-amount_cents) AS spent_cents "
        "FROM transactions WHERE user_id = ? AND amount_cents < 0 AND posted_at >= ? "
        "GROUP BY 1 ORDER BY spent_cents DESC",
        (user["id"], days_ago(now, config.SPENDING_WINDOW_DAYS)),
    ).fetchall()
    if not rows:
        return None
    return {
        "type": "spending_by_category",
        "window_days": config.SPENDING_WINDOW_DAYS,
        "total_cents": sum(r["spent_cents"] for r in rows),
        "categories": [dict(r) for r in rows[:5]],
    }


def goals_card(conn, user, now: datetime) -> dict:
    active = goals.active_goals(conn, user["id"])
    if not active:
        return {"type": "goals", "goals": [], "cta": "Set a savings goal"}
    return {
        "type": "goals",
        "goals": [{"id": g["id"], "name": g["name"], "progress_pct": goals.progress_pct(g)} for g in active],
    }
