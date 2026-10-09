# RIVEXIS transformation journal

## Objective and baseline — 2026-10-09

Transform the existing product in `rudras777/rivexis`, retaining the `rivexis-web` Cloudflare Worker and `ivszvufdonfgwjpfgwii` Supabase project. No billing changes, identity migration or production data deletion are authorized.

- Development branch: `transform/defi-risk-platform`.
- Source and observed public build: `d863d00b8a4e46de59586462a6a40c5bba21ddf9`.
- Recovery tag: `baseline/pre-defi-transformation-20261009`. A local full-history Git bundle is preserved outside the checkout.
- Production URL: https://rivexis-web.rudrasingh0718.workers.dev
- Supabase: ACTIVE_HEALTHY; API v11, reports v2, alerts v4, dispatch v2. Deployed API source fetched before modification.
- Legacy database rows retained: 4 users, 4 workspaces, 25 analyses, 1 decision, 1 saved analysis, 4 reports, 1 monitor and 1 alert.
- No public grants on existing tables; `has_table_privilege` confirmed anon/authenticated cannot select `public.users`. RLS-disabled legacy tables remain a defense-in-depth concern, not verified public exposure.
- Security advisors: pg_net in public; leaked password protection disabled. No blind remediation or paid upgrade.
- Brevo account/sender connectors returned internal errors. Delivery remains UNVERIFIED.
- Cloudflare deployment workflow is manual; recent runs failed. Local Wrangler authority is being checked. Never infer release success from push.

## Architecture and migration policy

One fixed-point model serves LiquidationGuard, Scenario Lab, Defense Frontier and GasGuard. Ethereum Aave V3 normal-mode positions first; unvalidated eMode, isolation, nonstandard oracle freshness and Morpho fail closed for modeling. Real snapshots read protocol state at one block and retain raw values. Anonymous public reads have persistent global quotas. No paid simulation or AI dependency.

Auth cookies, CSRF, workspace checks, existing API bridges, report and alert runtimes are retained. Historical engine records remain readable. Engine public interfaces are retired after dependency review; reusable backend engines remain archived source. Additive quota and report storage only, restricted to the service role, with owner authorization in the existing runtime. No schema reset.

## Release gates / status

LIVE: bounded Ethereum/Aave V3 beta on the original production URL. Release gates passed for the supported scope; unsupported protocol modes remain explicit. Email inbox delivery and Cloudflare billing visibility remain unverified.

Required: independent arithmetic/reference tests; malformed/stale data rejection; quota and security checks; locked builds/typechecks; responsive/browser QA; real RPC agreement; auth regressions; exact production commit and public API verification. External tests are labeled PASS / FAIL / BLOCKED / UNVERIFIED, never inferred from mocks.

## Rollback

Redeploy the baseline tag to the same Worker using the existing deployment authority; restore the captured API v11 source if necessary. Leave additive tables and historical user data intact. Do not reset main, force-push, rotate credentials or delete users. Verify public build marker after rollback.

## Validation update
- 27 selected browser tests PASS, including five-check monitoring, auth/session/CSRF, tenant scope, history and accessibility.
- 17 new financial/API boundary tests and 29 retained Edge tests PASS.
- Typechecks, AST lint, Next production build and Vinext Worker build PASS.
- Database distributed wallet quota [true,true,true,true,false]; public report access denied.
- Brevo read connector remains unavailable after three attempts; inbox delivery UNVERIFIED.
- Cloudflare billing/subscription API returned 403 with existing OAuth scope. No billing changes requested or performed; account plan/total charges UNVERIFIED.
- Actual EIP-1967 Aave implementation 0x728a138a4823392c2efa55e028d434f526fe03cf differs from address-book POOL_IMPL; runtime identity is checked and model agreement established from on-chain data.

