# Database maintenance continuation — 13 October 2026 IST

Fresh read-only inspection of existing project ivszvufdonfgwjpfgwii confirmed PostgreSQL 17.6, 61 public tables and zero public tables without RLS. Security advisors still report pg_net in public and disabled leaked-password protection, plus 19 informational RLS-without-policy findings on intentionally private server tables. No grants or policies were widened.

PR67 now rejects unsafe targets before either legacy PostgreSQL drill invokes an external tool. Five regression tests cover 23 cases, including production-target rejection at both real entry points; CI runs these regressions on every change. Legacy drills are explicitly documented as temporary fixture procedures, not durable production backup certification. Latest verified visual-release evidence is in WORKSPACE_CLARITY_RELEASE.md; it supersedes older UI commit evidence in PUBLIC_LAUNCH_RELEASE.md.

The user authorized autonomous continuation of the described maintenance. The complete backup and verified restore prerequisite still blocks the PostgreSQL upgrade. Connected SQL tools cannot perform a complete pg_dump and no configured database connection was found. Do not reset the existing database password, introduce paid backups, drop pg_net, discard cron history or certify a partial export as a complete backup. Vault is installed (supabase_vault 0.3.1); any eventual restore must preserve the required encryption configuration without exposing secrets.

Official documentation reviewed: https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore and https://supabase.com/changelog/postgres-15-19-17-11-breaking-changes . New tooling alone does not resolve missing database access. Production database and user data were not modified in this continuation.

Read-only upgrade compatibility preflight found zero ltree key indexes, zero GiST float key indexes, zero nonextension custom selectivity estimators and zero nonextension stored functions referencing PGP encrypt/decrypt. Repository search found no legacy PGP cipher references. These results cover catalog/code usage; they do not certify external-client encrypted data or replace the backup prerequisite. No reindexing or decryption was run.

## Completed release

PR67 merged as 45e29ec0447ab247abde1ab27343bfac04ec9a50. PR CI38297636810 and38297627246 succeeded, including133 browser tests and the five restore guard tests. Final main CI38387515630 and Worker bundle38387515619 succeeded. Existing Worker native build4ecc8172-6065-4c55-9e8c-1dc4b4b093eb deployed version6517df7c-99a5-4d26-bac9-bbe19f6d9c44 at100% Ready. Actual public HTML build metadata independently matched45e29ec. No overlapping manual deployment was run.

Final production suite passed13/13 in1.3minutes with no skips or retries. It covers exact build, public auth gates, unauthenticated API rejection, auth/recovery forms, mobile accessibility and motion/navigation regressions; it does not newly certify a signed-in financial workflow or a production database restore. Existing signed-in financial evidence remains in WORKSPACE_CLARITY_RELEASE.md; application and financial code were unchanged in this maintenance release.

Artifacts outside checkout: ../../outputs/maintenance-final-production-results.json, ../../outputs/maintenance-release-cloudflare.txt and ../../outputs/maintenance-release-live.png. Complete database backup/restore and PostgreSQL upgrade remain blocked by unavailable direct database access. This release closes the restore-script safeguard work, not the unrestricted launch gate.
