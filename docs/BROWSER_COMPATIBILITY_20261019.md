# Additional browser-engine verification — 19 October 2026

Production remains the independently verified PR94 merge `5247672bbe1eceb377c2862b90c611549e959071`. PR95 adds browser-engine verification and defers speculative Overview/header destination loads until selection. No application model, API, database or visual change.

The established default suite is Chromium269 cases. The new optional `npm --workspace @rivexis/web run test:compatibility` runs the same cases in the pinned Firefox and WebKit engines, with no retries or flaky acceptance. Controlled authenticated API/provider fixtures are restricted to a localhost test server; the config rejects a production base URL. Overall case budget is90seconds for multi-step cases, while existing per-assertion deadlines and financial/service request deadlines remain unchanged. This is functional compatibility evidence, not a performance/SLA claim or certification of native Safari, Apple devices or installed wallets.

The existing real Chromium clipboard permission/readback assertion remains. On other engines, a wrapper awaits the native clipboard-write promise before recording its exact argument; it neither replaces native success nor forges clipboard content/permissions. This avoids relying on Chromium-specific permission-grant/readback plumbing while retaining the real native write outcome.

## Initial local evidence

- Official pinned Firefox155/build1543 and WebKit26.6/build2359 packages installed from Playwright's CDN, without dependency upgrades or deletion of existing browsers.
- Firefox failed before any application scenario: `browserType.launch: spawn UNKNOWN`. A single-case probe and Windows SideBySide events independently identify failed activation of the `mozglue` assembly. The DLL is present; no security protection was bypassed, vendor binary altered or OS runtime silently changed. The interrupted broad launch run is not application test evidence.
- WebKit launched and passed a single storage-denial/workspace-switching probe. Its first31-case local run stopped at three overall30-second case-budget timeouts: two passed, one interrupted and25 did not run. Failure screenshots/video/traces and logs are retained. These do not establish a product defect or a compatibility pass; targeted retesting remains required.
- One initial focused command used the variadic project option incorrectly; its CLI error is retained separately. It did not execute application scenarios.

## Existing-infrastructure follow-up

The new bounded PR/manual workflow uses standard `ubuntu-24.04` runners in the **existing public repository**, two explicit engine jobs, contents-read-only permission, existing pinned checkout/setup actions and lockfile. No deployment, database credential, wallet permission, paid runner or new service is involved. GitHub documents standard hosted runners as free for public repositories: https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job . Results are recorded in job logs; no new persistent artifact-storage upload is added.

PR runs execute269 localhost fixture cases per engine. After release, a manual dispatch with the exact deployed commit selects the separate real-public29-case suite per engine on the fixed existing URL. Fixture and public result records are distinct; no live account/signup/password/submission action is added. Both full engine results, exact-head CI and any necessary corrections remain pending. Preserve failures and separate host launch limitations from actual application behavior.

## First Linux results and correction checkpoint

Source `e2338229ebee293fe03ee7b08bf80103eaff8479`: sourceCI39294677457 and PRCI39294761442 each passed269 Chromium cases; Worker39294761268 passed. Compatibility39294761477 was rejected: WebKit268 passed/one failed (406,385.934ms), Firefox264 passed/five failed. No retries, skips or flaky acceptance. Full original logs remain outside Git.

The WebKit failure was an uncaught error for a speculative reports RSC request during reload, after all workspace/switch/reload assertions passed. A separate controlled pre-fix regression reproduced **six destination route requests before selection**. Disabling Overview's three action prefetches reduced this to two wallet requests, identifying the header link as a second source. The current candidate also disables header-wallet prefetch. Destinations and client navigation remain unchanged; no global browser-error filter or exception waiver was added. The new request/explicit-navigation regression expands the candidate suite to270 cases per engine; it must pass on the final source. No causal LCP improvement is claimed.

Four Firefox failures stalled in the browser's broad `load` event before workflow assertions ran. The affected helper navigations now await `domcontentloaded`, retaining every subsequent semantic control/financial assertion. The Settings duplicate test now verifies the filled value and commits input focus before clicking; duplicate rejection, single saved address and unchanged server-write count remain mandatory. Its prior failure is retained and no product fix is claimed until the rerun proves it. Failure context is now logged with bounded output directly in CI, without persistent artifact uploads.

Both rebuilt frameworks and final type/AST169 passed for the expanded candidate. Initial local correction run passed31 cases and caught only the remaining header-wallet prefetch; its evidence is retained separately. Final32-case focused run passed without retries/skips/flakes, including zero premature requests and successful selected navigation. Updated-head full Chromium/Firefox/WebKit CI, merge, same-URL deployment and actual-public checks remain pending.
