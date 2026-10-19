# Financial display release and genuine production verification

19 October 2026, Asia/Calcutta. Existing repository, Worker, URL, Supabase project/data and Brevo retained. Telemetry retains its original UTC timestamps; the release was merged17 October and the fresh continuation checks occurred19 October.

## Deployed identity

- PR90: https://github.com/rudras777/rivexis/pull/90 . Source `ea3ddc2e4594e78e9edc4c949a747537d4101d6d`; production merge **35f62adf329a9e58fd63fbfb349f3b2206aac2c8**.
- Existing `rivexis-web` Worker **d11c4aea-00d6-4401-a21d-2a07fe213ea0**. Native build **62e4dbd4-406a-4131-83ca-26169e45228b**, Ready with100% configured allocation. Dashboard, read-only Wrangler and public/authenticated build markers agree. Previous Worker43ba061b remains recorded for rollback.
- Same production URL: https://rivexis-web.rudrasingh0718.workers.dev/ . No API or database deployment, new paid service, account/security change, user deletion or branding/layout change.

## Changes and release checks

Raw health strings now accompany approximate chart coordinates. Health readouts, titles and tables apply the same conservative3/4/6 precision as the headline. Saved USD grouping is honored across the affected charts and financial labels. Positive sub-cent costs and tiny token quantities use explicit bounds instead of zero; exact action prefill and financial arithmetic remain unchanged. Missing decimal metadata is unavailable rather than guessed.

Local focused regression:62 passed, no retries/skips/flakes/failures. Both production builds, types and AST passed. Initial source/PR runs each reported235 passed and one flaky prefill assertion; the release gate rejected them. The assertion had read the empty input before the navigation prefill effect settled. Its bounded settled-value assertion passed ten consecutive repetitions without retries. CI now enables the installed Playwright `failOnFlakyTests` option; retries remain available for diagnosis but cannot produce a passing job.

Updated sourceCI39073408132, PRCI39073411170, PRWorker39073411076, mainCI39073827255 and mainWorker39073827131 all succeeded. Source/PR/main each passed236 browser cases without flaky outcomes. Backend/API/financial units, PostgreSQL migration/RLS/distributed controls/restore fixtures, secret and dependency gates also passed within their recorded scope. The documented Vinext dependency exception remains; no clean-audit claim. The main-run watch temporarily lost its connection to GitHub. Re-reading completed job state and logs confirmed success and236 passes; no test/job was bypassed or rerun to erase a failure.

All26 actual-public browser cases passed19 October against the exact production marker, with zero retries/skips/flakes/failures (97.24s). Public route/authentication/API boundaries, mobile navigation, background/motion and credential-URL handling are included. Controlled provider/API fixtures in the full suite remain separate from this actual-public evidence and native-wallet permission testing.

## Genuine financial and Settings evidence

Using the existing dedicated QA account, changed only health precision3→6 and USD grouping on→off. The actual server save succeeded. A full reload confirmed both preferences persisted. Inspected the previously used public-reference address in the supported Morpho WBTC/USDC86% market; no wallet connection, ownership claim, signature or submission.

At block **26225744**, snapshot hash **0xc08148499387d510806dd661cd7da7af8869df5b65ebe4e07153d019b32cfc2b**, the headline, zero-shock sensitivity readout and table all showed **1.262721**. The genuine exported raw health was **1262721744049084066**. Independent integer reference calculations, without RIVEXIS imports or RPC calls, matched interest195950045, native debt6828861265803, raw collateral1002509958797684, debt682777950588989, adjusted exposure862158564565986 and raw health exactly. Selected precision formats are1.262 /1.2627 /1.262721.

The independent reference follows the protocol's [compounding/fixed-point definitions](https://github.com/morpho-org/morpho-blue/blob/main/src/libraries/MathLib.sol), [virtual-share conversions](https://github.com/morpho-org/morpho-blue/blob/main/src/libraries/SharesMathLib.sol) and [native interest/health accounting](https://github.com/morpho-org/morpho-blue/blob/main/src/Morpho.sol). This checks the recorded snapshot arithmetic and display; it does not establish a new independent protocol audit, global optimality, safety or future execution.

Restored the original three-decimal/grouped settings and reloaded them from the server. A subsequent genuine snapshot showed1.262 in both headline and chart, with USD grouping restored. Original appearance, timezone, financial defaults, workspaces, contracts and reports were preserved. Saved report data was not modified by these checks.

## Performance diagnostics and remaining scope

Two public fourfold-CPU probes passed layout, overflow, background and browser-error assertions. Desktop LCP2524ms/CLS0; mobile LCP5316ms/CLS0.0004845. Two targeted additional cold mobile probes measured3660ms and4016ms, CLS0, roughly0.6s TTFB and2.8–3.5s total long-task time. These samples warrant initial-loading investigation. They are not field Core Web Vitals, a Lighthouse score, a guaranteed latency or proof of a backend outage. The approved visual design is preserved.

Scoped browser QA: **4/5**. Supported flows and genuine numerical/preferences checks passed; variable initial mobile loading and the separate real-wallet/domain/recovery assurance gates prevent a stronger verdict. Current release decision remains **READY FOR CONTROLLED EARLY ACCESS**, with bounded beta quotas. Unrestricted institutional certification is not established.

Remaining resources: an existing owned sending domain/DNS authority, an unlocked configured native test wallet, approved separate off-device key custody and second-machine/full-service recovery. Existing pg_net-in-public, disabled leaked-password protection and documented dependency findings remain controlled maintenance work. No silent purchase, paid upgrade, credential reset, key upload or irreversible operation is authorized by unanswered resource questions.

Evidence outside the repository includes `pr90-*-final-ci-20261018.log`, `pr90-main-ci-20261018.log`, `pr90-live-browser-results-20261019.json`, actual snapshot/UI/reconciliation JSON, Settings restoration JSON, genuine screenshots and public performance probe records. No credentials or recovery keys belong in source control. The source checkpoint remains resumable and identifies the exact active follow-up.
