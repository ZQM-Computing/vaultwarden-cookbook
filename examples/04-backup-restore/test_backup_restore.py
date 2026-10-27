"""Regression tests for the synthetic backup/restore drill."""
import tempfile
import unittest
from pathlib import Path

import backup_restore


class BackupRestoreTests(unittest.TestCase):
    def test_round_trip_preserves_source_and_restores_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            backup = root / "backup"
            restored = root / "restored"
            backup_restore.write_fixture(source)
            before = {p.relative_to(source).as_posix(): backup_restore.sha256(p)
                      for p in source.rglob("*") if p.is_file()}
            backup_restore.create_backup(source, backup)
            backup_restore.verify_backup(backup)
            backup_restore.restore_isolated(backup, restored)
            after = {p.relative_to(source).as_posix(): backup_restore.sha256(p)
                     for p in source.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            self.assertEqual((source / "db.sqlite3").read_bytes(),
                             (restored / "db.sqlite3").read_bytes())
            self.assertTrue((restored / "attachments" / "fixture.txt").is_file())

    def test_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, backup = root / "source", root / "backup"
            backup_restore.write_fixture(source)
            backup_restore.create_backup(source, backup)
            (backup / "db.sqlite3").write_bytes(b"tampered\n")
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
