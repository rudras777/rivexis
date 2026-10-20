# Production authentication recovery release

21 October 2026, Asia/Calcutta. Same [production website](https://rivexis-web.rudrasingh0718.workers.dev/), repository, Worker, Supabase project and Brevo integrations. **PR100 is merged and deployed as `1bd99ed02b185d121177c29a68b8dcf780fcc61d`.** Tested source `32f804bb4ac2350cefcc127f58d79afa645ede38` and main have identical trees. Public HTTP200 and genuine browser DOM metadata independently match that commit.

Existing Worker `38e5925c-5f4b-4d7f-9ce4-cc87be39faea` has 100% traffic, deployment `0573d302-afa1-4738-b75d-cc2715cf3ff9`, native build `abe065f0-8c11-4cab-8756-c563ff2465cf` ready. Existing backend functions are ACTIVE: API 36, decision-reports 4 and alerts 5. All 29 deployed files match tested packages after normalizing CRLF and trailing whitespace. Existing custom cookie authentication remains enabled; the functions retain their existing verify_jwt=false configuration.

## Completed changes and retained failures

The [approved database upgrade](DATABASE_UPGRADE_20261021.md) completed from 17.6.1.166 to 17.11.0.003, ACTIVE_HEALTHY. All 61 public tables retain RLS; 7 auth users, 1 Vault record and 1 cron job remain. Policy fingerprint is unchanged. The raw ACL fingerprint changed, but independent archive comparison matched all 61 owners and 67 non-owner privileges. Exact production Vault equality passed without printing its value. No production restore, account reset, data deletion, paid-plan change or key upload was performed.

Provider failures previously could be treated as invalid sessions. Unknown/provider 5xx/429/transport/configuration failures now return 503, withhold private access and preserve the cookie without unnecessary renewal. Only explicit invalid access attempts renewal; confirmed invalid/revoked sessions still end access. Invalid field types never reach the provider. Confirmed replacement cookies remain HttpOnly/Secure/SameSite, including when the later application-user check fails. The same boundary now protects history/report and alert requests. Existing ownership, verified-user requirements, quotas and CSRF remain. Alerts SDK is pinned to the already-tested 2.117.3; CI now checks its Deno types.

The first main-handler regression had 25/31 failures before correction. PR99 deployed API 35/b40c6d3f, after which ten real public invalid-cookie scenarios found 8 passing and 2 failing: the actual refresh endpoint used 400/validation_failed for invalid token format. Private access stayed blocked. PR100 narrows that explicit rejection to validated refresh requests. Two new contract cases failed before correction; 28/36 secondary-handler cases also reproduced the related defect. All original failed results are retained. No production outage was injected, and no claim is made that this specific defect caused the genuine QA session ending after maintenance. Lost refresh responses and future provider availability are not guaranteed away.

## Verification

| Gate | Result |
| --- | --- |
| Financial/auth suite |295 PASS, including 74 actual-handler recovery cases across three functions |
| API-edge and Deno |30 PASS; all four checked function entrypoints typecheck |
| Source/PR/main CI |39485302272,39485310926,39486909207 PASS |
| Worker gates |39485310996 and39486909231 PASS; existing native Cloudflare build succeeded |
| Browser regression |Chromium 305 per source/PR/main; Firefox 305/WebKit 305 in39485311089 |
| Actual final public website |30 Chromium,30 Firefox,30 WebKit PASS; remote39487086056 |
| Actual invalid-cookie rejection |30 scenarios/33 requests PASS across API/history/alerts |
| Public commit identity |Independent Node HTTP200, browser DOM and Cloudflare source/traffic agree |

Browser cases have zero final skipped/unexpected/flaky results and zero test retries. The fixture Firefox run recorded one existing guarded bare-GET driver navigation release: the target document was complete 200 with no pending requests or page/resource/server errors. Assertions then continued. This is retained explicitly; no zero-driver-release claim applies to that fixture run. All actual-public engines recorded zero releases. Inactive workflow modes are not skipped test cases. Repeated runs/engines are not additional unique scenarios. [Workflow coverage](WORKFLOW_SCENARIO_COVERAGE.md) maps at least ten cases per critical function.

No UI, branding, approved background, financial arithmetic/defaults, schema or payment requirement changed. The floating Pause button remains absent; accessible motion settings remain. Existing bounded Aave/Morpho scope, 5% planner grid/at most two actions and prior independently reconciled receipts retain their separately dated limits. These new tests do not constitute fresh genuine authenticated financial certification.

## Readiness and exact next steps

**Deployment/public regression checks are complete. Fresh authenticated production sign-off is BLOCKED on normal website login. Unrestricted institutional launch is not certified.** Both preserved QA tabs now show Session ended. No reusable credential is available; the owner has a normal sign-in handoff in the existing website tab. Do not reset a password, import an administrator-created session or bypass authentication. After normal sign-in, verify actual Settings/profile, a supported live position/scenario/planner/transaction preview and private report history/export; preserve drafts and avoid signing or unnecessary production writes.

Other owner/resource assurance gates: owned sending-domain DNS and inbox placement (Spam was previously observed); actual installed-wallet permission UX; independent key custody/second-machine/full-service restore/retention/RPO/RTO; sustained field/load/provider availability and institutional operating/security assurance. The 20 October protected kit remains local; the verified off-device 17 October kit is a different snapshot. No key belongs in Git or the backup-upload destination.

Final advisors retain [pg_net in public](https://supabase.com/docs/guides/database/database-linter?lint=0014_extension_in_public) and [disabled Pro-only leaked-password protection](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection), plus 19 intentionally private deny-by-default table findings grouped under one INFO category. The previously disclosed build-tool advisory GHSA-vfj7-8cjw-p6xm remains scoped; no forced breaking downgrade or unsupported patch was introduced. Added recurring services cost $0; account-wide billing is not certified.

Rollback: preceding Worker f6be436d-9908-4323-8c56-c3b6d533dcad/b40c6d3f and earlier 6d7ffd8d/4ad0ddb0 remain retained. API 34 source, API 35 reconstruction from PR99, reports 3 and alerts 4 source archives are preserved outside Git. Local protected database recovery material remains untouched. This documentation branch records the actual deployed application without an unnecessary runtime redeployment.

Structured proof: [release evidence and raw artifact hashes](evidence/auth-recovery-release-20261021.json). Browser screenshots, raw logs, original failures and the active checkpoint are in task outputs outside Git. No credential, cookie, private user row, recovery key or decrypted Vault value is included in repository evidence.
