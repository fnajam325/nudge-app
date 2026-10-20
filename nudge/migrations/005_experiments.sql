-- Sticky experiment assignments. One row per user per experiment.

CREATE TABLE experiment_assignments (
    experiment_key TEXT NOT NULL,
    user_id        TEXT NOT NULL REFERENCES users (id),
    variant        TEXT NOT NULL,
    assigned_at    TEXT NOT NULL,
    PRIMARY KEY (experiment_key, user_id)
);
