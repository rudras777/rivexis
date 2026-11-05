# Managed-extension schema restore — 5 November 2026

**Verified: complete schema-only archive replay in an isolated matching PostgreSQL image. Full-service recovery and an executable repository baseline remain incomplete.** [Sanitized evidence](../evidence/managed-schema-restore-20261105.json). This continuation used the already approved confidential capture; no new production credential, SQL migration, user-data export or cloud resource was created.

## Capture and target

The [4 November capture](SCHEMA_RECONSTRUCTION_20261104.md) contains 1,100 schema archive entries and zero table-data entries. Its temporary access was already revoked/expired. The confidential archive stayed outside Git under an owner-only non-inherited Windows ACL. The existing CurrentUser DPAPI copy was verified before removing this attempt's redundant plaintext archive. It is not an independently portable recovery key.

The previous Docker pull failures were reconsidered using a minimal official Linux container, a task-owned Docker 29.9.1 daemon and one concurrent download. The empty-container probe and serial image pull passed. The original failure cause is not established. No global service, Windows network/security setting or user-owned server was changed.

The official AMD64 `supabase/postgres` image, source tag `17.11.0.003`, was pinned to digest `sha256:d6844e71062a3c8e2f8021d644802850760ef970a45ac163ec8c9f0171075bda`. Its PostgreSQL reports 17.11. Fresh read-only provider metadata on 5 November confirmed the same six extension versions: pg_cron 1.6.4, pg_net 0.20.4, pg_stat_statements 1.11, pgcrypto 1.3, supabase_vault 0.3.1 and uuid-ossp 1.1. Image extension defaults were checked before replay; restored versions match exactly.

The named disposable container used network `none`, no published ports, no restart, a 1 GiB memory limit and two CPUs. A random local-only bootstrap password was neither printed nor reused. Password-free NOLOGIN role metadata supports object owners and grants; this is not a production IAM/password clone. The target was a fresh template0 database, separate from production and the image's initial database.

## Reproducible failure handling

The first readiness probe reached the image's temporary Unix-socket initialization server. A second attempt exposed the missing pg_cron preload requirement; both failed attempts were retained and were not counted as passes. The successful attempt waited for the final TCP server and explicitly preloaded pg_stat_statements, pg_cron and pg_net. Cron targeted only the disposable database with active jobs disabled; pg_net targeted a nonexistent inactive database, in addition to network isolation.

`pg_restore --single-transaction --exit-on-error` replayed the **entire unfiltered archive**, excluding zero entries. The earlier native Windows test had excluded 28 provider-extension entries; that particular limitation is resolved by this managed-extension replay. The source capture's date remains 4 November in Asia/Calcutta; this does not imply a fresh 5 November user-data backup.

| Public catalog group | Matched objects |
|---|---:|
| Columns, defaults and types | 715 |
| Constraints | 206 |
| Functions, owners, security attributes and definitions | 13 |
| Indexes | 201 |
| RLS policies | 45 |
| Table RLS flags | 61 |
| Non-internal triggers | 3 |

Every group matches the captured source count and normalized digest. All 61 public tables have RLS enabled. The restored database contains zero Auth users, zero cron jobs and zero Vault records, consistent with a schema-only archive. The empty tables are a scope check, not evidence of production data removal. Production was not modified.

The specifically labeled disposable container and its volume were removed, and the exact task-owned daemon stopped. The public image cache remains available for future isolated work. The older stopped owner-only Windows restore directory remains retained after the previously documented automatic cleanup rejection; no recursive deletion was retried. Confidential diagnostics remain local and are excluded from source scans and uploads.

## Remaining recovery gates

This verifies schema archive replay with matching extensions, not the operation of Supabase Auth, Storage, Realtime, Edge Functions, SMTP or production IAM. There are no customer rows, migration-ledger rows, Vault contents or service secrets in this archive. It does not reconcile 48 production migration identities with four tracked files, establish a sanitized executable baseline, prove tenant workflows against restored data or satisfy fresh full-service RPO/RTO and independent key-custody requirements.

Next: review confidential definitions for a publishable baseline without exporting sensitive historical statements; preserve production identities; validate fixture-only application workflows in a disposable stack. Full-service/user-data recovery requires its separately scoped access, configuration, protected data and independent operator acceptance. Do not reset production or mark historical migrations applied to fit the checkout.

## CLI compatibility

This drill used direct PostgreSQL tools, not a Supabase CLI upgrade. [Supabase's 4 November CLI v3 notice](https://supabase.com/changelog/supabase-cli-v3) changes default targets, hosted-write consent and configuration precedence. Before future CLI work, inspect the installed version and command help, pin a reviewed version, and explicitly verify the destination. Do not add `--remote` or `--yes` mechanically to make a failing production command succeed. Existing authorization and review requirements still apply.
