#!/usr/bin/env python3
"""Synthetic backup/restore drill; never opens or modifies a real vault."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

SYNTHETIC_DB = b'{"format":"zqm-synthetic-fixture-v1","items":[{"id":"item-001","name":"synthetic-only"}]}\n'
MANIFEST = "sha256.manifest"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_fixture(source: Path) -> None:
    source.mkdir(parents=True, exist_ok=False)
    (source / "db.sqlite3").write_bytes(SYNTHETIC_DB)
    (source / "attachments").mkdir()
    (source / "attachments" / "fixture.txt").write_text(
        "synthetic attachment; no secrets\n", encoding="utf-8"
    )


def create_backup(source: Path, backup: Path) -> None:
    if not source.is_dir():
        raise SystemExit(f"source directory does not exist: {source}")
    if backup.exists():
        raise SystemExit(f"refusing to overwrite existing backup: {backup}")
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
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = (backup / relative).resolve()
        if backup.resolve() not in path.parents or not path.is_file():
            raise SystemExit(f"unsafe or missing manifest path: {relative}")
        observed = sha256(path)
        if observed != expected:
            raise SystemExit(f"checksum mismatch: {relative}")
    print(f"Verified {len(manifest.read_text(encoding='utf-8').splitlines())} files")


def restore_isolated(backup: Path, destination: Path) -> None:
    verify_backup(backup)
    if destination.exists():
        raise SystemExit(f"refusing to overwrite restore destination: {destination}")
    shutil.copytree(backup, destination, ignore=shutil.ignore_patterns(MANIFEST))
    # A restore is accepted only when all restored file hashes match the backup.
    for path in sorted(p for p in destination.rglob("*") if p.is_file()):
        relative = path.relative_to(destination)
        if sha256(path) != sha256(backup / relative):
            raise SystemExit(f"restored checksum mismatch: {relative}")
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
    before = {p.relative_to(source).as_posix(): sha256(p) for p in source.rglob("*") if p.is_file()}
    create_backup(source, backup)
    verify_backup(backup)
    restore_isolated(backup, restored)
    after = {p.relative_to(source).as_posix(): sha256(p) for p in source.rglob("*") if p.is_file()}
    if before != after:
        raise SystemExit("source-preservation check failed")
    if (restored / "db.sqlite3").read_bytes() != SYNTHETIC_DB:
        raise SystemExit("synthetic database fixture differs after restore")
    print("PASS: checksums valid; restore isolated; source unchanged; synthetic fixture matches")


if __name__ == "__main__":
    main()
