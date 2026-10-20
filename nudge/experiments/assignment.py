"""Deterministic, sticky experiment assignment."""
from __future__ import annotations

import hashlib
from datetime import datetime

from ..analytics import track
from ..timeutil import iso
from .registry import EXPERIMENTS


def bucket(user_id: str, salt: str) -> int:
    """Stable number from 0 to 99 for a user and a salt."""
    digest = hashlib.sha256(f"{salt}:{user_id}".encode()).hexdigest()
    return int(digest[:8], 16) % 100


def get_variant(conn, user_id: str, experiment_key: str, now: datetime) -> str | None:
    """Return the user's variant, assigning one on first call. None means not enrolled."""
    existing = conn.execute(
        "SELECT variant FROM experiment_assignments WHERE experiment_key = ? AND user_id = ?",
        (experiment_key, user_id),
    ).fetchone()
    if existing:
        return existing["variant"]  # sticky, even after the experiment concludes

    exp = EXPERIMENTS[experiment_key]
    if exp.status != "running":
        return None
    if exp.new_users_only:
        created = conn.execute("SELECT created_at FROM users WHERE id = ?", (user_id,)).fetchone()["created_at"]
        if created < exp.started_at:
            return None
    if bucket(user_id, exp.key) >= exp.traffic_pct:
        return None

    variant = exp.variants[bucket(user_id, f"{exp.key}:variant") % len(exp.variants)]
    conn.execute(
        "INSERT INTO experiment_assignments (experiment_key, user_id, variant, assigned_at) VALUES (?, ?, ?, ?)",
        (experiment_key, user_id, variant, iso(now)),
    )
    conn.commit()
    track(conn, user_id, "experiment_assigned", now, {"experiment": experiment_key, "variant": variant})
    return variant
