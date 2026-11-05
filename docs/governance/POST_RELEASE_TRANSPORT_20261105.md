# Post-release transport checkpoint — 5 November 2026

**Partially complete. Preserve the failed live checks; do not claim universal launch or institutional readiness.** Deployed main is PR129 / `60c00fa9a805751c59f4d4e8ef61378c6ce14d7f`, existing Worker `4717400b-85a5-4495-9f72-fb7226494bda` at 100%, deployment `f2eba06c-3596-485f-bfa2-4c4869ca0fcf`, native build `55758239-c46c-4693-88f5-40cb8937d89b`. API40 remains unchanged. This diagnostic branch changes documentation only and is not a production fix.

## Completed release and recovery

All six protected PR129 checks passed. Source CI42038728075 and Worker CI42038728052 passed; main CI42039949289 and Worker CI42039949134 also passed. Chromium fixtures passed 349 cases on both source and main. Reviewed and merged trees match `2fa38dca4f05ab85cdeea4efc3b8fc2ec36f5282`. Earlier PR128's 349-per-browser compatibility and 74 public checks retain their own commit/date scope.

The full matching managed-extension schema-only restore is verified in [its evidence record](MANAGED_SCHEMA_RESTORE_20261105.md). No production user data, financial source, design, schema, DNS, permanent credential or plan changed. The disposable restore container/volume were removed, the task daemon stopped and this attempt's redundant plaintext archive removed after verifying the retained protected copy. Older stopped Windows recovery-directory cleanup limitations remain as previously documented.

## Live results on PR129

| Target / attempt | Passed | Failed | Result |
|---|---:|---:|---|
| Canonical rivexis.rvea.info first run | 36 | 1 | Unauthenticated on-chain contract request returned provider503 instead of401 |
| Canonical single rerun | 37 | 0 | All original assertions passed; no internal retries or assertion changes |
| Original workers.dev first run | 36 | 1 | Browser navigation timed out opening /forgot-password during the five-route form-method test |
| Original workers.dev single rerun | 36 | 1 | Same recovery-navigation test timed out again; unresolved |

The canonical failure body reported `SUPABASE_EDGE_RUNTIME_SERVICE_DEGRADED`. A read-only aggregate query of provider logs from 13:58–14:03 UTC confirmed one503 with that code. A separate bounded probe subsequently received401/no-store from all four on-chain endpoints on both hostnames. The failure remains recorded; no global provider outage or sustained uptime guarantee is inferred.

An independent five-document request probe on the original hostname returned200 with the exact build and POST forms for login, signup, verify-email and reset-password; forgot-password timed out at30seconds. Connected Chrome separately loaded the original recovery page, confirmed the same build and a hydrated enabled reset-request control. No recovery request or credential was submitted. The source recovery page was inspected; no causal source defect is established, and its financial/authentication behavior was not changed to satisfy a test.

The Cloudflare dashboard's selected24-hour metrics showed zero exceeded-CPU, memory, load-shedding and uncaught-invocation outcomes. The active-version median CPU read4.97ms; the separate all-version CPU chart showed higher percentiles, so this is not free-tier capacity certification. Existing last-hour logs showed two error-level events: the canonical on-chain503 and a Network connection lost event. The latter's invocation was GET /platform/ (85ms CPU/88ms wall), not the failed recovery request; do not attribute the recovery timeout to that event or CPU limits. Canceled-request counts also include intentional browser navigation and are not an incident count.

A bounded CLI tail probe did not establish confirmed readiness; its task-owned process was stopped. No absence of errors is inferred from that probe. No raw headers/cookies/console logs were retained by it. The existing authenticated dashboard supplied the metrics/log observations instead. No protection, timeout assertion, paid plan, network setting or tracing configuration was weakened or upgraded.

## Exact next work

1. Continue original-host recovery transport diagnosis using existing dashboard logs filtered to the exact failed request/path/time. Compare request arrival/status/duration with the saved browser traces and a normal connected-Chrome navigation. Do not run more identical broad suites until a new finding or change justifies them. Preserve failures; do not add broad automatic retries, disable security or redirect away the recovery URL as a substitute for diagnosis.
2. The owner confirmed sign-in, but the connected canonical Chrome tab still showed an empty normal login form/Session ended after rechecking. An async clarification asks which exact browser and URL holds the signed-in workspace. Use that actual authorized session once identified; do not import tokens, reset passwords, fabricate acceptance or treat signing into a provider console as RIVEXIS login. Fresh authenticated acceptance is not verified by this continuation; earlier3–4November financial acceptance remains separately dated.
3. Owner Supabase/Cloudflare MFA enrollment, fresh full-service/user-data recovery and independent key custody, migration-ledger/baseline reconciliation, native-wallet permission lifecycle, inbox/sender assurance, independent operating/security and legal/transfer gates remain open in [the main checkpoint](CONSOLIDATION_CHECKPOINT.md). Do not mint new recovery access or perform production migrations without their required specific authorization.

Exact task-output evidence outside Git: `governance-pr129-release-receipt.json`, `governance-managed-schema-{canonical,original}-{live,retest}-20261105.{log,json}`, the two named first-failure trace archives, `governance-live-auth-probe-20261105.json`, `governance-auth-documents-probe-20261105.json`, `governance-worker-error-probe-20261105.json` and the named live/recovery screenshots. Protected recovery material, untracked repository outputs and arbitrary output directories are excluded from scans and uploads.
