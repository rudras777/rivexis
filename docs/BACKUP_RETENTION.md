# Backup, Restore and Retention — P11

Rivexis retention is non-destructive by default. Provider-request telemetry defaults to 90 days, audit logs to 365 days, and reports/investigation artifacts to indefinite retention. `scripts/retention_sweep.py` performs a dry run unless `--apply` is used and `RIVEXIS_RETENTION_ALLOW_DELETE=true`; report deletion additionally requires `RIVEXIS_RETENTION_ALLOW_REPORT_DELETE=true`.

`scripts/certify_backup_restore.py` performs a local procedural backup/restore certification by migrating a temporary SQLite database, inserting a marker, taking an online backup, restoring it, checking integrity and marker recovery, and confirming all 53 application tables. This validates the procedure locally; it does not certify managed PostgreSQL disaster recovery.

PostgreSQL certification is opt-in with separate source and disposable restore-target URLs. Restore execution additionally requires `RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY=true`. Never point the restore target at production.

Both legacy scripts now reject remote restore targets, source/target aliases, non-PostgreSQL URLs and connection-routing overrides before running `pg_restore --clean`. The restore database must be local and named `rivexis_restore_*`. Guard regressions run with `python -m unittest discover -s scripts -p test_backup_restore_guard.py`.

PostgreSQL tool calls pass connection credentials through libpq child environment variables rather than command-line URLs. They remove inherited backup URLs from the child environment, suppress password prompts, have a 900-second per-command timeout and redact command failure output. Restore commands use a single transaction and stop on the first error, so a failed restore rolls back its cleanup and changes. Verification queries ignore psql startup files and stop on SQL errors. Credentials still exist in the process environment; this is not encrypted credential storage. Tests mock tools and archives explicitly and do not perform a production dump/restore.

These scripts remain procedural drills, not production backup certification: their archive is temporary and roles/storage/service secrets are not completely backed up. The PostgreSQL drill compares the current source and restored application table counts; CI runs it against the actual ephemeral migrated fixture. Counts alone do not verify data equality. Do not use a passing drill as the production upgrade gate. A durable complete backup and a restore of the actual deployed schema/data/auth/required service configuration must be independently verified before maintenance. Production currently has61 public tables; source-consistent row/data reconciliation is required.

Production release gates should document RPO/RTO, encryption, immutable/off-site storage, backup frequency, restore drills, retention/legal requirements, and access/audit controls.
