from __future__ import annotations

from datetime import datetime

from .analytics import track
from .timeutil import iso


def create_goal(conn, goal_id: str, user_id: str, name: str, target_cents: int, now: datetime) -> None:
    conn.execute(
        "INSERT INTO goals (id, user_id, name, target_cents, created_at) VALUES (?, ?, ?, ?, ?)",
        (goal_id, user_id, name, target_cents, iso(now)),
    )
    conn.commit()
    track(conn, user_id, "goal_created", now, {"goal_id": goal_id, "target_cents": target_cents})


def active_goals(conn, user_id: str) -> list:
    return conn.execute(
        "SELECT * FROM goals WHERE user_id = ? AND status = 'active' ORDER BY created_at, id", (user_id,)
    ).fetchall()


def record_saving(conn, goal_id: str, delta_cents: int) -> None:
    conn.execute("UPDATE goals SET saved_cents = saved_cents + ? WHERE id = ?", (delta_cents, goal_id))
    conn.execute(
        "UPDATE goals SET status = 'achieved' WHERE id = ? AND target_cents > 0 AND saved_cents >= target_cents",
        (goal_id,),
    )
    conn.commit()


def progress_pct(goal) -> int:
    """Percent of target saved, capped at 100. A goal with no target shows 0."""
    if goal["target_cents"] <= 0:
        return 0
    return min(100, goal["saved_cents"] * 100 // goal["target_cents"])
