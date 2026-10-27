#!/usr/bin/env python3
"""Synthetic backup/restore drill; never opens or modifies a real vault."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

MANIFEST = "sha256.manifest"
FIXTURE_ITEM = ("item-001", "Synthetic item for recovery test")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_fixture(source: Path) -> None:
    source.mkdir(parents=True, exist_ok=False)
    database = source / "db.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE synthetic_items (id TEXT PRIMARY KEY, name TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO synthetic_items (id, name) VALUES (?, ?)", FIXTURE_ITEM
        )
        connection.commit()
    (source / "attachments").mkdir()
    (source / "attachments" / "fixture.txt").write_text(
        "synthetic attachment; no secrets\n", encoding="utf-8"
    )


def verify_synthetic_database(database: Path) -> None:
    """Check SQLite structural integrity and the expected synthetic record."""
    if not database.is_file():
        raise SystemExit(f"synthetic SQLite database missing: {database}")
    try:
        with sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()
            if result != ("ok",):
                raise SystemExit(f"SQLite integrity check failed: {result!r}")
            item = connection.execute(
                "SELECT id, name FROM synthetic_items WHERE id = ?", (FIXTURE_ITEM[0],)
            ).fetchone()
            if item != FIXTURE_ITEM:
                raise SystemExit(f"synthetic database record mismatch: {item!r}")
    except sqlite3.DatabaseError as exc:
        raise SystemExit(f"invalid synthetic SQLite database: {exc}") from exc


def create_backup(source: Path, backup: Path) -> None:
    if not source.is_dir():
        raise SystemExit(f"source directory does not exist: {source}")
    if backup.exists():
        raise SystemExit(f"refusing to overwrite existing backup: {backup}")
    if not (source / "db.sqlite3").is_file() or not (source / "attachments").is_dir():
        raise SystemExit("source must contain db.sqlite3 and attachments/")
    backup.mkdir(parents=True)
    shutil.copy2(source / "db.sqlite3", backup / "db.sqlite3")
    shutil.copytree(source / "attachments", backup / "attachments")
    entries = []
    for path in sorted(p for p in backup.rglob("*") if p.is_file()):
        entries.append(f"{sha256(path)}  {path.relative_to(backup).as_posix()}")
    (backup / MANIFEST).write_text("\n".join(entries) + "\n", encoding="utf-8")


def verify_backup(backup: Path) -> None:
    manifest = backup / MANIFEST
    if not manifest.is_file():
        raise SystemExit("backup manifest missing")
    seen = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        try:
            expected, relative = line.split("  ", 1)
        except ValueError as exc:
            raise SystemExit(f"malformed manifest line: {line!r}") from exc
        path = (backup / relative).resolve()
        if backup.resolve() not in path.parents or not path.is_file():
            raise SystemExit(f"unsafe or missing manifest path: {relative}")
        if relative in seen:
            raise SystemExit(f"duplicate manifest path: {relative}")
        seen.add(relative)
        observed = sha256(path)
        if observed != expected:
            raise SystemExit(f"checksum mismatch: {relative}")
    actual = {
        p.relative_to(backup).as_posix()
        for p in backup.rglob("*")
        if p.is_file() and p.name != MANIFEST
    }
    if seen != actual:
        raise SystemExit(
            f"manifest inventory mismatch; unlisted={sorted(actual - seen)}, "
            f"missing={sorted(seen - actual)}"
        )
    verify_synthetic_database(backup / "db.sqlite3")
    print(f"Verified {len(seen)} files and SQLite integrity")


def restore_isolated(backup: Path, destination: Path) -> None:
    verify_backup(backup)
    if destination.exists():
        raise SystemExit(f"refusing to overwrite restore destination: {destination}")
    shutil.copytree(backup, destination, ignore=shutil.ignore_patterns(MANIFEST))
    for path in sorted(p for p in destination.rglob("*") if p.is_file()):
        relative = path.relative_to(destination)
        if sha256(path) != sha256(backup / relative):
            raise SystemExit(f"restored checksum mismatch: {relative}")
    verify_synthetic_database(destination / "db.sqlite3")
    print(f"Restored {sum(1 for p in destination.rglob('*') if p.is_file())} files to isolated destination")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", type=Path, help="existing empty parent directory; default uses a temporary directory")
    args = parser.parse_args()
    if args.workdir:
        root = args.workdir.resolve()
        root.mkdir(parents=True, exist_ok=True)
        if any(root.iterdir()):
            raise SystemExit("--workdir must be empty; refusing to touch existing files")
        with tempfile.TemporaryDirectory(prefix="zqm-vaultwarden-drill-", dir=root) as temp:
            run(Path(temp))
    else:
        with tempfile.TemporaryDirectory(prefix="zqm-vaultwarden-drill-") as temp:
            run(Path(temp))


def run(root: Path) -> None:
    source = root / "synthetic-source"
    backup = root / "backup"
    restored = root / "restored-isolated"
    write_fixture(source)
    verify_synthetic_database(source / "db.sqlite3")
    before = {p.relative_to(source).as_posix(): sha256(p) for p in source.rglob("*") if p.is_file()}
    create_backup(source, backup)
    verify_backup(backup)
    restore_isolated(backup, restored)
    after = {p.relative_to(source).as_posix(): sha256(p) for p in source.rglob("*") if p.is_file()}
    if before != after:
        raise SystemExit("source-preservation check failed")
    with sqlite3.connect(f"file:{(restored / 'db.sqlite3').resolve().as_posix()}?mode=ro", uri=True) as connection:
        restored_item = connection.execute(
            "SELECT id, name FROM synthetic_items WHERE id = ?", (FIXTURE_ITEM[0],)
        ).fetchone()
    if restored_item != FIXTURE_ITEM:
        raise SystemExit("synthetic database record differs after restore")
    if (restored / "attachments" / "fixture.txt").read_text(encoding="utf-8") != "synthetic attachment; no secrets\n":
        raise SystemExit("synthetic attachment content differs after restore")
    print("PASS: checksums valid; SQLite integrity valid; synthetic record and attachment restored; source unchanged")


if __name__ == "__main__":
    main()
