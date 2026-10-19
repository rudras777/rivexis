# Service availability recovery

19 October2026, Asia/Calcutta. Continue the existing website, integrations and approved design. This candidate changes only the global service-status request lifecycle and adds a retry control inside its existing failure disclosure. Financial math, API34, authentication, data, protocol coverage, background and branding are unchanged.

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

Final local gates passed: both production builds, official route type generation, TypeScript, AST166, and all45 focused recovery/entry/auth/session cases on the final build, with no retries/skips/flakes. The original failing regression and the earlier15/30-case results are retained. Exact-head source/PR/Worker checks remain required before merge/deploy. The full browser suite adds15 cases to238, for253. The actual-public suite adds one no-interception health-evidence check, for29. Existing financial/model/security/database gates remain mandatory.

## Performance diagnostic

A separate actual-public recorder-disabled mobile4x-CPU profile observed LCP4044ms, CLS0, ScriptDuration297ms, LayoutDuration137ms and style recalculation419ms. Request start occurred3039ms after navigation; first byte arrived393ms after that request began. This one sample shows substantial delay before the request, not proof that the approved background is causing slow initial paint. Other measurements remain variable. No visual change or field-performance/SLA claim follows from this diagnostic. Temporary profiler files are removed from source; source/config and raw evidence are retained outside the repository.

Current verified runtime remains PR92/ddb70a7dcaee5691cf49b829acd891f992998c16 until a newer exact marker is observed. The fresh privileged backup-token draft is uncreated; its action-time question remains unanswered. No database upgrade, paid change, native-wallet approval or recovery-key transmission is included. Domain/native-wallet/recovery and institutional operational-assurance boundaries remain open.
