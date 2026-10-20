# Account-response recovery — 20 October 2026

## Problem and change

A read-only operational review found one actual Supabase Edge503 on GET account/settings in the provider's last 24-hour window. Its gateway error was SUPABASE_EDGE_RUNTIME_SERVICE_DEGRADED, not evidence of a Rivexis exception. Successful Edge Function responses numbered 2091 and authentication denials 548 in the aggregate query; no identities, tokens, IPs or raw user messages were selected. Execution p50/p95 for successful function responses were852/1574ms. The zeros in the separate edge_logs execution-time result mean that attribute was absent, not zero-latency requests.

Separately, a controlled HTTP200 Settings response with missing profile reproduced a TypeError reading emailVerified instead of the explicit recovery UI. The original failed test, trace and extracted page error remain outside Git. This malformed response was fault-injected locally; it was not observed in production or inferred to be the cause of the provider503.

Shared account GET and PATCH responses now pass through one decoder before publication into the query cache or confirmation of a save. It checks profile types, optional dates, all expected preference fields and the existing preference validator. It rejects malformed financial defaults instead of silently filling missing values. Authentication, CSRF, request deadlines and the existing explicit retry behavior are retained. Invalid save confirmation leaves the draft intact and shows no success notice; writes are not automatically retried.

Only the account response boundary and its consumers change. Financial models/handlers, API34, backend, database, dependencies, logo, public layout/colors and approved background are preserved. No migration, production account write, new credential, signing, provider configuration or paid service is required.

## Operational evidence and limits

Cloudflare's actively deployed-version filter showed Worker 6824855c at 100% allocation,644 invocations and zero runtime errors in the displayed24-hour window. Memory/CPU-limit/internal/load-shed/uncaught-exception counters were zero. It also reported74 client cancellations and zero response-stream disconnections. Those cancellations are retained and are not diagnosed as either application crashes or harmless test traffic without request-level evidence. Asset counters displayed zero 4xx/5xx, with 97.61% cache hits; asset metrics are not asserted to be version-filtered. The active table showed medianCPU7.45ms. Provider observations are not field browser Core Web Vitals, sustained load testing or an SLA.

The existing High braces advisory GHSA-vfj7-8cjw-p6xm still has no patched release in the checked [GitHub advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm); npm's current version remained 3.0.3. No force downgrade or undocumented patch was applied. The scoped audit exception remains disclosed.

## Verified release and tests

