# Schema reconstruction — 4 November 2026

**Verified within application-schema scope; full managed-service reconstruction remains incomplete.** [Sanitized evidence](../evidence/schema-reconstruction-20261104.json). This work changes no production table, policy, function or customer record and does not replace the dated user-data recovery kit.

## Authorized capture and access closeout

The owner specifically approved the reviewed 24-hour, single-project Database read-write token, restricted to obtaining a temporary read-only login, confidential schema capture, an isolated restore attempt and token revocation. The token was limited to the existing project, not the organization or legacy full-account scope. Its one-time displayed value went to Windows CurrentUser DPAPI through process stdin; no credential value was printed or committed. The copy control initially yielded an empty clipboard; the same displayed one-time field was then captured securely without creating another token.

The provider issued `cli_login_supabase_read_only_user`, read-only requested, TTL 300 seconds. An explicit read-only transaction selected the existing `supabase_read_only_user` membership and verified `transaction_read_only=on`. Direct connection used the project-linked certificate, verified against the accepted CA fingerprint, with `verify-full` hostname/certificate validation. No original database password or owner-level database login was used.

The schema-only custom archive was captured at `2026-11-03T18:54:54Z`–`18:55:03Z` (4 November in Asia/Calcutta): 642,592 bytes, 1,100 archive entries and **zero table-data entries**. Production metadata confirmed 61 public tables, zero without RLS. The new token was revoked through its exact dashboard row; the list subsequently showed no access tokens. Its local encrypted token/login files were removed. A final catalog query confirmed the temporary login expired with zero active connections. No global CLI-role cleanup was used.

## Restore evidence and limitations

Official portable PostgreSQL 17.11 tools matched the previously accepted EDB archive fingerprint. A task-owned WSL Docker 29.9.1 runtime attempted the official matching Supabase image, pinned to its AMD64 digest. The runtime exited during image pull on three attempts, including an attached terminal attempt. The cause was not established; no matching-container restore is claimed. The verified task-owned Linux runtime/cache was removed after process/path checks.

A disposable native PostgreSQL 17.11 server then bound only to `127.0.0.1:55439`. Password-free metadata for 19 nonbuiltin/nontemporary roles supported a **local NOLOGIN bootstrap**, not a production IAM clone. An initial prefix filter accidentally omitted `pgbouncer`; the corrected role query excludes the literal `pg_` prefix. Subsequent failures identified ACL entries for the unavailable provider extensions. Failed restores used one transaction and exit-on-error; they were not counted as passes.

The successful application-schema test excluded 28 archive entries belonging to `pg_cron`, `pg_net`, `supabase_vault` and their provider-schema ACLs. It preserved application definitions and owners. Independently computed production/restored metadata matched in all seven groups:

| Group | Matched objects |
|---|---:|
| Public table columns/defaults/types | 715 |
| Constraints | 206 |
| Functions/owners/security attributes/definitions | 13 |
| Indexes | 201 |
| RLS policies | 45 |
| Table RLS flags | 61 |
| Non-internal triggers | 3 |

The comparison covers normalized catalog definitions, not customer rows, migration-ledger data, original managed-extension implementation, role passwords, Vault contents, SMTP/JWT/Edge secrets or an operating Supabase Auth/Storage/Realtime stack. The archive had no table data, and no row-based application workflow was certified by this test. The native server was stopped; checks found zero owned PostgreSQL processes and zero listeners on its port.

## Confidentiality, cleanup and next work

The archive and rendered schema SQL have verified DPAPI round trips. A bounded strong-credential-pattern check found no private-key, supported API-token or JWT-shaped value; this is not exhaustive clearance to publish 14,389 lines of raw schema SQL. Raw SQL, private diagnostics and local helper files remain outside Git under an owner-only, non-inherited ACL. Automatic approval review rejected recursive removal of the stopped Windows restore directory, stating only that the action was blocked by policy. The private directory was retained; no active server or production credential remains in use. This cleanup limitation is not hidden as a completed deletion.

Next: repair/reprovision a supported matching managed-extension target, reconcile its extension/role/service initialization and all 48 production migration identities, review and sanitize an executable baseline, and validate it using fixture data in a fresh environment. Do not mark these migrations applied or reset production to fit the checkout. A full-service recovery drill still needs current user-data/configuration coverage and independent key custody; schema reconstruction alone does not satisfy that gate.
