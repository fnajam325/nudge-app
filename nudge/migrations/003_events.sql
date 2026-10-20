-- Product analytics events. Names are validated in nudge/analytics/events.py.

CREATE TABLE events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL,
    name        TEXT NOT NULL,
    properties  TEXT NOT NULL DEFAULT '{}',
    occurred_at TEXT NOT NULL
);
CREATE INDEX idx_events_user_time ON events (user_id, occurred_at);
CREATE INDEX idx_events_name_time ON events (name, occurred_at);
