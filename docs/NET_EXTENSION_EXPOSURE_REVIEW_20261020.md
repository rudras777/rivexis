# pg_net exposure and recovery-access review

20 October 2026. Read-only continuation on existing Supabase project `ivszvufdonfgwjpfgwii`. Production remains commit `4ad0ddb0177add65fd0748202e64ed6115638c69`; no application deployment or database mutation was required for this review.

## Actual catalog and dashboard evidence

- `pg_net` is version `0.20.4`, registered in `public`, with `extrelocatable = false`. Vault and cron are also nonrelocatable. The generic advisor's `ALTER EXTENSION ... SET SCHEMA` example therefore is not a verified fix for this installed extension. No relocation, drop/recreation or upgrade was attempted.
- All twelve extension-member routines returned by the catalog query are in `net` and are security invoker. Both `anon` and `authenticated` have EXECUTE on them and USAGE on `net`.
- Both roles have SELECT and INSERT on `net.http_request_queue` and `net._http_response`. These are broad database privileges; no routine was invoked and no request/response row or request payload was read.
- The authenticated Data API Settings page shows exactly two exposed schemas. Opening its selector and inspecting the checkmarks confirmed `graphql_public` and `public`; `net` is excluded. The page separately reported zero of 61 tables and zero of 13 functions exposed, automatic new-table exposure off, and extra search path `public extensions`.
- The database-role setting query returned no `pgrst.db_schemas` entry for `authenticator`; that result alone was inconclusive. The actual dashboard selection, rather than an assumed default, establishes the observed Data API configuration.
- The selector was closed without changing a selection. Save/Cancel remained disabled. No API schema, table, function, grant, credential, account, plan or security setting was changed.

This narrows the prior warning: broad database-role grants are present, but this review does **not** establish public HTTP access to the `net` routines. Excluding `net` from the observed Data API is a boundary, not proof against SQL injection, privileged wrappers, later configuration changes or every possible indirect path. Retain the official WARN and independent assurance gate. Do not remove an existing extension or widen privileges merely to clear an advisor.

Outside-Git screenshot: task outputs `net-api-exposed-schemas-20261020.png`. It shows the actual exposed-schema checkmarks. No recovery key, user rows, queue data or credential is included in this report.

## Recovery authorization review and subsequent outcome

The existing dashboard is at the final review for proposed token `RIVEXIS-pre-upgrade-backup-20261019`: 24-hour expiry, one existing project, Database read-write capability only. **Create token has not been clicked.** The browser identifies this as high risk because it grants new privileged access.

An explicit asynchronous confirmation now describes that exact scope and its write capability. Planned use is solely to request a temporary read-only database login, create a fresh protected production archive, verify an isolated restore and revoke the token. No password reset, paid upgrade, production restore or database upgrade is included. The earlier approved token was revoked after the dated 17 October drill; it has not been reused.

That review recorded the state before authorization. The user then replied continue directly to the exact reviewed proposal/risk. The approved temporary-access task completed: fresh protected production capture, isolated restore and exact102-entry/32,179-row comparison, logical Vault recovery, encrypted kit verification, token revocation/login expiry and cleanup all passed. [Fresh recovery closeout](FRESH_RECOVERY_DRILL_20261020.md) supersedes the earlier pending-token state. A production version upgrade still needs its own explicit outage/no-downgrade approval. Sender-domain ownership, actual native-wallet permission testing and independent recovery/operating assurance remain separate gates.

Outside-Git review screenshot: task outputs `recovery-access-confirmation-20261020.png`. The proposal contains no generated credential.

References: [official extension-in-public advisor](https://supabase.com/docs/guides/database/database-linter?lint=0014_extension_in_public), [scoped personal access tokens](https://supabase.com/docs/guides/platform/personal-access-tokens), [prior actual recovery drill](RECOVERY_DRILL_20261017.md), [current checkpoint](../RIVEXIS_PRODUCTION_COMPLETION_TRACKER.md).
