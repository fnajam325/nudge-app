from __future__ import annotations

import json
from datetime import datetime

from ..timeutil import iso
from .events import EVENT_NAMES


def track(conn, user_id: str, name: str, now: datetime, properties: dict | None = None) -> None:
    if name not in EVENT_NAMES:
        raise ValueError(f"unknown event: {name}")
    conn.execute(
        "INSERT INTO events (user_id, name, properties, occurred_at) VALUES (?, ?, ?, ?)",
        (user_id, name, json.dumps(properties or {}, sort_keys=True), iso(now)),
    )
    conn.commit()
