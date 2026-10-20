import sqlite3
import unittest

from nudge import db
from tests.helpers import make_conn


class MigrationTests(unittest.TestCase):
    def test_migrations_apply_once(self):
        conn = db.connect(":memory:")
        first = db.migrate(conn)
        self.assertEqual(first[0], "001_init.sql")
        self.assertEqual(len(first), 5)
        self.assertEqual(db.migrate(conn), [])

    def test_goal_backfill_copies_legacy_goal_names(self):
        conn = db.connect(":memory:")
        conn.executescript((db.MIGRATIONS_DIR / "001_init.sql").read_text())
        conn.execute("INSERT INTO users (id, created_at, platform) VALUES ('u1', '2025-01-01T00:00:00Z', 'ios')")
        conn.execute(
            "INSERT INTO accounts (id, user_id, type, institution, linked_at, goal_name) "
            "VALUES ('a1', 'u1', 'savings', 'Bank', '2025-01-02T00:00:00Z', 'rainy day')"
        )
        conn.commit()
        conn.executescript((db.MIGRATIONS_DIR / "004_goals.sql").read_text())
        row = conn.execute("SELECT name FROM goals WHERE user_id = 'u1'").fetchone()
        self.assertEqual(row["name"], "rainy day")

    def test_foreign_keys_are_enforced(self):
        conn = make_conn()
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO accounts (id, user_id, type, institution, linked_at) "
                "VALUES ('a1', 'missing', 'checking', 'Bank', '2026-01-01T00:00:00Z')"
            )


if __name__ == "__main__":
    unittest.main()
