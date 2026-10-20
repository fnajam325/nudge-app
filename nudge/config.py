"""Runtime configuration. Production overrides come from environment variables."""
import os

DB_PATH = os.environ.get("NUDGE_DB_PATH", "nudge.db")

# --- Transaction sync (docs/adr/0002-nightly-transaction-sync.md)
SYNC_STALE_AFTER_HOURS = 36

# --- Notifications (docs/adr/0003-global-push-frequency-cap.md)
NUDGE_SEND_HOUR_UTC = 15  # 10am US Eastern, 7am US Pacific
MAX_PUSH_PER_7_DAYS = 2
# Highest priority first. A user gets at most one nudge per scheduler run.
NUDGE_PRIORITY = [
    "spending_alert",
    "milestone",
    "goal_reminder",
    "re_engagement",
    "weekly_tip",
]
RE_ENGAGEMENT_INACTIVE_DAYS = 3
SPENDING_ALERT_MIN_CENTS = 15000
SPENDING_ALERT_RATIO = 1.5
MILESTONE_THRESHOLDS = (25, 50, 75, 100)

# --- Home feed (docs/adr/0001-server-driven-home-feed.md)
HOME_FEED_ORDER = ["balance", "recent_transactions", "spending_by_category", "goals"]
RECENT_TRANSACTIONS_LIMIT = 5
SPENDING_WINDOW_DAYS = 30
