# Vaultwarden Cookbook

<!-- ZQM-START -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <strong>ZQM Computing — Geospatial Engineering & Scientific Computing</strong><br>
  <a href="https://github.com/ZQM-Computing">ZQM Computing</a>
</p>
<!-- markdownlint-enable MD033 -->
<!-- ZQM-END -->

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A **Vaultwarden cookbook** for self-hosted password-vault operations. This repository includes a synthetic SQLite-and-file backup/restore drill. It does not connect to a Vaultwarden instance or certify production recovery.

## Repository role and status

**Status:** Active, public — synthetic backup/restore exercise and application-aware recovery runbook.

**Audience:** Engineers documenting safe backup and recovery boundaries for self-hosted credential services.

**Portfolio:** Part of the ZQM Computing cookbook collection, indexed by [geospatial-cookbooks](https://github.com/ZQM-Computing/geospatial-cookbooks).

## Example

| Path | Purpose | Evidence level |
|---|---|---|
| [04-backup-restore](examples/04-backup-restore/) | Generates a valid synthetic SQLite database and attachment, writes and verifies a SHA-256 manifest, restores into a new isolated directory, and checks source preservation | Standard-library tests check SQLite integrity, a known synthetic row, attachment content, tampering, manifest inventory, and overwrite refusal; not a Vaultwarden integration test |

From that directory, run:

```sh
python backup_restore.py
python -m unittest -v test_backup_restore.py
```

## Safety and operational limits

- The example creates only synthetic data and never opens a real vault database or export.
- It refuses to overwrite existing backup and restore destinations.
- SHA-256 detects accidental corruption; a manifest stored beside the data does not defend against an attacker who can replace both.
- The SQLite file is a purpose-built synthetic database, **not** the Vaultwarden schema. The checks do not prove Vaultwarden application consistency, login, attachment retrieval from a running service, encrypted off-host retention, or recovery objectives.
- Never commit admin tokens, real vault data, exports, or encryption keys.

The [application-aware recovery runbook](docs/RESTORE-RUNBOOK.md) expands these limits into a controlled backup, isolated restore, synthetic application-validation, evidence, and cleanup checklist. It remains operational guidance: it has not been executed against a live Vaultwarden deployment.

## Roadmap

1. Keep the synthetic SQLite/file drill dependency-free and fail closed on invalid database content or incomplete manifests.
2. Add a separately isolated Vaultwarden application-level recovery harness only when the application image, synthetic account setup, networking, and data-handling controls can be validated without production credentials.
3. Require isolated restore evidence and source-preservation checks before making any operational recovery claim.

## Contributing

Use synthetic fixtures and isolated temporary directories. Report security issues to <zqmcomputing@gmail.com>; do not disclose vulnerabilities in public issues.

## More from this series

- [authelia-cookbook](https://github.com/ZQM-Computing/authelia-cookbook) — Identity and access-control patterns
- [caddy-cookbook](https://github.com/ZQM-Computing/caddy-cookbook) — HTTPS reverse proxy patterns
- [portainer-cookbook](https://github.com/ZQM-Computing/portainer-cookbook) — Container management
