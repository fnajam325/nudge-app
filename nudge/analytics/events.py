"""The event vocabulary. Adding an event means adding it here first.

Server-side events are emitted by this repo. Client events (app_opened, session_ended,
nudge_opened, nudge_acted_on) arrive through nudge/api/handlers.py.
"""

EVENT_NAMES = frozenset(
    {
        # Server-side
        "account_linked",
        "goal_created",
        "feed_viewed",  # properties: card_count
        "nudge_sent",  # properties: nudge_id, nudge_type
        "experiment_assigned",  # properties: experiment, variant
        # Client
        "app_opened",
        "session_ended",  # properties: screen, duration_seconds
        "nudge_opened",  # properties: nudge_id
        "nudge_acted_on",  # properties: nudge_id
    }
)

CLIENT_EVENTS = frozenset({"app_opened", "session_ended", "nudge_opened", "nudge_acted_on"})
