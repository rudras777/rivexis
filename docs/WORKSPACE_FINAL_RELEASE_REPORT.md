# RIVEXIS verified release — October 12, 2026

Live website: https://rivexis-web.rudrasingh0718.workers.dev/
Deployed GitHub commit: e734af268f21010179dc479152028f4c6e8a7c05 (PR60). Workspace implementation: PR59 /993a6117fc4057910d188c7f2ea86a69f5add080.
Existing Cloudflare Worker: rivexis-web, unchanged account/configuration/URL. Native build e18ea102-42ef-4db7-acea-642c552e003c Ready; version4df2ba25 at100% in rollout history. Main CI38224377941, Worker38224378047 and native deployment38224377178 succeeded.

## Completed behavior

- Approved shared teal/bronze SVG and CSS3D background across public, authentication and workspace pages: four fine flowing lines, sparse nodes, three transparent cubes (two on narrow screens), quiet Settings, optional pause and static accessibility/device fallback.
- Six grouped horizontal workspace destinations, keyboard/click/hover disclosures and responsive mobile navigation. Removed decorative workspace ranks, empty-state index and redundant briefing copy; meaningful financial/chart identifiers remain.
- Information controls for important functions and metrics, with focus/hover/tap, Escape/outside dismissal and viewport positioning.
- Verified-account Wallets/Contracts/Networks/Overview routes. Explicit installed-provider EIP-6963/EIP-1193 address access, Ethereum/checksum validation, account/network/disconnect handling, local forgetting and financial-context invalidation. No signing, transaction submission, private keys, network switching or paid relay.
- Ethereum bytecode, canonical metadata and EIP-1967 slot inspection; bounded eth_call, fixed observed block, final block hash/network verification and distributed quotas. User JSON ABI is unverified, memory-only and limited to zero-argument scalar view/pure reads. Owner-validated persistence stores up to five contract identities; five analysis addresses remain supported.
- Existing verified-login requirement, ten Settings sections, reports, financial models, Supabase/Brevo and all other necessary infrastructure preserved. No database migrations, user deletion, account/security permission expansion, new permanent project or paid plan.
- Removed the photographed old Risk Atlas structure completely: SignatureRiskField, WebGL renderer, fallback grid planes, mesh CSS and chapter controls are absent. Closed its unused hero space; public copy, logo assets and brand colors unchanged.

## Validation and real evidence

Next/Vinext builds, types, Deno, AST, invariants, secret scan and existing dependency gate passed. CI runs90 financial/API/auth/account tests,30 retained backend/report/email tests and90 browser tests. PR and main checks all green. Local full browser run89/90: the25-page/width accessibility case exceeded its90-second deadline under load; unchanged isolated rerun passed in55.3seconds. This is recorded rather than represented as a clean local full run.

Thirteen actual production browser tests passed with no request mocks, including exact deployed SHA, no legacy mesh/canvas, one updated background, pause/reduced-motion behavior, mobile overflow/accessibility, guest auth flows and protected new API/routes. Independent host browser also verified the commit, desktop/mobile rendering, grouped authenticated navigation and production rollout.

API28 ACTIVE in retained Supabase project ivszvufdonfgwjpfgwii, hash efe47fa781179b24e0ac52f5173e7757b06c80f540a1c7461f234642d41957bc; all21 retrieved deployed files matched the upload. It retains custom trusted-cookie/CSRF/email verification, with the existing gateway verify_jwt:false configuration. Exact API27 rollback source is stored outside checkout. No API changes were needed for mesh removal.

Real WETH inspection: block26175067,3124code bytes, code hash0xd0a06b12ac47863b5c7be4185c2deaad1c61557033f56c7d4ea74429cbb25e23, nameWrapped Ether, symbolWETH, decimals18. Bounded totalSupply at26175071 returned2172105058155880963009449. Source/ABI remain explicitly unverified. QA WETH identity persisted after reload; no existing identity was removed. Network read at26175088 observed Ethereum. Host browser had no injected wallet: actual vendor permission approval remains unverified, with the truthful unavailable state captured; provider behavior is covered by fixtures.

