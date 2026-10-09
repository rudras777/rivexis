# RIVEXIS — DeFi risk platform release evidence

Release state: the redesigned bounded beta is LIVE at https://rivexis-web.rudrasingh0718.workers.dev. Final deployed source is e42fd2a22721c26b73756c48c2ae906e1ed04674; Cloudflare Worker version 30481780-7781-4ff9-bdd9-1d45c76ece10; existing Supabase API v16 ACTIVE. Final main CI 37945178364 passed all four jobs. Independent public verification matched this source identity, exact on-chain health factor and read-only transaction simulation. Authenticated browser verification confirmed the existing session, saved receipt and zero-cost current-state baseline. See TRANSFORMATION_PROGRESS.md and certification-reports/defi-live-verification.json.

## Architecture and feature inventory

- KEEP: existing Cloudflare Worker/account/domain, Supabase project and identity, secure-cookie/CSRF auth, tenant bridges, retained analyses/reports, Brevo configuration and alert delivery infrastructure.
- REFACTOR: public website, shared theme, authenticated navigation, portfolio state, reporting, transaction intelligence and risk calculations.
- RETIRE: B1–B5/F1–F5 public engine forms, ten-engine navigation, generic entity/security/bridge/yield/treasury dashboards and fragmented marketing pages. Old URLs redirect; historical records and reusable backend source remain.
- REMOVE: six competing CSS override layers from the active source. Existing wordmark/lockup shapes are retained and recolored with a shared CSS filter; the new teal X SVG favicon is served from the same Worker. Original PNG sources remain recoverable.
- ADD: anonymous wallet lookup; LiquidationGuard block-pinned discovery; per-asset Scenario Lab; Defense Frontier; GasGuard previews; owner-scoped risk receipts; JSON exports; optional five-check in-browser monitoring.

The same bigint/fixed-point module serves frontend scenarios, server-generated account reports and server-side action consequences. Aave state is read from Ethereum through bounded RPC multicalls. Deployment identity is resolved from the addresses provider; the actual EIP-1967 Pool implementation is recorded and checked. Account totals and health factor must agree exactly (at most one HF wei of rounding tolerance).

## Financial validation and limitations

PASS: normal-mode Aave account with WETH collateral and USDT debt, exact health-factor agreement with Pool.getUserAccountData; empty Aave account; native balance; block consistency and reorganization check; source and oracle identity; feed timestamps; current capped USDC/USDT price formula; read-only WETH withdrawal call and gas estimate.

PASS: independent arithmetic cases for mixed liquidation thresholds, USD/token decimals, ceil debt valuation, weighted-numerator health factor, simultaneous collateral/debt shocks, no-debt state, repayment versus supply, budget and balance constraints, insufficient native ETH, stale data and invalid modes. Separate-position allocation is tested using explicitly hypothetical fixtures.

SUPPORTED: Ethereum Aave V3 normal mode; current WETH direct and USDC/USDT capped oracle adapters. Repayment uses variable debt; supply modeling only adds an existing enabled collateral reserve. Withdraw/borrow previews are limited to discovered assets and checked by RPC. Oracle timestamps are checked against bounded freshness assumptions (WETH 70 minutes; stable feeds 25 hours). Governance upgrades or changed sources require revalidation. Stress scenarios override snapshot prices and do not forecast the future cap, interest or market state.

UNSUPPORTED: eMode, isolation, stable debt, WBTC composite and other unvalidated oracle wrappers, Morpho, Compound, other chains, swaps, bridges, new collateral enablement, arbitrary contract safety/MEV detection, multi-step transaction forks and automatic execution. Multi-position mathematics is validated, but live discovery currently covers one Aave account; no production multi-protocol claim is made.

Defense Frontier enumerates 5% budget increments and at most two actions per alternative (maximum 12 eligible action types), plus a zero-cost no-action baseline when the target is already met. It compares least capital found to meet a target or highest minimum health found. Leading candidates and action-type representatives are returned. There is no claim of global optimality. Outcomes remain MODELED_ONLY; approval, supply/borrow caps, liquidity and protocol execution constraints need the GasGuard preview. Native gas affordability is checked against the user-assumed fee reserve when a validated WETH price exists; otherwise it stays unknown. The fee reserve is not represented as a measured gas cost.

## Data, security and rollback

The new migration is additive. No existing users, tables, sessions, records, credentials or default grants are removed. New quota and report tables enable RLS and deny anon/authenticated table access. The existing authenticated API filters reports by auth.user.id; writes require the existing CSRF check. Save requests recompute live receipts from fresh server evidence rather than accepting client portfolio numbers. Twenty reports per account are enforced atomically with a database advisory lock. Reports contain public financial addresses and should be exported deliberately.

PASS: database quota returns [true,true,true,true,false] for five requests to the same wallet/minute; direct anon report read and authenticated save RPC are denied. Quota outage fails closed before RPC. Request sizes and decimal inputs are bounded; no RPC URL is supplied by clients.

