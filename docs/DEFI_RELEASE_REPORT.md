# RIVEXIS — DeFi risk platform release evidence

Release state: the redesigned bounded beta is LIVE at https://rivexis-web.rudrasingh0718.workers.dev. Latest functional release is cf289a60d856c59b6788cad28b871e521f74ec89; Worker version 6cb4ec06-264a-45b3-82f9-32122e0468f7; existing Supabase API v18 ACTIVE. Source CI 37966720748 and Worker bundle 37966720577 pass; the existing Cloudflare-connected build succeeds. Independent public verification and browser metadata match this source identity. Documentation-only successors can trigger the existing deployment integration; the Worker tag and public rivexis-build marker identify the precise current deployed commit. See TRANSFORMATION_PROGRESS.md and certification-reports/defi-live-verification.json.

## Architecture and feature inventory

- KEEP: existing Cloudflare Worker/account/domain, Supabase project and identity, secure-cookie/CSRF auth, tenant bridges, retained analyses/reports, Brevo configuration and alert delivery infrastructure.
- REFACTOR: public website, shared theme, authenticated navigation, portfolio state, reporting, transaction intelligence and risk calculations.
- RETIRE: B1–B5/F1–F5 public engine forms, ten-engine navigation, generic entity/security/bridge/yield/treasury dashboards and fragmented marketing pages. Old URLs redirect; historical records and reusable backend source remain.
- REMOVE: six competing CSS override layers from the active source. Existing wordmark/lockup shapes are retained and recolored with a shared CSS filter; the new teal X SVG favicon is served from the same Worker. Original PNG sources remain recoverable.
- ADD: anonymous wallet lookup; LiquidationGuard block-pinned discovery; per-asset Scenario Lab; Defense Frontier; GasGuard previews; owner-scoped risk receipts; JSON exports; optional five-check in-browser monitoring.

The same bigint/fixed-point module serves frontend scenarios, server-generated account reports and server-side action consequences. Aave state is read from Ethereum through bounded RPC multicalls. Deployment identity is resolved from the addresses provider; the actual EIP-1967 Pool implementation is recorded and checked. Account totals and health factor must agree exactly (at most one HF wei of rounding tolerance).

## Financial validation and limitations

PASS: normal-mode Aave account with WETH collateral and USDT debt, exact health-factor agreement with Pool.getUserAccountData; empty Aave account; native balance; block consistency and reorganization check; source and oracle identity; feed timestamps; current capped USDC/USDT price formula; read-only WETH and WBTC withdrawal calls and gas estimates. A real WETH/WBTC/USDC/USDT account independently agrees with Pool collateral, debt and health-factor totals; both WBTC component-feed rounds and adapter bytecode identity are retained.

PASS: independent arithmetic cases for mixed liquidation thresholds, USD/token decimals, ceil debt valuation, weighted-numerator health factor, simultaneous collateral/debt shocks, no-debt state, repayment versus supply, budget and balance constraints, insufficient native ETH, stale data and invalid modes. Separate-position allocation is tested using explicitly hypothetical fixtures.

SUPPORTED: Ethereum Aave V3 normal mode; current WETH direct, USDC/USDT capped and WBTC composite oracle adapters. Repayment uses variable debt; supply modeling only adds an existing enabled collateral reserve. Withdraw/borrow previews are limited to discovered assets and checked by RPC. Oracle timestamps are checked against bounded freshness assumptions (WETH and WBTC BTC/USD component 70 minutes; stable feeds and WBTC/BTC ratio component 25 hours). Governance upgrades or changed sources require revalidation. Stress scenarios override snapshot prices and do not forecast the future cap, interest or market state.

UNSUPPORTED: eMode, isolation, stable debt, other unvalidated oracle wrappers, other Morpho markets, Compound, other chains, swaps, bridges, new collateral enablement, arbitrary contract safety/MEV detection, multi-step transaction forks and automatic execution. Live combined discovery reads Aave and the pinned Morpho WBTC/USDC 86% LLTV market at one block. Other Morpho markets are not discovered.

PASS: Morpho bigint accrual exactly matches actual contract execution across six recorded markets; the maximum WBTC collateral withdrawal succeeds while one extra base unit reverts as unhealthy. The pinned V1 oracle validates three feed identities/rounds, bytecode, vault/sample, 8/6 token decimals, scale 1e26 and exact integer price. Morpho health uses native loan units and ceiling debt with virtual assets/shares. Share-based repayment updates market and borrower shares before recomputing remaining debt. Combined planning reconciles shared wallet balances and budget prices while keeping protocol risk independent. Captured evidence is in certification-reports/morpho-*-reference.json; seven independent production checks also pass.

