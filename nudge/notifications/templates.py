"""Push copy. Each template renders to (title, body, deep_link)."""
from __future__ import annotations

DEFAULTS = {"goal_name": "savings goal", "category": "spending", "threshold": 25, "variant": "control"}

TEMPLATES = {
    "goal_reminder": ("Keep your savings on track", "Keep going on your {goal_name}. Small deposits add up.", "nudge://goals"),
    "milestone": ("Milestone reached", "You are {threshold}% of the way to your {goal_name}.", "nudge://goals"),
    "re_engagement": ("Your money misses you", "Take a minute to see where things stand this week.", "nudge://home"),
    "spending_alert": ("Heads up on {category}", "Your {category} spending is up this week.", "nudge://spending"),
}

WEEKLY_TIP_BODIES = {
    "control": "Round up your purchases and move the change into savings. It adds up faster than you think.",
    "short": "Round up purchases into savings.",
}


def render(nudge_type: str, context: dict) -> tuple[str, str, str]:
    values = {**DEFAULTS, **context}
    if nudge_type == "weekly_tip":
        body = WEEKLY_TIP_BODIES.get(values["variant"], WEEKLY_TIP_BODIES["control"])
        return "A tip for this week", body, "nudge://home"
    title, body, link = TEMPLATES[nudge_type]
    return title.format(**values), body.format(**values), link
