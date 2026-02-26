import sqlite3
import unittest
from pathlib import Path

from countersignal.core.db import get_connection, init_db


class TestDBInit(unittest.TestCase):
    def setUp(self):
        self.db_path = Path("test_init.db")
        if self.db_path.exists():
            self.db_path.unlink()

    def tearDown(self):
        if self.db_path.exists():
            self.db_path.unlink()

    def test_fresh_init(self):
        # Initial call
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            # Check version
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            self.assertEqual(version, 4)

            # Check tables
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            self.assertIn("campaigns", tables)
            self.assertIn("hits", tables)

            # Check columns in campaigns
            columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(campaigns)").fetchall()
            }
            self.assertIn("payload_style", columns)
            self.assertIn("format", columns)
            self.assertIn("payload_type", columns)

    def test_migration_from_old_schema(self):
        # Create an "old" database without the migration columns
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE campaigns (
                uuid TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                technique TEXT NOT NULL,
                callback_url TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.close()

        # Run init_db
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            # Check version
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            self.assertEqual(version, 4)

            # Check columns in campaigns (should have been added)
            columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(campaigns)").fetchall()
            }
            self.assertIn("payload_style", columns)
            self.assertIn("format", columns)
            self.assertIn("payload_type", columns)

            # Check hits table (should have been created)
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            self.assertIn("hits", tables)

    def test_repeated_init(self):
        init_db(self.db_path)

        # Measure time or just ensure it doesn't crash/error
        init_db(self.db_path)
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            self.assertEqual(version, 4)


if __name__ == "__main__":
    unittest.main()
