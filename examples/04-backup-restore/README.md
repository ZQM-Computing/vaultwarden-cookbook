# Synthetic backup and restore drill

This exercise validates basic file-level backup integrity and isolated restore
behavior using generated fixture files. It does **not** connect to Vaultwarden,
read a real SQLite database, encrypt a backup, or prove application consistency.
No real credentials, vault exports, attachments, or production data are used.

## Requirements

- Python 3.11 or newer
- No third-party Python dependencies

## Run the drill

From this directory:

```sh
python backup_restore.py
python -m unittest -v test_backup_restore.py
```

The script creates a temporary synthetic source, copies the fixture database
and attachment into a backup, writes a SHA-256 manifest, verifies the backup,
restores to a new isolated directory, and checks that the source fixture did
not change. It refuses to overwrite an existing backup or restore destination.
Checksum validation detects accidental corruption; it does not authenticate a
manifest against a malicious replacement.

## What a real Vaultwarden recovery plan still needs

Before treating a backup process as operational, separately design and test:

1. A quiesced or application-consistent SQLite backup procedure.
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
file-copy integrity drill, not a production backup certification.