Outstanding findings: pg_net remains in public; leaked-password protection remains disabled; 19 legacy tables have no RLS but no anon/authenticated grants were found, and users SELECT is denied. The two new service-only tables intentionally have RLS with no client policies (advisor INFO). Existing build-tool GHSA-vfj7-8cjw-p6xm remains covered by the repository's narrow exception; no other high/critical advisory is accepted. No secrets found by the repository scanner. An independent security audit is not claimed.

Rollback: redeploy baseline tag baseline/pre-defi-transformation-20261009 to rivexis-web; restore captured API v11 files if necessary, retaining the additive schema. Git history and a full-history local bundle preserve recovery. Cloudflare's pre-release Worker version is a3fa1dea-608e-480e-95b0-0db01efc8573. No default-branch reset or force push.

## Test evidence

- PASS: 17 new model/API boundary tests.
- PASS: 29 retained Edge/role/membership/report/email-template tests (fixtures, not proof of email delivery).
- PASS: 27 selected browser tests, including bounded monitoring and zero-cost current-state comparisons. Includes login/signup/verification/recovery UI, session/CSRF/logout, tenant scope, history/save operations, exports and browser headers.
- PASS: 320, 375, 390, 768, 1024, 1280, 1440 and 1920px home/sample-frontier overflow checks.
- PASS: axe serious/critical WCAG-tagged checks on public/app/auth/methodology dark surfaces and light app. This is automated coverage, not comprehensive accessibility certification.
- PASS: web typecheck/AST lint, existing API-edge typecheck, Next production build and Cloudflare/Vinext bundle build.
- PASS: preserved production cookie session, real wallet lookup, canonical server-recomputed report save and owner-scoped report retrieval through the live browser.
- UNVERIFIED: new verification-email/inbox delivery and recovery-email receipt. Brevo account, sender and template reads returned internal connector errors in three attempts. No delivery success is inferred from earlier reports or tests.
- UNVERIFIED: paid-provider capacity, statistical financial forecasts, regulatory certification and independent protocol/security audit.

## Cost model and operational limits

Supabase organization plan verified free. No new paid service, AI dependency, account or permanent project was created, and no paid plan was activated. Cloudflare account/Worker identity is unchanged; billing/subscription reads returned 403 with existing OAuth scopes, so current Cloudflare plan and total charges are UNVERIFIED. Free allowances are shared with existing workloads, so zero total cost is not guaranteed. Source CI passes, but the pre-existing Cloudflare-connected Workers Builds check fails; the release used the existing authenticated manual Wrangler path successfully.

Distributed beta cap: 300 RPC-backed attempts/day globally, 4 per wallet/minute. Each snapshot uses approximately 9–12 RPC round trips with bounded multicalls (up to 80 reserves); a transaction preview adds call/estimate/fee/nonce/reorganization checks. That bounds accepted analysis to about 9,000 attempts/month and roughly 150,000 RPC method calls/month before provider failures, with no SLA. PublicNode publishes free Ethereum access; commercial reliability and abuse limits are not contractually guaranteed. Provider failure returns UNKNOWN.

Quota writes are roughly two upserts per accepted attempt and a bounded expiry cleanup. Only recent wallet-minute counts and daily counters persist. Account reports are <=100KB each, <=20/account; storage still grows with accounts and must be monitored. Optional browser monitoring stops after five checks, every two minutes, on view closure/hidden tab/provider failure/quota exhaustion. It is not a background service or an email liquidation-alert guarantee. Auth/email and other existing endpoints are outside the new RPC cap and retain their existing limits.

## Design tokens

Dark: background #141B1D; surface #1C272A; elevated #223034; inset #172124; primary #326C6A; soft #80AAA1; pale #C8DED9; primary text #E9EBE7; secondary #B8C3BE; muted #A4B0AB; bronze #B5A383; border #303E40; strong border #465355.

Light: background #F3F3EF; surface #FAFAF7; elevated/inset #E9ECE8; primary text #202B2D; secondary #475656; muted #54635E; primary/soft #326C6A; pale #244E4D; bronze #756244 (darkened from the suggested #8A7454 after a measured contrast failure); border #D6DDDA; strong border #A7B4AE. Risk colors retain separate semantic tokens. Reduced motion is respected.

## Primary references

- Aave Pool: https://aave.com/docs/aave-v3/smart-contracts/pool
- Current GenericLogic: https://github.com/aave-dao/aave-v3-origin/blob/main/src/contracts/protocol/libraries/logic/GenericLogic.sol
- Stable price-cap adapter: https://github.com/aave-dao/aave-price-feeds/blob/main/src/contracts/PriceCapAdapterStable.sol
- Workers limits: https://developers.cloudflare.com/workers/platform/limits/
- Supabase pricing: https://supabase.com/pricing
- Free public RPC: https://www.publicnode.com/
- Dependency advisory: https://github.com/advisories/GHSA-vfj7-8cjw-p6xm