SUPPORTED Morpho coverage is exactly Ethereum market 0x3a85e619751152991742810df6ec69ce473daef99e28a64ab2340d7b7ccfee49 (WBTC/USDC, 86% LLTV). Read-only repay, collateral supply/withdraw and borrow calls retain balance/allowance/gas constraints. Each transaction action is previewed separately; a multi-action sequence is not a state fork. Production receipt d37be8e6-51f2-47d1-880d-47584c814c46 retains two real protocol positions and a -10% WBTC, target 1.00, zero-cost baseline. It is a modeled comparison for a public reference wallet, not a recommendation.

Defense Frontier enumerates 5% budget increments and at most two actions per alternative (maximum 12 eligible action types), plus a zero-cost no-action baseline when the target is already met. It compares least capital found to meet a target or highest minimum health found. Leading candidates and action-type representatives are returned. There is no claim of global optimality. Outcomes remain MODELED_ONLY; approval, supply/borrow caps, liquidity and protocol execution constraints need the GasGuard preview. Native gas affordability is checked against the user-assumed fee reserve when a validated WETH price exists; otherwise it stays unknown. The fee reserve is not represented as a measured gas cost.

Live WBTC stress receipt aa27aad0-aa60-4cd7-b2da-27b3ff9be55c was saved and retrieved through the existing account after RLS hardening. It retains a -10% WBTC scenario, $25,000 budget, target HF 1.20, $2 assumed fee reserve, both oracle-feed rounds and five alternatives. The leading modeled repayment reaches HF 1.217 with approval still required; it is not execution evidence or a recommendation.

## Data, security and rollback

The new migration is additive. No existing users, tables, sessions, records, credentials or default grants are removed. New quota and report tables enable RLS and deny anon/authenticated table access. The existing authenticated API filters reports by auth.user.id; writes require the existing CSRF check. Save requests recompute live receipts from fresh server evidence rather than accepting client portfolio numbers. Twenty reports per account are enforced atomically with a database advisory lock. Reports contain public financial addresses and should be exported deliberately.

PASS: database quota returns [true,true,true,true,false] for five requests to the same wallet/minute; direct anon report read and authenticated save RPC are denied. Quota outage fails closed before RPC. Request sizes and decimal inputs are bounded; no RPC URL is supplied by clients.

RLS hardening is applied to all 19 previously unprotected legacy tables. There are zero public tables without RLS, and no client grants were widened. Existing rivexis_app users/data_sources access is preserved through role-specific server policies; table ownership and data remain unchanged. Live counts remain 4 users, 4 workspaces, 25 analyses and 4 legacy reports. PostgreSQL CI exercises runtime reads and denied direct client reads; the production MCP cannot impersonate rivexis_app, so that direct production role-switch test is BLOCKED, not PASS. Production effective-grant/catalog checks, authenticated account access and retained history pass. Outstanding findings: pg_net remains in public and leaked-password protection remains disabled. Nineteen owner/service-only tables intentionally have RLS with no client policies (advisor INFO). Existing build-tool GHSA-vfj7-8cjw-p6xm remains covered by the repository's narrow exception; no other high/critical advisory is accepted. No secrets found by the repository scanner. An independent security audit is not claimed.

Rollback: redeploy baseline tag baseline/pre-defi-transformation-20261009 to rivexis-web; restore captured API v11 files if necessary, retaining the additive schema. Git history and a full-history local bundle preserve recovery. Cloudflare's pre-release Worker version is a3fa1dea-608e-480e-95b0-0db01efc8573. No default-branch reset or force push.

## Test evidence

- PASS: 39 model/API/oracle boundary and captured-reference tests.
- PASS: 29 retained Edge/role/membership/report/email-template tests (fixtures, not proof of email delivery).
- PASS: 29 selected browser tests, including bounded monitoring and zero-cost current-state comparisons. Includes login/signup/verification/recovery UI, session/CSRF/logout, tenant scope, history/save operations, exports and browser headers.
- PASS: 320, 375, 390, 768, 1024, 1280, 1440 and 1920px home/sample-frontier overflow checks.
- PASS: axe serious/critical WCAG-tagged checks on public/app/auth/methodology dark surfaces and light app. This is automated coverage, not comprehensive accessibility certification.
- PASS: web typecheck/AST lint, existing API-edge typecheck, Next production build and Cloudflare/Vinext bundle build.
- PASS: preserved production cookie session, real wallet lookup, canonical server-recomputed report save and owner-scoped report retrieval through the live browser.
- UNVERIFIED: new verification-email/inbox delivery and recovery-email receipt. Brevo account, sender and template reads returned internal connector errors in three attempts. No delivery success is inferred from earlier reports or tests.
- UNVERIFIED: paid-provider capacity, statistical financial forecasts, regulatory certification and independent protocol/security audit.

