"""Request handlers. The mobile gateway (not in this repo) authenticates the caller and
passes the user id in. Handlers take plain dicts and return plain dicts."""
from __future__ import annotations

from datetime import datetime

from .. import goals, users
from ..analytics import track
from ..analytics.events import CLIENT_EVENTS
from ..feed import compose_home_feed
from ..notifications import engagement


def get_home(conn, user_id: str, now: datetime) -> dict:
    """GET /home"""
    user = users.get_user(conn, user_id)
    users.touch_active(conn, user_id, now)
    return {"user_id": user_id, "cards": compose_home_feed(conn, user, now)}


def post_goal(conn, user_id: str, body: dict, now: datetime) -> dict:
    """POST /goals"""
    name = (body.get("name") or "").strip()
    if not name:
        raise ValueError("goal name is required")
    target_cents = int(body.get("target_cents", 0))
    if target_cents < 0:
        raise ValueError("target_cents must not be negative")
    goal_id = f"g_{user_id}_{len(goals.active_goals(conn, user_id)) + 1}"
    goals.create_goal(conn, goal_id, user_id, name, target_cents, now)
    return {"id": goal_id, "name": name, "target_cents": target_cents}


def post_client_event(conn, user_id: str, body: dict, now: datetime) -> dict:
    """POST /events. Only client-originated events are accepted here."""
    name = body.get("name")
    if name not in CLIENT_EVENTS:
        raise ValueError(f"unsupported client event: {name}")
    properties = body.get("properties") or {}
    if name == "nudge_opened":
        engagement.mark_opened(conn, properties["nudge_id"], now)
    elif name == "nudge_acted_on":
        engagement.mark_acted_on(conn, properties["nudge_id"], now)
    else:
        track(conn, user_id, name, now, properties)
        if name == "app_opened":
            users.touch_active(conn, user_id, now)
    return {"ok": True}
