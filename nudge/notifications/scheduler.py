"""The notification run. Cron calls run() every hour (see nudge/jobs.py)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime

from .. import config, users
from ..analytics import track
from ..experiments import get_variant
from ..timeutil import iso
from . import frequency, selector, templates
from .sender import PushError, PushProvider


def run(conn, now: datetime, push: PushProvider) -> list[dict]:
    """Send due nudges. Returns one dict per push sent. Does nothing outside the send hour."""
    if now.hour != config.NUDGE_SEND_HOUR_UTC:
        return []
    sent_to: set[str] = set()
    results = []
    for nudge_type in config.NUDGE_PRIORITY:
        for candidate in selector.select(conn, nudge_type, now):
            if candidate.user_id in sent_to:
                continue  # one nudge per user per run
            user = users.get_user(conn, candidate.user_id)
            if not frequency.can_send(conn, user, now):
                continue
            context = dict(candidate.context)
            if nudge_type == "weekly_tip":
                context["variant"] = get_variant(conn, user["id"], "weekly_tip_copy", now) or "control"
            title, body, link = templates.render(nudge_type, context)
            nudge_id = uuid.uuid4().hex[:12]
            try:
                push.send(user, title, body, link)
                status = "sent"
            except PushError:
                status = "failed"
            conn.execute(
                "INSERT INTO nudges (id, user_id, nudge_type, status, payload, sent_at) VALUES (?, ?, ?, ?, ?, ?)",
                (nudge_id, user["id"], nudge_type, status, json.dumps(candidate.context, sort_keys=True), iso(now)),
            )
            conn.commit()
            if status == "sent":
                track(conn, user["id"], "nudge_sent", now, {"nudge_id": nudge_id, "nudge_type": nudge_type})
                sent_to.add(user["id"])
                results.append({"nudge_id": nudge_id, "user_id": user["id"], "nudge_type": nudge_type})
    return results
