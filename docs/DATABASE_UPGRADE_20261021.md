# Approved database upgrade and recovery follow-up

21 October2026, Asia/Calcutta. Existing project `ivszvufdonfgwjpfgwii`, application URL, users/data and integrations retained. **Database maintenance completed: PostgreSQL17.6.1.166 →17.11.0.003, ACTIVE_HEALTHY.** Recovery PR99 passed source/PR/Worker/Firefox/WebKit gates, merged as b40c6d3f, and deployed API35 with all24 source files matched to the tested package. Its existing native Worker build is25df7238. A live invalid-token follow-up below must pass before final release verification.

## Authorization, baseline and actual maintenance

The user replied continue directly to the exact maintenance question and screenshot showing up to one hour offline, no downgrade and disk right-sizing. That contextual approval covered this upgrade, excluding a paid-plan change, password reset or production restore. The existing free project was used; no new project, token, account or deployment service was created.

The [fresh20October recovery drill](FRESH_RECOVERY_DRILL_20261020.md) had matched102 entries/32,179 rows and Vault recovery. Immediately before maintenance, its encrypted-kit SHA256 was rechecked; the separate owner-only key existed without being read/uploaded. The verified snapshot was about two hours old. Current source baseline at18:45:26UTC20October showed61 public tables, zero without RLS,7 auth users,1 Vault record,1 cron job and zero client-callable public security definers. Public table ACL/RLS and policy fingerprints were captured without user rows.

Confirm upgrade was submitted **exactly once**. Supabase accepted operation `b9667749-bba6-4629-a75a-68a8234098e2`, starting18:46:29UTC20October (**00:16:29IST21October**). Actual UI progressed through server preparation, preflight checks, API shutdown, database transfer and migration, then displayed Upgrade completed/back online. No repeat upgrade, restart, manual database migration or production restore was submitted.

The Management API then reported exact17.11.0.003/ACTIVE_HEALTHY. The real database read at18:53:50UTC returned server17.11, with61 tables,7 auth users,1 Vault record,1 cron job, zero public tables without RLS and zero client-callable public security definers. This first healthy read was about7m21s after recorded start; actual API outage duration was not continuously measured and no uptime/SLA claim follows.

## Permission and encryption verification

Public RLS policy fingerprint remained `87bd1161dce422a8e9f98e4db269775a`. Raw serialized ACL/RLS fingerprint changed from `fa893bd9e1b3f385907a0c4f4f9453c4` to `8de9ea7e6892eaabd6dabdf6d5276c70`; this was investigated rather than silently marked unchanged.

Extracted only public table ACL/ownership metadata from the verified protected dump. Its61 owners matched the new database owner fingerprint `05497cde757cedd15633fb1b987719f6`;21 archived GRANT statements expanded to67 non-owner privileges. Every table/grantee/grantor/privilege/grant-option tuple matched the upgraded database. No source owner ACL override existed; all current owners retained default privileges. Anonymous and authenticated clients have zero public-table privileges. The raw representation differs, but no actual table-permission difference was found. No particular serialization cause is asserted. Six temporary decrypted dump/metadata inspection files were removed afterward; encrypted recovery material and keys were untouched.

Using the existing owner's normal Vault display control, the single current decrypted value was compared directly through process stdin against the protected pre-upgrade supplement. Exact equality passed, without printing the value or writing a plaintext file; the value was hidden and the temporary tab closed. No production secret was changed.

All existing Edge functions remained ACTIVE, including rivexis-api34, decision-reports3, alerts4, alert-dispatch3 and recovery-relay3. Security advisors still report the existing pg_net-public warning and disabled Pro-only leaked-password protection, plus19 intentional private-table deny-by-default INFO findings. No grant, extension removal or paid upgrade was used to silence them.

## Actual post-maintenance application checks

On the unchanged4ad0ddb0 application/API34, all30 actual-public Chromium cases passed in129,134ms, with zero skipped/unexpected/flaky cases. The separate paced30 GET observations all passed (ten rounds of /demo, guest session status and private Settings denial). These are bounded real checks; they are not fixture-authenticated customer workflows or load/SLA certification.

The genuine QA workspace reloaded during the API shutdown, withheld private navigation/content and presented a recoverable Retry state after its deadline. After services returned, Retry led to Session ended. **No successful authenticated recovery is claimed.** No credential was re-entered, password reset, session imported or user account changed. A normal website sign-in handoff is pending so the owner can establish a valid session without sharing a password.

## Concrete authentication defect and implementation checkpoint

