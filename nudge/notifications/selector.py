"""Decide who is eligible for each nudge type. Frequency caps are applied later, by the scheduler."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime

from .. import config
from ..timeutil import days_ago


@dataclass
class Candidate:
    user_id: str
    context: dict = field(default_factory=dict)


def select(conn, nudge_type: str, now: datetime) -> list[Candidate]:
    return _SELECTORS[nudge_type](conn, now)


def _opted_in_users(conn) -> set[str]:
    return {r["id"] for r in conn.execute("SELECT id FROM users WHERE push_opt_in = 1")}


def _recently_sent(conn, nudge_type: str, since: str) -> set[str]:
    rows = conn.execute(
        "SELECT DISTINCT user_id FROM nudges WHERE nudge_type = ? AND status = 'sent' AND sent_at >= ?",
        (nudge_type, since),
    )
    return {r["user_id"] for r in rows}


def _first_goal_names(conn) -> dict[str, str]:
    names: dict[str, str] = {}
    for r in conn.execute("SELECT user_id, name FROM goals WHERE status = 'active' ORDER BY created_at, id"):
        names.setdefault(r["user_id"], r["name"])
    return names


def _goal_reminder(conn, now: datetime) -> list[Candidate]:
    # Users who are saving toward something. A linked savings account is how we find them:
    # in v1 the goal lived on the savings account itself.
    skip = _recently_sent(conn, "goal_reminder", days_ago(now, 7))
    opted_in = _opted_in_users(conn)
    names = _first_goal_names(conn)
    rows = conn.execute("SELECT DISTINCT user_id FROM accounts WHERE type = 'savings' ORDER BY user_id")
    return [
        Candidate(r["user_id"], {"goal_name": names[r["user_id"]]} if r["user_id"] in names else {})
        for r in rows
        if r["user_id"] in opted_in and r["user_id"] not in skip
    ]


def _milestone(conn, now: datetime) -> list[Candidate]:
    opted_in = _opted_in_users(conn)
    sent: dict[str, int] = {}  # goal_id -> highest threshold already sent
    for r in conn.execute("SELECT payload FROM nudges WHERE nudge_type = 'milestone' AND status = 'sent'"):
        p = json.loads(r["payload"])
        if "goal_id" in p:
            sent[p["goal_id"]] = max(sent.get(p["goal_id"], 0), p["threshold"])
    out = []
    goals = conn.execute(
        "SELECT id, user_id, name, target_cents, saved_cents FROM goals "
        "WHERE target_cents > 0 AND status IN ('active', 'achieved') ORDER BY user_id, id"
    )
    for g in goals:
        pct = g["saved_cents"] * 100 // g["target_cents"]
        crossed = [t for t in config.MILESTONE_THRESHOLDS if pct >= t]
        if not crossed or g["user_id"] not in opted_in:
            continue
        top = max(crossed)
        if top > sent.get(g["id"], 0):
            out.append(Candidate(g["user_id"], {"goal_id": g["id"], "goal_name": g["name"], "threshold": top}))
    return out


def _re_engagement(conn, now: datetime) -> list[Candidate]:
    # Inactive for a few days, but not so long gone that a push is pointless (30 days).
    skip = _recently_sent(conn, "re_engagement", days_ago(now, 14))
    rows = conn.execute(
        "SELECT id FROM users WHERE push_opt_in = 1 AND last_active_at IS NOT NULL "
        "AND last_active_at <= ? AND last_active_at >= ? ORDER BY id",
        (days_ago(now, config.RE_ENGAGEMENT_INACTIVE_DAYS), days_ago(now, 30)),
    )
    return [Candidate(r["id"]) for r in rows if r["id"] not in skip]


def _spending_alert(conn, now: datetime) -> list[Candidate]:
    this_week, two_weeks = days_ago(now, 7), days_ago(now, 14)
    rows = conn.execute(
        "SELECT user_id, category, "
        "SUM(CASE WHEN posted_at >= ? THEN -amount_cents ELSE 0 END) AS cur, "
        "SUM(CASE WHEN posted_at < ? THEN -amount_cents ELSE 0 END) AS prev "
        "FROM transactions WHERE amount_cents < 0 AND posted_at >= ? AND category IS NOT NULL "  # can't name a category we don't know
        "GROUP BY user_id, category",
        (this_week, this_week, two_weeks),
    )
    best: dict[str, tuple[int, str]] = {}
    for r in rows:
        spiked = r["prev"] == 0 or r["cur"] / r["prev"] >= config.SPENDING_ALERT_RATIO
        if r["cur"] >= config.SPENDING_ALERT_MIN_CENTS and spiked:
            if r["user_id"] not in best or r["cur"] > best[r["user_id"]][0]:
                best[r["user_id"]] = (r["cur"], r["category"])
    opted_in = _opted_in_users(conn)
    skip = _recently_sent(conn, "spending_alert", days_ago(now, 7))
    return [
        Candidate(uid, {"category": cat})
        for uid, (_, cat) in sorted(best.items())
        if uid in opted_in and uid not in skip
    ]


def _weekly_tip(conn, now: datetime) -> list[Candidate]:
    skip = _recently_sent(conn, "weekly_tip", days_ago(now, 7))
    rows = conn.execute(
        "SELECT id FROM users WHERE push_opt_in = 1 AND created_at <= ? ORDER BY id", (days_ago(now, 1),)
    )
    return [Candidate(r["id"]) for r in rows if r["id"] not in skip]


_SELECTORS = {
    "goal_reminder": _goal_reminder,
    "milestone": _milestone,
    "re_engagement": _re_engagement,
    "spending_alert": _spending_alert,
    "weekly_tip": _weekly_tip,
}
