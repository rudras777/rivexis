# Backup, Restore and Retention — P11

Rivexis retention is non-destructive by default. Provider-request telemetry defaults to 90 days, audit logs to 365 days, and reports/investigation artifacts to indefinite retention. `scripts/retention_sweep.py` performs a dry run unless `--apply` is used and `RIVEXIS_RETENTION_ALLOW_DELETE=true`; report deletion additionally requires `RIVEXIS_RETENTION_ALLOW_REPORT_DELETE=true`.

`scripts/certify_backup_restore.py` performs a local procedural backup/restore certification by migrating a temporary SQLite database, inserting a marker, taking an online backup, restoring it, checking integrity and marker recovery, and confirming all 53 application tables. This validates the procedure locally; it does not certify managed PostgreSQL disaster recovery.

PostgreSQL certification is opt-in with separate source and disposable restore-target URLs. Restore execution additionally requires `RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY=true`. Never point the restore target at production.

Both legacy scripts now reject remote restore targets, source/target aliases, non-PostgreSQL URLs and connection-routing overrides before running `pg_restore --clean`. The restore database must be local and named `rivexis_restore_*`. Guard regressions run with `python -m unittest discover -s scripts -p test_backup_restore_guard.py`.

These scripts remain procedural drills, not production backup certification: their archive is temporary, roles/storage/service secrets are not completely backed up, and the old PostgreSQL drill expects the legacy55-table fixture. Do not use a passing drill as the production upgrade gate. A durable complete backup and a restore of the actual deployed schema/data/auth/required service configuration must be independently verified before maintenance. Production currently has61 public tables; source-consistent row/data reconciliation, not a fixed fixture count, is required.

Production release gates should document RPO/RTO, encryption, immutable/off-site storage, backup frequency, restore drills, retention/legal requirements, and access/audit controls.
