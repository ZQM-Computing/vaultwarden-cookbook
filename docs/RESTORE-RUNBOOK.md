# Vaultwarden application-aware recovery runbook

## Purpose and evidence boundary

Use this as a planning and execution checklist for a **separately authorized, isolated recovery exercise**. It supplements the synthetic file-level drill in [04-backup-restore](../examples/04-backup-restore/README.md); it does not turn that drill into a Vaultwarden integration test.

This runbook is deliberately not a copy-and-paste production restore script. Paths, deployment method, database mode, environment variables, reverse proxy, and key material differ between installations. Record the actual deployment-specific values in a protected operations system, not in this public repository.

**Never restore over a live Vaultwarden data directory. Never place real vault contents, exports, tokens, passwords, or private keys in this repository or CI artifacts.**

## 1. Define the recovery target before starting

Record in the incident/change ticket:

- Incident owner, approver, recovery operator, and communication channel.
- Target environment and isolated hostname/network; confirm production clients cannot reach it.
- Vaultwarden version and deployment method used by the source and intended recovery target.
- Required recovery point (backup timestamp) and recovery-time objective.
- Exact data directory and any external volumes or mounts used by the deployment.
- Protected inventory of deployment configuration, environment variables, reverse-proxy settings, and required cryptographic/key material.
- Backup location, retention status, access controls, and independent integrity evidence.

If the source layout or required files are unknown, stop and inventory the installation before proceeding. Do not assume that a database file alone is a complete backup.

## 2. Create an application-consistent backup

1. Confirm the backup target has adequate space and is access-controlled and encrypted according to the operating policy.
2. Quiesce writes using the deployment's documented maintenance procedure. The conservative option is to stop the Vaultwarden application cleanly before copying its data directory. If the deployment uses a supported online SQLite backup method, follow that method's documentation and capture its output and exit status.
3. Capture the **complete configured persistent data set**, not just `db.sqlite3`. Depending on the installation this can include attachments, sends, generated key files, icon cache, and other persistent state. Confirm each path against the actual deployment.
4. Capture deployment configuration and required environment/secret references separately in the approved secret-management system. Do not print secret values in logs or place them beside a public artifact.
5. Record source version, backup timestamp, file inventory, sizes, and cryptographic checksums. Store integrity metadata independently from the backup where feasible; a checksum manifest beside the data alone cannot detect an attacker replacing both.
6. Verify the backup is readable and that all expected files are present. Record any exclusions and their rationale.
7. Restart the source only after the backup operation is complete and the source's normal health checks pass.

Do not delete or rotate the source data as part of this exercise.

## 3. Restore to an isolated target

1. Provision a disposable host or isolated network with no route from public users or production clients. Restrict outbound connectivity unless required for the test.
2. Install a compatible, explicitly recorded Vaultwarden version. Do not automatically upgrade during recovery; first prove recovery on the intended compatible version.
3. Restore the backed-up persistent data to a **new, empty** target directory. Verify checksums before application startup, then set ownership and permissions to the identity expected by the service.
4. Reapply configuration through the approved secret-management process. Never copy secrets into shell history, tickets, CI logs, or public artifacts.
5. Keep the service bound to loopback or the isolated test network. Do not attach the production reverse proxy, DNS, SMTP delivery, push services, or production identity dependencies unless the test plan specifically requires them and their side effects are controlled.
6. Start the service and capture startup logs with secrets and user data redacted. If database migration, missing-file, permission, or compatibility errors appear, stop and investigate; do not experiment on the only backup copy.

## 4. Validate recovery with a dedicated test account

Use only a synthetic test account and synthetic vault items created for the exercise.

- Confirm the service starts and remains healthy.
- Confirm the expected login flow works for the synthetic account.
- Confirm a known synthetic item can be read after login.
- If attachments are in scope, retrieve a known synthetic attachment and compare its content/hash.
- Check for missing data, migration errors, permission errors, and unexpected outbound requests.
- Confirm the recovered version, data paths, and configuration match the approved test plan.
- Verify public access and production clients cannot reach the isolated instance.
- Record observed recovery time and recovered backup timestamp; calculate actual RTO/RPO only from recorded evidence.
- Preserve redacted logs and test results without exporting real vault data.

A successful process start or a valid checksum is not, by itself, proof that users' vaults and attachments are usable.

## 5. Close out and clean up

1. Have the recovery owner review the evidence and record pass/fail for each criterion.
2. If any critical validation fails, mark the recovery unsuccessful; retain the source and backup, then investigate in a fresh isolated target.
3. Securely destroy the disposable target and temporary copies according to the organization's data-handling policy after evidence is retained.
4. Confirm temporary credentials, access grants, DNS entries, firewall rules, and test resources have been removed.
5. Update the deployment-specific runbook with exact versions, verified paths, actual commands, evidence links, and known limitations. Do not record secrets.
6. Schedule a repeat exercise at a defined cadence and after material changes to the application, database, storage, or deployment.

## Evidence checklist

| Evidence | Required record |
|---|---|
| Backup provenance | Source version, timestamp, operator, and storage location reference |
| Completeness | Data/config inventory and documented exclusions |
| Integrity | Checksum results and location of independently protected manifest |
| Isolation | Target identity, network restrictions, and proof production clients cannot reach it |
| Compatibility | Vaultwarden version and any migration behavior observed |
| Application validation | Synthetic login, item read, and attachment test results where applicable |
| Objectives | Measured recovery duration and recovered backup timestamp |
| Cleanup | Temporary target and access removal confirmation |
| Limitations | Failed checks, untested dependencies, and follow-up actions |

## What this repository currently tests

The automated example uses generated fixture files and standard-library tests to verify file checksums, isolated copying, refusal to overwrite existing destinations, and source preservation. It does **not** execute this runbook, open a real SQLite database, start Vaultwarden, validate a login, test encryption or off-host retention, or demonstrate a production recovery. Treat the table above as a manual operational checklist until a separately isolated application-level integration harness exists.