## Production evidence — 2026-10-09
- Initial deployment: original URL, exact main SHA 1b448e5f21b8e74a26fe37fa86c308e431be1d46, Worker 19ac8b43-9887-4505-9f8d-f0feec8b5f29. GitHub CI 37943824615 and 37943823801 PASS; the merge tree matches the certified branch tree.
- Authenticated browser retained the existing Production QA Workspace and Primary Workspace session. A real Aave comparison was saved and retrieved as report 346ce9fc-b4b3-42ca-bec9-3ae049bd29e2. No new identity or credential entry was required.
- Legacy data counts unchanged: 4 users, 4 workspaces, 25 analyses, 4 legacy reports. One explicit new risk report was added to the new owner-scoped table.
- Live UI testing identified the already-met-target edge case. Added a zero-cost, zero-gas no-transaction candidate, regression tests and optimizer identity bounded-frontier-2. Never rank a paid transaction ahead of an already-satisfying $0 baseline for the least-capital objective.
- Financial validation is bounded normal-mode Aave WETH/USDC/USDT. Morpho, eMode, isolation, composite oracles and live multi-protocol discovery remain unsupported. Fresh Brevo inbox delivery remains UNVERIFIED.
- Final deployed source: e42fd2a22721c26b73756c48c2ae906e1ed04674 (PR #35 merged); same Worker version 30481780-7781-4ff9-bdd9-1d45c76ece10. Existing Supabase rivexis-api v16 is ACTIVE; other Edge Functions retained.
- Final main CI 37945178364, worker-bundle 37945178128 and pages build 37945177668 PASS. Local model, browser, migration and build checks passed before promotion. Separate Cloudflare-connected Workers Builds checks remain a pre-existing pipeline defect; manual Wrangler deployment succeeded.
- Independent live verification at 2026-10-09T14:38:19Z: public marker matches final SHA; block 26155500 observed and modeled health factor both 1621306618169667914; read-only withdrawal simulation succeeds (262067 gas); invalid wallet rejected 422; unauthenticated reports denied 401.
- Final browser: existing account session remains authorized; saved report 346ce9fc-b4b3-42ca-bec9-3ae049bd29e2 remains retrievable. Current-state target 1.50 ranks a $0 no-transaction alternative first. Browser error log empty during this final check.
- Next safe action: validate additional oracle adapters and protocol modes independently, then consider Morpho discovery. Resolve Brevo connector visibility and check actual email delivery without inferring success. Inspect Cloudflare billing and repair connected-build integration with existing authority; do not enable paid plans or broader financial coverage from this record alone.
- The source identity above was verified at that release checkpoint. Later documentation/evidence pushes can trigger the retained Cloudflare build integration and replace the build marker; inspect the marker and Worker check for current identity. Rollback evidence and additive schema remain preserved.

## Continuation — WBTC validation and legacy RLS
- Branch improve/oracle-validation, based on documentation commit 313dba2. At the start, production remained the prior release until this continuation cleared its gates.
- WBTC composite source observed at block 26155556: 0xDaa4B74C6bAc4e25188e64ebc68DB5050b690cAc, pinned keccak256 runtime code 0x585d9bff94e70a45a18e9f7b03dcb249051e32a6cba0f14c6ab81e194595364e. BTC/USD feed 0xb41E773f507F7a7EA890b1afB7d2b660c30C8B0A; WBTC/BTC feed 0xfdFD9C85aD200c506Cf9e21F1FD8dd01932FBB23. Exact composite integer-price agreement; bounds BTC 70 minutes, ratio 25 hours are explicit beta assumptions.
- Public Borrow-event account 0x1FbcadCc4c250cF1f6da6b360263A6EBC3967aA9 (not user-owned) contains WETH/WBTC/USDC/USDT. Same-block collateral, debt and HF agree with Pool. A 0.00001 WBTC withdrawal call/estimate succeeds without signing or submission. Reference snapshot retained in certification-reports/wbtc-reference-snapshot.json.
- Local gates: 22 model/API/oracle tests, 29 retained Edge tests, 27 browser tests, Deno check, Next build, web types/lint and existing narrow npm audit gate PASS.
- Brevo account connector still returns an internal error. No unsolicited email was sent; delivery remains UNVERIFIED.
- Effective SQL privilege audit found rivexis_app access to users/data_sources that information_schema grants omitted for the querying role. The pending RLS migration preserves this existing trusted server role with explicit role-specific policies, changes no grants, and refuses client inheritance/access. It does not FORCE RLS or change table ownership. Never enable these policies for anon/authenticated.
- Migration applied after exact-source CI passed. All 19 audited legacy tables now enable RLS; no public table remains without RLS. Row counts remain 4 users, 4 workspaces, 25 analyses and 4 legacy reports. Effective anon/authenticated users grants remain false; rivexis_app users grant remains true. Remote MCP role impersonation is restricted, so direct production SET ROLE testing is BLOCKED; full PostgreSQL CI role tests and actual production authenticated history pass.


## Continuation released — 2026-10-09
- WBTC feature release 4c599618845e3e69897576e856bdbcdbcdc49442, Worker b2724396-12a7-4297-b3ce-559358035e82, PR #36 merged. Supabase rivexis-api v17 ACTIVE. Source CI 37949202042 passes all four jobs.
- Precision correction fc384ac764f7b70495e12d57596c006256d004bb, Worker 001d01c0-cab4-431e-9527-a4f42d28e705, PR #37 merged. Main CI 37950312692, Worker bundle 37950312685 and connected Cloudflare build PASS. Public HTML and independent browser marker match this commit.
- Oracle USD prices now retain all 8 oracle decimals; token amounts retain up to 8 decimals and positive dust displays a less-than bound. No floating-point conversion is used for these price/balance table cells. Raw exported quantities remain unchanged.
- PASS: 22 model/API/oracle tests, 29 retained Edge tests, 28 browser tests; rebuilt Next bundle, types/lint and actual PostgreSQL migration/runtime/client-denial checks. Initial local precision test used an old built bundle; certification was rerun on the rebuilt source and passed. No stale-bundle run is counted as PASS.
- PASS: independent live normal Aave and WBTC-composite references, exact Pool HF agreement, read-only WETH and WBTC withdrawals, invalid-wallet rejection, unauthenticated receipt rejection and exact expected public source marker. Evidence in certification-reports/defi-live-verification.json.
- Production WBTC stress -10%, budget $25,000, target HF 1.20, assumed fee reserve $2 saved at 20:51:45 IST as receipt aa27aad0-aa60-4cd7-b2da-27b3ff9be55c. It is MODEL_COMPARISON_NOT_EXECUTION, has both composite-feed rounds, 5 alternatives and approval constraints. First modeled repayment costs $20,000.39 including the assumed reserve and reaches HF 1.217 at the saved block. This is a test of public on-chain evidence, not a recommendation or an owned wallet.
- Existing receipt 346ce9fc-b4b3-42ca-bec9-3ae049bd29e2 and 18 retained active-workspace history records remain accessible. One explicit new risk receipt added; no existing record removed.
- Security advisors: zero RLS-disabled public tables; 19 intentional owner/service-only no-policy INFO findings; pg_net in public and leaked-password protection disabled remain WARN findings. No wider grants or identity changes.
- Existing Cloudflare connected deployment recovered and successfully deploys main. No replacement integration/configuration was created. Future documentation-only commits can change the public marker; use the Worker check/version plus exact marker rather than assuming the feature merge remains the newest deployment.
- No paid changes. Supabase free plan retained; current Cloudflare billing totals remain UNVERIFIED. Brevo connector remains unavailable; new inbox delivery remains UNVERIFIED. No unsolicited test emails sent.
- Next safe work: validate Morpho math, market identity, oracle freshness, accrual and bounded discovery before enabling production modeling; extend eMode/isolation only with independent protocol agreement. Resolve Brevo/billing visibility with existing authority. Preserve the current Worker, Supabase data and recovery tag.

## Morpho validation continuation — staging only
- Safe branch validate/morpho-financial-evidence starts from main 5ebc94463eab33c49ba30d013d28f54b23c07462, independently verified on the existing public URL with Worker b8c0fd1e-fc88-4a11-a28e-949111fd4f56. Existing API v17 and user data retained.
- Added a separate bigint Morpho kernel: virtual shares/assets, current-block Taylor interest, fee shares, ceiling debt, protocol-native LLTV health, share-based repayment, relative oracle shocks and inverse withdrawal boundaries. Legacy floating-point debt estimates are not reused. The new modules are not imported by production API or UI.
- At block 26156130, six real Ethereum markets exactly matched actual contract accrueInterest + market executed in one non-persistent Multicall3 eth_call. Stored state was reread unchanged. No wallet signs or submits a transaction. Public event borrowers are reference fixtures, not owned wallets.
- WBTC/USDC market 0x3a85e619751152991742810df6ec69ce473daef99e28a64ab2340d7b7ccfee49, LLTV 86%: withdrawing the exact modeled limit succeeded in eth_call; one extra collateral base unit reverted specifically with insufficient collateral. This confirms the actual contract boundary, not merely agreement between two JavaScript functions.
- At block 26156160, pinned V1 oracle 0xDddd770BADd886dF3864029e4B377B5F6a2B6b83 matched exact WBTC/BTC × BTC/USD ÷ USDC/USD component math and feed timestamps. Vault must be zero, sample 1; scale 1e26; native token decimals 8/6. Three feeds, bytecode hash, market hash and parameters are checked. This oracle is not the Aave composite or V2 vault oracle.
- Morpho core source pinned to morpho-blue@8e26ca6a8dbc5089edcd67fb576248810fd2870a; V1 oracle source morpho-blue-oracles@6941f06e411ca17c692fc63824cc60eeeec0035e. Evidence saved under certification-reports/morpho-*-reference.json.
- Local financial gate: 35 tests PASS, comprising 22 existing Aave/API/oracle tests and 13 new Morpho math, real contract reference, boundary and oracle rejection tests. Production remains bounded Aave support; no Morpho support claim is made yet.
- Remaining release gates: bounded market discovery, protocol-specific scenario/Frontier actions, shared Aave/Morpho wallet capital accounting, supported transaction calls, server receipts, UI coverage and browser/integration/free-tier tests. Do not enable Morpho by labeling a price or debt estimate as validated.
