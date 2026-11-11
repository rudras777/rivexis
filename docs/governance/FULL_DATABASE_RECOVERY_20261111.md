# Full database archive recovery — 11 November 2026

**Verified: fresh full database archive replay in an isolated target. Operating full-service recovery and independent key custody remain incomplete.** [Sanitized receipt](../evidence/full-database-recovery-20261111.json). Customer rows and confidential historical SQL remain outside Git and were not printed or shared.

## Capture and access closeout

The owner specifically approved the reviewed24-hour, single-project Database read-write token solely to request a300-second read-only login, capture a confidential encrypted local backup, attempt isolated restore and revoke access. The token could modify production data; actual database operations were read-only. It did not grant organization-wide, migration, backup-restore, network, Auth-configuration or paid-plan capabilities. No password was reset.

The existing provider issued `cli_login_supabase_read_only_user`; an explicit read-only transaction selected `supabase_read_only_user` and verified `transaction_read_only=on`. The connection used the previously accepted project CA with TLS `verify-full`. The capture operation ran07:32:48–07:33:11 UTC. PostgreSQL17.11 pg_dump produced a consistent2,157,807-byte custom archive with104 table-data entries, including authentication and migration data. Its Windows CurrentUser DPAPI encryption round trip matched the original archive hash. Raw values and one-time credentials were never printed.

The exact new token was deleted through its dashboard row; the list subsequently showed no access tokens. Its local encrypted token/login files were removed, clipboard cleared, and a metadata check confirmed the temporary login expired with zero active connections. No broad CLI-role cleanup or original credential rotation occurred.

## Restore and verification

The previous Linux runtime/cache was absent, so the first attempt was withheld. A new task-owned runtime used the already verified Docker29.9.1 archive (SHA256 `c158ecc55adb3afb01bbd3539ed3b997d20c26dbdc418080506cc1bf5243ff57`) and pinned official `supabase/postgres@sha256:d6844e71062a3c8e2f8021d644802850760ef970a45ac163ec8c9f0171075bda` image, source tag17.11.0.003. Fresh provider metadata matches its six extension versions: pg_cron1.6.4, pg_net0.20.4, pg_stat_statements1.11, pgcrypto1.3, supabase_vault0.3.1 and uuid-ossp1.1.

The fresh template0 target had networknone, no published ports, no restart,1GiB memory and two CPUs. Cron job launching was disabled and pg_net targeted a nonexistent inactive database. Password-free NOLOGIN role metadata supplied owners; the local random bootstrap password was never printed or reused. This was an explicitly approved recovery target, never an application preview or development fixture.

The entire archive replayed with `pg_restore --single-transaction --exit-on-error`, excluding zero entries. A confidential local reader counted COPY rows without printing their values. All104 restored table-data section counts match the archive, including all48 migration-ledger entries. All61 public tables have RLS. Fresh production and restored public catalog fingerprints match in seven groups:715 columns,206 constraints,13 functions,201 indexes,45 policies,61 RLS flags and three triggers.

## Cleanup, custody and limits

The exact labeled container and its anonymous volume were removed; checks found zero container/volume directories, no running owned daemon and no daemon socket. The public image cache is retained. The redundant plaintext archive was removed only after re-verifying the encrypted copy. The protected archive and confidential diagnostics remain under a non-inherited owner-only Windows ACL. The older Windows restore directory remains untouched after its previously rejected automatic recursive cleanup; that action was not retried.

This closes the fresh full-database archive replay gap, including row-data/ledger restoration. It does not prove value-by-value service acceptance, operating Supabase Auth/Storage/Realtime/Edge/SMTP/IAM recovery, portable founder-independent custody, Vault decryption/root-key custody or production RPO/RTO targets. CurrentUser DPAPI depends on the original Windows account; this is not an independently portable disaster-recovery key. No archive upload/sharing was authorized or performed. The public executable baseline still has22 content-verified migration identities out of48; the confidential full ledger in a recovery archive does not certify source reconciliation.

Production tables, customer identities and saved records were not reset, restored or deleted. Ordinary authorized reads and temporary provider-access housekeeping are distinct from a production migration. No paid service or recurring cloud resource was added.
