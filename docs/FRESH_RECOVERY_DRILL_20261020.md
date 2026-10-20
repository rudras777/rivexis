# Fresh production recovery verification

20 October 2026 UTC. This completes a fresh logical backup and isolated restore of the existing Supabase project `ivszvufdonfgwjpfgwii`. Production application commit remains `4ad0ddb0177add65fd0748202e64ed6115638c69`; no application redeployment, production restore, database upgrade, password reset, paid change or user deletion was performed.

[Sanitized structured evidence](evidence/fresh-recovery-20261020.json), [current checkpoint](../RIVEXIS_PRODUCTION_COMPLETION_TRACKER.md), [earlier recovery method and limitations](RECOVERY_DRILL_20261017.md).

## Authorized temporary access and capture

The user replied “continue” immediately after review of the exact proposed 24-hour, single-project Database read-write token, its risk and its restricted purpose: temporary read-only database login, fresh protected backup, isolated restore and revocation. That contextual confirmation was used for this action; the revoked 17 October token was not reused. The same exchange explicitly excluded a production upgrade.

Created only that reviewed token. Its one-time value went directly from the existing dashboard into Windows CurrentUser DPAPI through process stdin; no plaintext token file, console output or Git entry was produced. The Management API issued `cli_login_supabase_read_only_user`, `read_only=true`, TTL300 seconds. Production access selected the already-granted `supabase_read_only_user` role; `transaction_read_only=on` was verified. No permanent grants were widened.

The original verified Supabase CA was retained with SHA256 `700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7`; hostname/certificate checks used `verify-full`. The verified dump workflow ran from **16:29:27.9698265 to16:30:07.2964036 UTC**, using custom format and a serializable-deferrable snapshot. It captured the whole permitted database without schema exclusions:61 public tables, database size40,668,307 bytes. The original archive is1,428,343 bytes, SHA256 `f1a453349f067c7972820b4e0dd41b324e02711b92b98ecb08caf1eac0cc1367`. Password-free role definitions and metadata for19 nontemporary/nonbuiltin roles were separately captured and protected.

After capture, the new token was revoked through its own dashboard row; the resulting account list shows **No access tokens found**. Both local token/login credential files were removed. Catalog inspection confirmed the login expired at **16:34:30.032025 UTC**. Neither the original database password nor an owner-level database login was used.

## Actual isolated restore and independent comparison

Used existing Ubuntu WSL and the official Supabase PostgreSQL image matching production17.6.1.166, pinned to digest `sha256:b3bfedb107413abb3b8cb0d0874b0414a1dceb3d55bc0c778de6ad22d1f7dc86`. The task-owned local Docker29.9.1 runtime had no new cloud project or Windows service. The container used network `none`, no published ports, restart `no`, inactive pg_net database target and `cron.launch_active_jobs=off`.

The disposable server bootstrapped `supabase_admin` at OID10. The restore role bootstrap omitted only its duplicate CREATE and three ephemeral CLI-role statements;26 original grantors were preserved through explicit session authorization. Passwords remained excluded. Role bootstrap and the entire archive restored with single-transaction/exit-on-error safeguards into `rivexis_restore_20261020`.

The restored database contained61 public tables,7 auth users,1 Vault record and1 cron job; zero public tables lacked RLS. Independent comparison parsed each archive COPY section, exported the matching restored columns, sorted raw COPY row bytes and compared both SHA256 and exact row counts. **All102 table-data entries and all32,179 rows matched**, with no mismatched table. This comparison occurred before any local Vault logical rekey; it includes the original Vault ciphertext and retained auth/cron history. No production user rows were printed or uploaded.

The read-only role cannot decrypt Vault. The authorized existing dashboard's explicit Show secret value control provided the single logical value directly to DPAPI without displaying it in tool output; it was hidden again. In the disconnected local target, only its ciphertext was re-encrypted under a newly generated local test key, retaining original UUID/nonce/name/description/timestamps. Exact decrypted-value equality passed transactionally. No production Vault value or original production root encryption key was changed/exported.

## Protected kit and cleanup

The portable recovery kit includes17 ZIP entries: original archive, password-free roles/metadata, logical Vault supplement, manifest, verification evidence and recovery helpers/instructions. Its AES-256-GCM version header is authenticated, with a random12-byte nonce and a separate32-byte owner-only key. The key is outside the archive and was not uploaded or committed. The verified encrypted kit is **804,514 bytes**, SHA256 `fedbd8db3ea05414587fcc79989cdaad1cbf8f5314c52ac3e53dc3561f2d4724`.

In-memory round-trip and tamper rejection passed. The independent decrypt CLI reproduced the original ZIP SHA256 `3ed66caf52720b1e89abfeae3bcbfcd550cc3d7a0ed860acfe7d54f2cdadcb01`; ZIP integrity and all16 payload-manifest hashes passed. Decryption for this test stayed in the fresh owner-only recovery directory.

After these checks, nine plaintext/intermediate data files were removed, with each resolved path constrained to that fresh directory. The task-labeled container was stopped/removed; the verified task daemon, restored database, local test encryption key and image cache were removed only after path/process/mount checks. Original17 October recovery material was untouched. The fresh encrypted kit, separate owner-only portable key and DPAPI-protected original supplements remain outside Git.

At16:38:57 UTC, the source project remained ACTIVE_HEALTHY on17.6.1.166; catalog checks still showed61 public tables, zero without RLS, and the temporary login expired. At16:39:36 UTC, ordinary no-cache public GETs to `/` and `/demo` each returned200 with exact production commit4ad0ddb0. These are post-drill identity/health observations, not fresh authenticated workflow, financial receipt or uptime certification.

## Maintenance and readiness boundaries

The real dashboard offers17.11.0.003. Its confirmation warns **all services offline for up to one hour**, **no downgrade to17.6.1.166**, and right-sizing the current2GB disk. The dialog was recorded and Cancel selected; Confirm upgrade was not clicked. A separate specific maintenance approval is pending.

Fresh read-only compatibility queries found zero ltree/array opclass key indexes, zero float GiST opclass key indexes, zero operators with nonbuiltin selectivity estimators, and zero nonextension stored PGP calls in public/auth/vault. Stored ciphertext, dynamic SQL and external clients were not comprehensively scanned. No reindex or production decryption probe was attempted.

The fresh kit has **not** been copied off-device; the verified private Drive copy remains the separate17 October snapshot. Independent off-device key custody, second-machine restore, automated retention/RPO/RTO, physical/PITR and full provider/service-configuration reconstruction remain unverified. Logical archives omit pg_net unlogged request/response queues, original production root key, role passwords and SMTP/JWT/edge secrets. Do not replay external requests or label this full-service disaster recovery.

Owned sending-domain authentication, actual native-wallet permission UX, sustained performance/provider availability, disclosed advisories and independent institutional operating/security assurance remain open. Existing application release/financial tests retain their dated scope; this documentation change introduces no new runtime or financial test claim. Added recurring services cost remains$0; account-wide billing is not independently certified.

Outside-Git screenshots: `recovery-token-revoked-20261020.png`, `fresh-recovery-upgrade-review-20261020.png`. All private recovery data and keys are excluded from the Git evidence manifest.

References: [Supabase temporary login role](https://supabase.com/docs/reference/api/v1-create-login-role), [scoped tokens](https://supabase.com/docs/guides/platform/personal-access-tokens), [PostgreSQL pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html), [upgrade compatibility notice](https://supabase.com/changelog/postgres-15-19-17-11-breaking-changes), [disk sizing](https://supabase.com/docs/guides/platform/upgrading#disk-sizing).