The existing authenticate function treats an unsuccessful Supabase getUser/refresh response as a missing session without distinguishing operational errors. The outer handler consequently may clear the browser cookie or publish signed-out status during a provider failure. Inspection and controlled actual-handler fault fixtures establish this defect; they do **not** establish that it caused the specific live QA session ending.

Safe branch `fix/auth-provider-recovery-20261021` now distinguishes known explicit auth rejection codes from provider5xx/429, transport/configuration failures and malformed success responses. Unknown/unavailable identity evidence yields503, with private access withheld and no cookie deletion or unnecessary refresh. A bad access JWT can still refresh once; confirmed missing/reused/expired refresh sessions still end access. Malformed cookie field types fail before provider I/O. If identity rotation succeeds but the later application-user database check fails,503 retains the validated HttpOnly replacement cookie without exposing tokens in JSON.

Before the fix,25 of31 new actual Edge-handler cases failed; six already passed. After the change and three additional repeated/recovery cases, all34 cases pass. Full financial/auth suite255, API-edge30 and Deno checking pass locally. Two older SDK fixtures now supply realistic bad_jwt/refresh_token_not_found error contracts; their assertions are unchanged. Financial models, default values, authentication requirements, CSRF, UI/branding and dependencies are unchanged. API34 rollback source is preserved outside Git before any release.

Remaining ordinary work at this checkpoint: source/PR CI, review/merge, deploy the existing API function and existing Worker as required, compare deployed source identity, rerun actual-public/auth probes and complete genuine authenticated financial/Settings/report checks after normal sign-in. Do not force a production auth outage to test the failure path, create a privileged test bypass, or claim recovery of already-ended sessions. Refresh-response loss outside this confirmed-response contract is not solved or guaranteed away.

## Actual invalid-refresh contract follow-up

After API35 deployment, ten actual public invalid-cookie scenarios produced eight passing scenarios and two failing scenarios (eleven requests total). No private access was granted. Missing/malformed/incorrectly typed cookies were rejected correctly, but the deliberately invalid token pair returned503 without cookie deletion. A direct read using only the existing public anon key and deliberately invalid tokens established the actual Auth contract: invalid access403/bad_jwt; invalid refresh400/validation_failed, with the provider stating Refresh token is not valid. No account, credential, user row or provider configuration was changed.

The first classifier conservatively left this unrecognized rejection unavailable. A focused follow-up on safe branch `fix/auth-refresh-validation-20261021` accepts400/validation_failed only from the refresh endpoint after our own nonempty-string input validation. The same code on a user read, unknown errors and provider5xx remain unavailable without deleting cookies. Four additional actual-handler cases reproduce both private and session-status failures before correction and guard against broadening the classification. The two rejection cases failed before the fix; the other36 already passed. Original live failure results and API34 rollback remain retained, and API35 can also be reconstructed from PR99. No visual, financial, database-schema or dependency change is included.

All259 financial/auth cases and Deno checking pass locally. Release gates, deployment and fresh actual-public checks for this follow-up remain pending at this source checkpoint. Genuine authenticated checks still require the owner's normal website sign-in; no bypass or password reset is authorized by this checkpoint.

Owner gates still include sending-domain ownership/DNS, real native-wallet permission UX, independent key custody/second-machine/full-service recovery and institutional security/operating assurance. The supported beta scope and prior financial receipts retain their separately dated limits.

Raw evidence is in task outputs outside Git: database-maintenance-preflight, database-upgrade-started/completed screenshots, unavailable-workspace screenshot, ACL reconciliation, Vault equality, public browser/paced HTTP results, API34 rollback, before/after regressions and local test/typecheck logs. No key, credential, private user row, cookie or decrypted Vault value belongs in Git evidence.

References: [official Auth errors](https://supabase.com/docs/guides/auth/debugging/error-codes), [upgrade compatibility notice](https://supabase.com/changelog/postgres-15-19-17-11-breaking-changes), [pg_net advisor](https://supabase.com/docs/guides/database/database-linter?lint=0014_extension_in_public), [password security](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection).

The same concrete provider-failure defect was then reproduced in the separate history/report and alerts handlers:28 of36 new secondary cases failed before correction. Both now follow the same verified-session contract, including malformed-cookie validation, unavailable-provider preservation, explicit rejection and confirmed renewal. All74 auth-provider cases pass after correction. Existing owner-bound reads and CSRF checks are retained. The alerts SDK is pinned to the already-tested2.117.3; CI now includes alerts in Deno checks. Preserved production source archives for decision-reports3 and alerts4 match all4/1 repository files before mutation. Follow-up PR100 contains these related corrections; its latest exact head must pass gates before deploying all three existing functions.
