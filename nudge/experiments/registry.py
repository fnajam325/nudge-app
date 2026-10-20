"""Experiment definitions. One entry per experiment, edited by hand."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Experiment:
    key: str
    variants: tuple[str, ...]
    traffic_pct: int  # share of eligible users enrolled, 0 to 100
    started_at: str
    new_users_only: bool = False
    status: str = "running"  # running | concluded


EXPERIMENTS = {
    "onboarding_checklist_v2": Experiment(
        key="onboarding_checklist_v2",
        variants=("control", "checklist"),
        traffic_pct=50,
        started_at="2025-09-01T00:00:00Z",
        new_users_only=True,
        status="concluded",
    ),
    "weekly_tip_copy": Experiment(
        key="weekly_tip_copy",
        variants=("control", "short"),
        traffic_pct=100,
        started_at="2025-11-10T00:00:00Z",
    ),
}
