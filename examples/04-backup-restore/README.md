# Synthetic backup and restore drill

This exercise validates file-level backup integrity and isolated restore behavior
using generated fixture files, including a **real SQLite database created for
this test**. It checks SQLite's `PRAGMA integrity_check`, verifies a known
synthetic row can be queried after restore, checks attachment content, detects
file tampering, validates manifest inventory, refuses overwrite, and confirms
the source fixture remains unchanged.

It does **not** connect to Vaultwarden, use the Vaultwarden schema, prove
application consistency, or establish production recovery. No real credentials,
vault exports, attachments, or production data are used.

## Requirements

- Python 3.11 or newer
- No third-party Python dependencies (uses Python's standard-library `sqlite3`)

## Run the drill

From this directory:

```sh
python backup_restore.py
python -m unittest -v test_backup_restore.py
```

The script creates a temporary synthetic source with a small SQLite database
and text attachment, writes a SHA-256 manifest, verifies the backup, restores
to a new isolated directory, checks SQLite structural integrity and the known
test record, validates attachment content, and confirms that the source did not
change. It refuses to overwrite an existing backup or restore destination.

Checksum validation detects accidental corruption; it does not authenticate a
manifest against a malicious replacement. The synthetic SQLite database is
not a copy of Vaultwarden's database schema and is not evidence that a real
Vaultwarden database can be restored.

## What a real Vaultwarden recovery plan still needs

Before treating a backup process as operational, separately design and test:

1. A quiesced or application-consistent SQLite backup procedure for the actual
   Vaultwarden deployment.
2. Required attachments and any other configured data paths.
3. File ownership, permissions, encryption at rest, and protected off-host copies.
4. A manifest protected independently from the backup contents.
5. A restore into an isolated host/network with no production clients attached.
6. Version compatibility, application startup, login using a dedicated synthetic
   account, and attachment retrieval.
7. Recovery-time and recovery-point objectives, retention, monitoring, and a
   documented rollback/destroy procedure.

Never test restoration over a live data directory. Keep admin tokens and
encryption keys out of source control and logs. This cookbook example is a
synthetic SQLite-and-file integrity drill, not a production backup certification.
