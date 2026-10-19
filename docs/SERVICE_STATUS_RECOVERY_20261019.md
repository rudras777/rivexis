# Verified service availability recovery

19 October2026, Asia/Calcutta. Existing website, integrations and approved design preserved. This release changes only the global service-status request lifecycle and adds a retry control inside its existing failure disclosure. Financial math, API34, authentication, data, protocol coverage, background and branding are unchanged.

## Verified release

Merged PR93: https://github.com/rudras777/rivexis/pull/93 . Source **60b548fc7c4ec48e3a4749709d1a0c21e7bee68d**, production merge **b138b1491ac790aa63937426ba080238d5e09e27**. Existing public URL https://rivexis-web.rudrasingh0718.workers.dev/ serves this exact marker over HTTP200 and genuine authenticated DOM. Existing Worker **7e0ff9e9-c555-490a-9378-5a57d312ae3c**,100% configured allocation read independently with Wrangler. Cloudflare native build **8076b51a-3a8b-415e-83b3-a83bcdaea0cd** has a successful provider check on the exact merge. No new dashboard Ready-row observation is claimed.

| Gate | Run | Observed result |
| --- | --- | --- |
| Source CI |39257361835|PASS;253 browser cases and existing financial/API/security/PostgreSQL checks|
| PR CI |39257383895|PASS;253 browser cases|
| PR Worker |39257384007|PASS; both existing root/bundle configurations|
| Main CI |39258441332|PASS;253 browser cases|
| Main Worker |39258441421|PASS|
| Actual public URL |29 cases,114.720s|PASS; no retries/skips/flakes, including genuine healthy-response evidence|

All full CI runs retain the28 audit-gate scenarios and the narrow existing dependency advisory exception. No new vulnerability-free or institutional-audit certification is claimed.

## Reproduced defect

The previous component checked `/health` once. A transient503, failed connection, malformed response or four-second timeout left its warning permanently visible until reload, even after service recovery. A new browser regression on the original production build failed: expected a second request after the backoff, received only one. Original failure log, screenshot and trace remain outside source control.

## Behavior

- Each request retains a four-second deadline, including response-body reading. Invalid evidence never means ready.
- A failed observation can make two automatic retries, after5 and15 seconds. Healthy status stops all polling.
- Hidden/offline tabs pause work and abort in-flight requests; returning online/visible can resume the remaining bounded attempts. Older responses cannot overwrite current status.
- After persistent failure, the existing warning stays visible with an explicit Retry service status control. The control is disabled during a request. A manual retry starts a fresh bounded cycle.
- Existing degraded-service and legacy-runtime disclosures remain accurate. Valid status evidence is required before hiding a warning; no fake success or retry storm.

## Validation and evidence boundary

Fifteen browser cases passed on the first corrected build: ready/healthy/OK; transient HTTP/transport/JSON/invalid-status recovery; persistent bounded failures and manual retry; stalled request; hidden-tab pause/resume; offline entry; older healthy response after a newer degraded observation; retained legacy-runtime disclosure; no ongoing healthy polling; and disabled in-flight retry. These failure cases use controlled fixtures and local test clocks. They are not a claim that production was forced offline.

Final local gates passed: both production builds, official route type generation, TypeScript, AST166, and all45 focused recovery/entry/auth/session cases on the final build, with no retries/skips/flakes. The original failing regression and earlier15/30-case results are retained. Exact-head source/PR/main/Worker checks and existing-URL verification passed as recorded above. The full browser suite adds15 cases to238, for253. The actual-public suite adds one no-interception health-evidence check, for29. Existing financial/model/security/database gates remain passing.

## Performance diagnostic

A separate actual-public recorder-disabled mobile4x-CPU profile observed LCP4044ms, CLS0, ScriptDuration297ms, LayoutDuration137ms and style recalculation419ms. Request start occurred3039ms after navigation; first byte arrived393ms after that request began. This one sample shows substantial delay before the request, not proof that the approved background is causing slow initial paint. Other measurements remain variable. No visual change or field-performance/SLA claim follows from this diagnostic. Temporary profiler files are removed from source; source/config and raw evidence are retained outside the repository.

## Genuine authenticated observation and remaining limits

The existing dedicated QA session reached Portfolio Intelligence on the new merge. A genuine Morpho public-reference read returned block26226861, collateral$9,992,848.74, debt$6,827,923.99 and health1.258; source identity, chart and supported-coverage disclosures rendered with zero service warnings. No signing, submission, ownership claim, report save, preference/account change or production clock/data mocking occurred. This new observation establishes integration behavior; PR92's separately dated six-alternative/sequence integer reconciliation remains the independent financial reference, since financial source is unchanged.

**READY FOR CONTROLLED EARLY ACCESS** within the documented Ethereum lending scope and quotas. The fresh privileged backup-token draft remains uncreated and its action-time question unanswered. No database upgrade, paid change, native-wallet approval or recovery-key transmission occurred. Owned sending domain/DNS, native-wallet permission UX, independent key/full-service recovery and sustained security/performance/operational assurance remain open. Added recurring service cost$0. Passing bounded tests does not establish unrestricted institutional certification.

Current raw evidence is outside source control: `service-status-release-proof-20261019.json`; original/focused/final45-case logs/results; both final build logs; source/PR/main/Worker logs;29-case actual-public JSON/log; native provider check and Worker allocation; HTTP/authenticated markers; genuine workspace JSON/screenshots; recorder-disabled CPU profile/source/config. Temporary profiler/local probe files were removed from the repository. This documentation closeout is a separate branch, not a newer runtime; do not redeploy merely to make it name itself.
