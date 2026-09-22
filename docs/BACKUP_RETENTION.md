# Backup, Restore and Retention — P11

Rivexis retention is non-destructive by default. Provider-request telemetry defaults to 90 days, audit logs to 365 days, and reports/investigation artifacts to indefinite retention. `scripts/retention_sweep.py` performs a dry run unless `--apply` is used and `RIVEXIS_RETENTION_ALLOW_DELETE=true`; report deletion additionally requires `RIVEXIS_RETENTION_ALLOW_REPORT_DELETE=true`.

`scripts/certify_backup_restore.py` performs a local procedural backup/restore certification by migrating a temporary SQLite database, inserting a marker, taking an online backup, restoring it, checking integrity and marker recovery, and confirming all 53 application tables. This validates the procedure locally; it does not certify managed PostgreSQL disaster recovery.

PostgreSQL certification is opt-in with separate source and disposable restore-target URLs. Restore execution additionally requires `RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY=true`. Never point the restore target at production.

Production release gates should document RPO/RTO, encryption, immutable/off-site storage, backup frequency, restore drills, retention/legal requirements, and access/audit controls.
