-- One row per push notification we attempt to send.

CREATE TABLE nudges (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users (id),
    nudge_type  TEXT NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('sent', 'failed')),
    payload     TEXT NOT NULL DEFAULT '{}',
    sent_at     TEXT NOT NULL,
    opened_at   TEXT,
    acted_on_at TEXT
);
CREATE INDEX idx_nudges_user_sent ON nudges (user_id, sent_at);
CREATE INDEX idx_nudges_type_sent ON nudges (nudge_type, sent_at);
