# RIVEXIS public-launch engineering — resumable record

## Current verified state — 2026-10-13 IST

Follow-up: genuine recovery email delivery verified in Gmail and Brevo at00:05 IST using retained QA identity, no credential change. Native Cloudflare build for b2ed4c9 confirmed Ready; GitHub manual deployment secret is separate optional maintenance. Supabase owner dashboard offers17.11.0.003 with up to1hour downtime/no downgrade; inspection cancelled before submission. Free plan and paid-only leaked-password protection verified. Full backup/restore certification and explicit maintenance approval remain required; see release report follow-up.

Production source b2ed4c94d0f53ddc05fa2c15f98468b50054c101 is live on the existing URL, Worker ce7d15b1-6c49-497f-b819-5717b37fb903 at100%. API29 exact21-file verification remains valid. Main CI38289868663 passed131 browser cases and release gates. Final actual-production13/13 passed; performance probes2/2 passed, LCP1968ms desktop /2064ms mobile at4xCPU, CLS0. Final scoped provider regressions38/38 passed. No layout/branding redesign, production data deletion or plan change.

Read [PUBLIC_LAUNCH_RELEASE.md](PUBLIC_LAUNCH_RELEASE.md) for final evidence, supported coverage, rollback and next steps. Historical pending statements below are a chronological record, superseded by that report. Decision: NOT READY — CRITICAL BLOCKERS REMAIN for unrestricted public launch. Remaining gates: controlled PostgreSQL maintenance/extension/password-protection review, fresh email/native-wallet certification, existing deploy-automation credential repair. Do not repeat completed engineering or claim these gates resolved.

Baseline main/live9d203a1951a00d1f1493d85ed385e9a78bbf7fe2. Safe branch feat/public-launch-functional-integrity. Existing API28, source history, project/data and rollback records preserved. No production migrations or account upgrades authorized/performed.

## Active engineering

- Floating Pause control removed; public footer motion preferences retained, account motion controls added in Appearance, device/reduced-motion honored. Updated tests pending execution.
- Missing concentration/sensitivity/observed-session-history charts implemented from canonical position inputs, with stale/no-debt/unsupported/empty explanations and per-position collateral selection. No fabricated historical positions. Planner null-health chart now explains absence.
- Genuine on-chain market context (ETH/USD and BTC/USD Chainlink observations + Ethereum base fee history) implemented with fixed public RPC, pinned canonical hashes, strict validation, sparse history/recent-round fallback, bounded visible60-second polling, abort/retry/backoff and source freshness. No exchange prices substituted into lending math. Coinbase redistribution restriction found in current official terms, so that feed was not used.
- Financial audit found missing-fee success defect; both Aave/portfolio preview orchestrators now fail closed on missing/zero/malformed gas/fees.55 new scenarios cover LiquidationGuard13, GasGuard15 on each path, planner12. Model kernels unchanged.
- Logout audit found false server-revocation success and cached workspace identities; narrow backend/frontend fixes implemented.26 new backend account/report scenarios and11 browser scenarios added.
- Fresh production read-only audit: all61 public tables RLS, inspected privileged functions/client grants restricted. PostgreSQL17.6 minor-upgrade review, pg_net/public and leaked-password-protection warnings require retained security consideration. No database/account mutation made.

## Release gates not yet complete

Local builders/types, chart/provider/browser scenario suites, full CI, backend source backup/deployment verification, real browser market CORS/update proof, fresh auth/Brevo journey where accessible, exact production commit verification and launch decision pending. DO NOT claim public launch readiness from rendered charts alone.

Dedicated audit records: LAUNCH_FINANCIAL_AUDIT.md, LAUNCH_ACCOUNT_SECURITY_AUDIT.md, LAUNCH_MARKET_SOURCE_AUDIT.md. Actual synthetic/reference fixture tests must remain distinguished from genuine live observations. Native wallet provider permission approval remains uncertified in host browser; no private keys, hidden signing or transaction submission.

## Scenario-driven corrections

Chart13/13PASS final; initialcapturedfixtureAavecollateralexpectation correctedhonestly. Account11/11PASS afternewlogouttestcaughtworkspacequeryrepopulatingclearedselection; guardfixed. Market17/17PASS afterinitialGasGuardtestidentifiednetworkcontextwasinsidepositiongate; rootmovednetworkcontextoutsidethatgateandupdatedtesttoassertzero position/simulationcallsbeforeawalletisloaded. Finalmarketretargetedtest/rebuildpending. Marketadapter21/21PASS. Backendfinancial/account171/171PASS. All local/browser fixtures are explicitly distinguished from live public RPC probes. ExactdeployedAPI28source(21files,hashefe47fa7) preservedatwork/rivexis-api28-launch-rollback.json beforeanybackendrelease.

## Backend released and verified

Supabase rivexis-api29 is ACTIVE; retrieved all21 deployed runtime files and matched every file exactly to the intended release bundle. Bundle SHA256 d11487b0104c912a57e5c8b227e3e678aec7d0b523bfabdbef3a93ef677a343a. Custom cookie/CSRF authentication is retained (gateway verify_jwt remains false as before). API28 exact-source rollback is preserved. No schema/data/account-plan changes.

First full Chromium suite130/131 passed. The remaining Light-mode Axe observation occurred during the existing180ms color transition; a steady-state color assertion passed before Axe, with no CSS/design change. The full131 suite is being rerun. Scoped market17, charts13, connectivity/account11, adapter21, financial/account171 and retained backend30 checks passed.

Full local retest129/131 passed; two initial market batch reads exceeded the old5s assertion while still Connecting. Test waits now align with adapter25s bound; all17 market scenarios passed again(51.5s). Hosted PR CI passed131, but push CI identified real large-text desktop navigation overflow at1440px. Added existing compact-menu fallback through1700px for large text, with font-ready regression assertion. Rebuild/retest and fresh CI are required before merge; no failure is waived.

PR63 merged as ba8bad1. Both final hosted CI runs passed all131 browser cases, other release gates green. Same Worker deployed through existing local OAuth session as dd6a6507; exact public SHA independently verified. Supabase29 all21files exact match. Production13tests passed. Real market quote/fee CORS worked, automatic block26177989->26177995 and fee points4->8 observed; independent RPC matched ETH/BTC quotes. Live Aave read block26177999 succeeded. A narrow post-deploy provenance correction is in progress: sensitivity charts must say modeled points, while actual history remains observed. Existing saved GitHub deployment token rejected(6003); no token/scope changes made. Cancelled old-commit native retry before build/deploy; using existing valid local Wrangler authority.

PR64 final caption fix merged/deployed8436283, Workerfe68ffd6 at100%, final13productionchecks passed. Live snapshot integer checks3/3 and planner receipt49/49 passed independently. Saved reports4loaded, historical restore correctly disabled calculation/preview. Cold production4xCPU samples LCP4556/4568ms, CLS0; performance is not certified. Moving new market provider from public root to the verified workspace shell avoids unnecessary guest-page feed-module loading; full tests and fresh measurement required.