[PR 98](https://github.com/rudras777/rivexis/pull/98) is merged. Tested source 2d96c5e975479242f11500fd901e266d35ac2886 and main **4ad0ddb0177add65fd0748202e64ed6115638c69** have identical trees. The existing production URL serves this exact main commit; no-cache Node HTTP200 and genuine authenticated DOM independently match it. Worker **6d7ffd8d-82be-4d10-92c3-04c21afffb3e** has 100% allocation, deployment 2d6c78c6-ef40-4e69-b084-3aad86e6f359. Native build 818c8f15-bfa8-4f18-b040-27053191a749 succeeded in 48seconds.

| Gate | Evidence |
| --- | --- |
| Before-fix regression | Failed as intended; captured TypeError reading emailVerified. Local fixture, not a production malformed response. |
| Local Settings | Chromium 31/31 and WebKit 31/31;44,281.805ms /247,263.721ms;14 new cases and 17 retained cases |
| Source and PR CI | [39386577710](https://github.com/rudras777/rivexis/actions/runs/39386577710), [39386618824](https://github.com/rudras777/rivexis/actions/runs/39386618824) PASS;305 Chromium each |
| Worker gates | [39386618897](https://github.com/rudras777/rivexis/actions/runs/39386618897), main [39388116083](https://github.com/rudras777/rivexis/actions/runs/39388116083) PASS |
| Full compatibility | [39386618916](https://github.com/rudras777/rivexis/actions/runs/39386618916) PASS; Firefox 305 /462,390.035ms; WebKit 305 /650,133.194ms |
| Main CI | [39388116043](https://github.com/rudras777/rivexis/actions/runs/39388116043) PASS;305 Chromium and standard financial/API/security/database gates |
| Actual-public Chromium |30/30 PASS on 4ad0ddb0;94,049.078ms |
| Actual-public Firefox/WebKit | [39388528360](https://github.com/rudras777/rivexis/actions/runs/39388528360) PASS;30 each,65,900.385ms /81,133.523ms |

Final cases have zero skipped/unexpected/flaky results, test retries or driver GET releases. Inactive public/fixture jobs are intentionally unselected by workflow mode, not skipped browser cases. Counts across engines/repeated gates are not unique scenarios. Next/Worker production builds, official Next typegen/types and AST 174 pass. Financial 221/API-edge 30/audit 28/sequence-RPC10/market 21/API-client12/wallet 18/driver-safety30 and the existing Python, migration/restore/invariant/secret gates pass. The disclosed npm exception remains; a passing gate is not a clean dependency audit.

Genuine signed-in production Settings renders all ten sections, verified profile, saved Dark/Comfortable/System appearance and financial defaults 3000/25/1.50. Save remains disabled with no draft; no account mutation, session revocation or wallet permission/signing was submitted. The deployed Overview also showed genuine fresh market block 26232383 and seven ETH/BTC oracle observations each. Appearance screenshot and sanitized DOM proof are retained outside Git.

Financial/backend/API/dependency/style/public-asset paths are unchanged from 4849a626. The independently reconciled six-alternative receipt at 26231717 and earlier sequence evidence remain included within their dated scope in [the prior report](UNIFIED_WORKSPACE_CLOSEOUT_20261020.md). No new financial receipt, protocol certification or sequence run is claimed in this account-boundary release.

## Additional availability evidence and retained limitations

Ten bounded rounds,07:28:28–07:30:22UTC before promotion, issued30 unauthenticated GETs without retries or credentials. All passed: /demo200 with exact4849a626 marker; guest session-status200/unauthenticated; protected Settings401. Complete-response p50/max: demo624/853ms, session828/905ms, Settings denial794/1064ms. These are short observations from one client, not a load or SLA certification.

One later Python urllib root probe returned403; its body/headers were not captured. Independent no-cache Node requests to root and /demo returned200/exact 4ad0ddb0, and all actual-public browser tests passed. Cause of that individual403 is unestablished and remains recorded. Earlier public timeout evidence is also retained in the prior report. Zero Worker runtime exceptions must never be represented as zero HTTP/client failures.

## Readiness and next actions

**Supported controlled early access is verified. Unrestricted institutional certification remains open.** Existing logo/colors/layout/background, users/data, GitHub/Cloudflare/Supabase/Brevo and rollback versions are preserved. Added recurring services cost $0; total account billing is not independently certified. No privileged token, upgrade, migration, signing, paid service or production account write was performed.

Owned sender-domain/DNS details were requested asynchronously and remain missing. Native-wallet permission UX, independent key custody/second-machine/full-service recovery, specific privileged backup/maintenance approval, sustained field/load/provider assurance and independent operating/security review remain gates. Existing pg_net/leaked-password configuration warnings and the upstream build-tool advisory stay disclosed. Generic continue does not supply missing owner resources or authorize a new privileged token/outage.

[Structured proof](evidence/account-response-release-20261020.json) hashes 23 allowlisted raw evidence files; no protected recovery file was read. [Supported-beta operations](SUPPORTED_BETA_OPERATIONS_20261020.md), [readiness](PRODUCTION_READINESS.md), [scenario matrix](WORKFLOW_SCENARIO_COVERAGE.md) and the [root checkpoint](../RIVEXIS_PRODUCTION_COMPLETION_TRACKER.md) retain exact next safe actions. Ordinary implementation/deployment/verification for this fix is complete; resume a specifically authorized owner gate or newly evidenced defect without asking for generic continue.
