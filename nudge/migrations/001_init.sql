-- Core tables: users, linked accounts, transactions.

CREATE TABLE users (
    id                  TEXT PRIMARY KEY,
    created_at          TEXT NOT NULL,
    timezone            TEXT NOT NULL DEFAULT 'America/New_York',
    platform            TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
    acquisition_channel TEXT NOT NULL DEFAULT 'organic',
    push_opt_in         INTEGER NOT NULL DEFAULT 1,
    last_active_at      TEXT
);

CREATE TABLE accounts (
    id             TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL REFERENCES users (id),
    type           TEXT NOT NULL CHECK (type IN ('checking', 'savings', 'credit_card')),
    institution    TEXT NOT NULL,
    balance_cents  INTEGER NOT NULL DEFAULT 0,
    linked_at      TEXT NOT NULL,
    last_synced_at TEXT,
    goal_name      TEXT
);
CREATE INDEX idx_accounts_user ON accounts (user_id);

CREATE TABLE transactions (
    id           TEXT PRIMARY KEY,
    account_id   TEXT NOT NULL REFERENCES accounts (id),
    user_id      TEXT NOT NULL REFERENCES users (id),
    posted_at    TEXT NOT NULL,
    amount_cents INTEGER NOT NULL, -- negative means money out
    merchant     TEXT NOT NULL,
    category     TEXT
);
CREATE INDEX idx_transactions_user_posted ON transactions (user_id, posted_at);
