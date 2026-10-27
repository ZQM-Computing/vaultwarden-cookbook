"""Regression tests for the synthetic backup/restore drill."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

import backup_restore


class BackupRestoreTests(unittest.TestCase):
    def test_round_trip_preserves_source_and_restores_sqlite_and_attachment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            backup = root / "backup"
            restored = root / "restored"
            backup_restore.write_fixture(source)
            before = {
                p.relative_to(source).as_posix(): backup_restore.sha256(p)
                for p in source.rglob("*") if p.is_file()
            }
            backup_restore.create_backup(source, backup)
            backup_restore.verify_backup(backup)
            backup_restore.restore_isolated(backup, restored)
            after = {
                p.relative_to(source).as_posix(): backup_restore.sha256(p)
                for p in source.rglob("*") if p.is_file()
            }
            self.assertEqual(before, after)
            backup_restore.verify_synthetic_database(restored / "db.sqlite3")
            with sqlite3.connect(restored / "db.sqlite3") as connection:
                self.assertEqual(
                    connection.execute(
                        "SELECT id, name FROM synthetic_items WHERE id = ?",
                        (backup_restore.FIXTURE_ITEM[0],),
                    ).fetchone(),
                    backup_restore.FIXTURE_ITEM,
                )
            self.assertEqual(
                (restored / "attachments" / "fixture.txt").read_text(encoding="utf-8"),
                "synthetic attachment; no secrets\n",
            )

    def test_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, backup = root / "source", root / "backup"
            backup_restore.write_fixture(source)
            backup_restore.create_backup(source, backup)
            (backup / "db.sqlite3").write_bytes(b"tampered\n")
            with self.assertRaises(SystemExit):
                backup_restore.verify_backup(backup)

    def test_rejects_invalid_sqlite_even_if_manifest_matches(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, backup = root / "source", root / "backup"
            backup_restore.write_fixture(source)
            backup_restore.create_backup(source, backup)
            (backup / "db.sqlite3").write_bytes(b"not a SQLite database")
            entries = []
            for path in sorted(p for p in backup.rglob("*") if p.is_file() and p.name != backup_restore.MANIFEST):
                entries.append(f"{backup_restore.sha256(path)}  {path.relative_to(backup).as_posix()}")
            (backup / backup_restore.MANIFEST).write_text("\n".join(entries) + "\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                backup_restore.verify_backup(backup)

    def test_refuses_existing_backup_and_restore_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, backup, restored = root / "source", root / "backup", root / "restored"
            backup_restore.write_fixture(source)
            backup_restore.create_backup(source, backup)
            with self.assertRaises(SystemExit):
                backup_restore.create_backup(source, backup)
            restored.mkdir()
            with self.assertRaises(SystemExit):
                backup_restore.restore_isolated(backup, restored)


if __name__ == "__main__":
    unittest.main()
