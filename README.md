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

A **Vaultwarden cookbook** for self-hosted password-vault operations. This repository includes a synthetic file-level backup/restore drill. It does not migrate credentials, connect to a Vaultwarden instance, or certify production recovery.

## Repository role and status

**Status:** Active, public — initial backup/restore exercise submitted for review in [PR #2](https://github.com/ZQM-Computing/vaultwarden-cookbook/pull/2).

**Audience:** Engineers documenting safe backup and recovery boundaries for self-hosted credential services.

**Portfolio:** Part of the ZQM Computing cookbook collection, indexed by [geospatial-cookbooks](https://github.com/ZQM-Computing/geospatial-cookbooks).

## Example

| Path | Purpose | Evidence level |
|---|---|---|
| [04-backup-restore](examples/04-backup-restore/) | Generates synthetic files, writes and checks a SHA-256 manifest, restores into a new isolated directory, and verifies source preservation | Standard-library test suite included; not a Vaultwarden integration test |

From that directory, run:

```sh
python backup_restore.py
python -m unittest -v test_backup_restore.py
```

## Safety and operational limits

- The example creates only synthetic fixture files and never opens a real vault database or export.
- It refuses to overwrite existing backup and restore destinations.
- SHA-256 detects accidental corruption; a manifest stored beside the data does not defend against an attacker who can replace both.
- This is a file-copy exercise, not proof of SQLite consistency, application-level restore, encrypted off-host retention, or recovery objectives.
- Never commit admin tokens, real vault data, exports, or encryption keys.

The example README lists the additional checks required for an actual recovery runbook, including application-consistent backup, attachments, ownership, isolated restore, version compatibility, and post-restore application checks.

## Roadmap

1. Keep the synthetic drill dependency-free and testable.
2. Add separately reviewed guidance for application-consistent SQLite backup without using live credentials in CI.
3. Require isolated restore evidence and source-preservation checks before making any operational recovery claim.

## Contributing

Use synthetic fixtures and isolated temporary directories. Report security issues to <zqmcomputing@gmail.com>; do not disclose vulnerabilities in public issues.

## More from this series

- [authelia-cookbook](https://github.com/ZQM-Computing/authelia-cookbook) — Identity and access-control patterns
- [caddy-cookbook](https://github.com/ZQM-Computing/caddy-cookbook) — HTTPS reverse proxy patterns
- [portainer-cookbook](https://github.com/ZQM-Computing/portainer-cookbook) — Container management