## Cost model and operational limits

Supabase organization plan verified free. No new paid service, AI dependency, account or permanent project was created, and no paid plan was activated. Cloudflare account/Worker identity is unchanged; billing/subscription reads returned 403 with existing OAuth scopes, so current Cloudflare plan and total charges are UNVERIFIED. Free allowances are shared with existing workloads, so zero total cost is not guaranteed. The earlier Cloudflare-connected build failure has cleared: subsequent existing-integration builds and deployments for 313dba2, 4c59961 and fc384ac pass. No account or integration configuration was replaced.

Distributed beta cap: 300 RPC-backed attempts/day globally, 4 per wallet/minute. Each snapshot uses typically 9–15 RPC round trips for supported four-asset snapshots with bounded multicalls (up to 80 reserves); a transaction preview adds call/estimate/fee/nonce/reorganization checks. That bounds accepted analysis to about 9,000 attempts/month and roughly 135,000 snapshot RPC method calls/month for that typical case before provider failures, with no SLA. Larger unvalidated reserve sets can require additional multicall chunks; total RPC method usage is not independently metered. PublicNode publishes free Ethereum access; commercial reliability and abuse limits are not contractually guaranteed. Provider failure returns UNKNOWN.

Quota writes are roughly two upserts per accepted attempt and a bounded expiry cleanup. Only recent wallet-minute counts and daily counters persist. Account reports are <=100KB each, <=20/account; storage still grows with accounts and must be monitored. Optional browser monitoring stops after five checks, every two minutes, on view closure/hidden tab/provider failure/quota exhaustion. It is not a background service or an email liquidation-alert guarantee. Auth/email and other existing endpoints are outside the new RPC cap and retain their existing limits.

Oracle prices display all eight USD decimals. Token balances retain up to eight decimals; positive smaller amounts show a less-than bound instead of zero. Full native-unit values remain in receipts.

## Design tokens

Dark: background #141B1D; surface #1C272A; elevated #223034; inset #172124; primary #326C6A; soft #80AAA1; pale #C8DED9; primary text #E9EBE7; secondary #B8C3BE; muted #A4B0AB; bronze #B5A383; border #303E40; strong border #465355.

Light: background #F3F3EF; surface #FAFAF7; elevated/inset #E9ECE8; primary text #202B2D; secondary #475656; muted #54635E; primary/soft #326C6A; pale #244E4D; bronze #756244 (darkened from the suggested #8A7454 after a measured contrast failure); border #D6DDDA; strong border #A7B4AE. Risk colors retain separate semantic tokens. Reduced motion is respected.

## Primary references

- Aave Pool: https://aave.com/docs/aave-v3/smart-contracts/pool
- Current GenericLogic: https://github.com/aave-dao/aave-v3-origin/blob/main/src/contracts/protocol/libraries/logic/GenericLogic.sol
- WBTC composite adapter: https://github.com/aave-dao/aave-price-feeds/blob/main/src/contracts/CLSynchronicityPriceAdapterPegToBase.sol
- RLS reference: https://supabase.com/docs/guides/database/postgres/row-level-security
- Stable price-cap adapter: https://github.com/aave-dao/aave-price-feeds/blob/main/src/contracts/PriceCapAdapterStable.sol
- Workers limits: https://developers.cloudflare.com/workers/platform/limits/
- Supabase pricing: https://supabase.com/pricing
- Free public RPC: https://www.publicnode.com/
- Dependency advisory: https://github.com/advisories/GHSA-vfj7-8cjw-p6xm

## Final operational checkpoint

PR #39 preserves exact USD display cents above JavaScript safe precision and explicit positive native/fee dust bounds. Full CI passes 39 financial/API/oracle, 29 retained Edge and 29 browser tests. Final live checks pass seven Morpho/combined cases and eight Aave/WBTC/API/source cases. A preceding RPC interruption returned HTTP 503 UNKNOWN and withheld results; an independent contract read and subsequent public checks recovered. Free RPC availability is not guaranteed. New Brevo inbox delivery and current Cloudflare billing totals remain unverified. Three explicit QA receipts now exist; existing users, workspaces, 25 analyses and four legacy reports remain unchanged.
