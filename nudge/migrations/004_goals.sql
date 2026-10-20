-- Goals move out of accounts.goal_name into their own table (docs/adr/0004-goals-table.md).
-- accounts.goal_name stays in place until the backfill is verified.

CREATE TABLE goals (
    id           TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL REFERENCES users (id),
    name         TEXT NOT NULL,
    target_cents INTEGER NOT NULL DEFAULT 0,
    saved_cents  INTEGER NOT NULL DEFAULT 0,
    status       TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'achieved', 'archived')),
    created_at   TEXT NOT NULL
);
CREATE INDEX idx_goals_user ON goals (user_id);

INSERT INTO goals (id, user_id, name, created_at)
SELECT 'g_' || id, user_id, goal_name, linked_at
FROM accounts
WHERE goal_name IS NOT NULL;
