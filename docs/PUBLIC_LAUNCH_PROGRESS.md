# RIVEXIS public-launch engineering — resumable record

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
