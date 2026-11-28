from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.backup_sqlite import backup_sqlite


class SQLiteBackupTests(unittest.TestCase):
    def test_backup_uses_online_backup_and_preserves_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.db"
            target = root / "backups" / "backup.db"
            conn = sqlite3.connect(source)
            conn.execute("CREATE TABLE sample(value TEXT NOT NULL)")
            conn.execute("INSERT INTO sample(value) VALUES('soulsbo')")
            conn.commit()
            conn.close()
            result = backup_sqlite(source, target)
            self.assertEqual(result["status"], "ok")
            copy = sqlite3.connect(target)
            self.assertEqual(copy.execute("SELECT value FROM sample").fetchone()[0], "soulsbo")
            self.assertEqual(copy.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            copy.close()

    def test_backup_supports_source_paths_with_spaces_and_uri_characters(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "database # community.db"
            target = root / "backup folder" / "backup.db"
            conn = sqlite3.connect(source)
            conn.execute("CREATE TABLE sample(value TEXT NOT NULL)")
            conn.execute("INSERT INTO sample(value) VALUES('preserved')")
            conn.commit()
            conn.close()
            result = backup_sqlite(source, target)
            self.assertEqual(result["integrity"], "ok")
            copy = sqlite3.connect(target)
            self.assertEqual(copy.execute("SELECT value FROM sample").fetchone()[0], "preserved")
            copy.close()

    def test_backup_rejects_same_path_and_missing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.db"
            with self.assertRaises(ValueError):
                backup_sqlite(path, path)
            with self.assertRaises(FileNotFoundError):
                backup_sqlite(path, Path(directory) / "backup.db")


if __name__ == "__main__":
    unittest.main()