Financial validation: exported real Aave snapshot at26175106, collateral3012617922847 USD raw/1e8, debt1498881386310 and HF1668225984258009822. WETH−20%, budget3000, target1.50, assumed fee25: first alternative repays1786.911995USDT, total1809.99999916USD, stressed HF1.515000378970311272. All33 independent Python integer checks matched exact raw values, including protocol ceiling debt and weighted-numerator wadDiv half-up, costs, balances and budget. Primary protocol reference: https://github.com/aave-dao/aave-v3-origin/blob/main/src/contracts/protocol/libraries/logic/GenericLogic.sol . Financial model sources unchanged in the final visual release.

Exact handoff to GasGuard at26175115, nonce73: BLOCKED due to insufficient allowance; call/gas execution unverified and gas/fees UNKNOWN. Modeled current-price health after1.893 is distinct from the stressed planner result. Nothing signed or submitted. Three-minute evidence expiry correctly withheld new calculations until refreshed. JSON exports and actual screenshots are in the task outputs.

## Costs, security and limits

No new paid service, dependency, plan upgrade, AI API, infrastructure project or deployment URL. Existing billing unchanged; bounded beta targets zero recurring infrastructure spend. Shared existing quota:300 RPC-backed analyses/inspections daily globally, four per address/minute; an inspection uses several bounded RPC reads. No guarantee of provider allowance or unlimited service. Reports capped20/owner, addresses/contracts capped5each.

Known retained findings: pg_net in public schema; leaked-password protection disabled; existing unpatched build-tool braces advisory GHSA-vfj7-8cjw-p6xm. No new exception or security weakening. Existing RLS/owner checks and no-custody controls remain. Brevo/auth configuration unchanged; preceding live confirmation/recovery evidence retained, with this release testing the unchanged auth handlers and production entry/gates rather than generating another email.

Financial beta coverage: Ethereum/Aave V3 normal mode and one validated Morpho WBTC/USDC86%LLTVmarket. Other chains, markets and unvalidated modes/oracles stay unsupported. Defense search uses5% increments and at most two actions; no global optimum or safety guarantee. GasGuard does not fork combined multi-action execution. Contract code/metadata/user ABI do not prove safety, verified source or financial coverage. No background risk email service, account deletion/MFA management, custody or automatic execution. Safari/Firefox and real wallet vendor approval are not certified here.

Two actual production measurements at4xCPU passed rendering/error/overflow bounds: zero WebGL draws on desktop/mobile, no page errors. Desktop LCP3828ms, CLS0; mobile LCP5012ms, CLS0.0004504. These single-machine synthetic timings are an honest performance limitation, not Lighthouse or field Core Web Vitals certification. Files: BLOCKCHAIN_BACKGROUND_DESKTOP_MEASUREMENTS.json and BLOCKCHAIN_BACKGROUND_MOBILE_MEASUREMENTS.json. Do not claim a high Lighthouse score.

## Rollback and evidence

Git history preserves993a611 (workspace release) and9b99a48 (prior landing). Local baseline/pre-workspace-connectivity-20261012 tag and exact API27 source preserve rollback. Avoid restoring API27 while new contract preferences are actively used without assessing compatibility; rolling back only the mesh removal leaves API28 intact. Production data and existing users were never removed.

Task outputs contain mesh-removal-live-desktop.jpg/mobile.jpg, workspace-live-navigation-desktop.jpg, workspace-live-contract-evidence.jpg, wallet-availability/financial screenshots, actual exported receipts, WORKSPACE_LIVE_FINANCIAL_RECONCILIATION.json, final production/local/isolated browser result JSON and CI web log. This evidence-only branch does not deploy another website.
