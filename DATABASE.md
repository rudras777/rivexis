# Database governance

Production is the existing Supabase project `ivszvufdonfgwjpfgwii`, PostgreSQL 17.11.0.003. No database reset, role rotation or schema migration is part of this governance release.

## Observed ownership and access

The 3 November 2026 catalog check found 61 public tables, none without RLS, zero client-callable public security-definer functions and no direct login capability on the `anon`/`authenticated` client roles. Nineteen tables have RLS without policies: these are denied by default, not an instruction to grant access.

The current Edge API authenticates the Supabase user and enforces owner/organization boundaries before using its server-side service client. Core saved comparison receipts live in `rivexis_defi_reports`, referencing `auth.users`; quotas use `rivexis_defi_budget` and bounded privileged routines. Existing `users`, workspaces, organizations, analyses, reports, monitors and alerts also support retained backend/history capabilities. Supabase Auth identities and legacy application user rows are distinct; do not merge them based on email.

Additional read-only catalog counts: zero storage buckets/policies, three non-internal public triggers, 114 public foreign keys, 201 public indexes and one scheduled job. No scheduled command or credential was exported. Performance Advisor reports 113 informational unused-index observations; these do not justify deleting indexes without workload and constraint review. See [the provider's unused-index guidance](https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index).

## Migration reconciliation: partially complete

There are 48 observed entries in `supabase_migrations.schema_migrations`, four tracked Supabase SQL files and a separate Alembic sequence through `0019_investigation_review_evidence_links`. The Supabase project currently has no tracked CLI `config.toml`. This is not a verified fresh-project reconstruction baseline.

Two tracked October SQL filenames have different timestamps from their production ledger entries. Preserve both truthful identities; do not rename historical applied migrations or mark unexecuted versions applied. The governance evidence contains names, statement counts and digests only. One historical migration requires sensitive-statement review; do not export its SQL into this public repository.

Existing PostgreSQL CI validates the Alembic schema, runtime controls, private legacy-table RLS and a disposable fixture restore. It does not certify replay of all 48 Supabase migrations or all managed Auth/storage configuration. Historical restore evidence is dated in [the recovery drill](docs/FRESH_RECOVERY_DRILL_20261020.md).

## Making a database change

1. Identify the actual production table, owners, calling Edge functions, constraints and policies. Capture a metadata baseline without reading unrelated user rows.
2. Reconcile the required baseline before using Supabase CLI reset/push commands. Until then, do not run `supabase db reset`, `db push` or an Alembic upgrade against production based solely on this checkout.
3. Create the new migration using the supported CLI workflow; preserve exact version IDs. Review impact, grants, indexes, lock/downtime risk and rollback or forward repair.
4. Apply it only to a disposable local/staging database with fixture data. Validate ordinary and adversarial owner/tenant access, not just successful SQL execution.
5. Obtain any required production approval and an appropriate verified recovery point. Apply once through the existing authorized connection; read back schema and migration history.
6. Run relevant application tests and provider advisors. Preserve failures and the actual migration/deployment identity.

Full local Supabase reconstruction, production-ledger reconciliation and fresh full-service recovery remain explicit work. A script that creates only convenient tables is not a production baseline.

## 4 November bounded reconstruction

The specifically approved confidential schema-only capture and isolated native PostgreSQL 17.11 restore matched seven public metadata groups, including all 61 tables and RLS flags, 715 columns, 206 constraints, 201 indexes, 45 policies, 13 functions and three triggers. The test excluded 28 unavailable managed-extension entries and all table data; it is not full Supabase reconstruction, migration-ledger replay or user-data recovery. Temporary access was revoked/expired and the local server stopped. Raw schema stays outside Git pending review. [Exact evidence, failures and cleanup limits](docs/governance/SCHEMA_RECONSTRUCTION_20261104.md).

## 5 November matching managed-extension replay

The entire confidential 1,100-entry schema-only archive now replays atomically in the pinned matching Supabase PostgreSQL image, with zero excluded entries. Six extension versions and all seven public catalog fingerprints match; 61 restored public tables have RLS enabled. This resolves the earlier missing-extension limitation, while full-service/user-data recovery, migration-ledger reconciliation and a sanitized executable baseline remain incomplete. No production SQL or user record changed. [Evidence and exact isolation/cleanup scope](docs/governance/MANAGED_SCHEMA_RESTORE_20261105.md).
