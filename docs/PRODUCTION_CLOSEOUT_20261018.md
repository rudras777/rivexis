# RIVEXIS engineering and launch record

18 October 2026, Asia/Calcutta. Existing production URL: https://rivexis-web.rudrasingh0718.workers.dev/ . No new site, permanent project, cloud account, paid service or branding suffix.

**Decision: READY FOR CONTROLLED EARLY ACCESS** within the documented Ethereum lending scope and beta quotas. **Not certified for unrestricted institutional public launch.** The application release is implemented, merged, deployed and independently verified; resource/assurance gates remain below. This is engineering evidence, not a financial/security audit certification.

## Implemented release

PR86: https://github.com/rudras777/rivexis/pull/86 . Source commit cac261507ae154f83762c9f57d7ccfd6017a889c.

Verified production merge commit **31a52fd130ab8419d32900177f519c2095d0d9ff**, source/merge tree **0cb7ff916da0a48ad3b9fd221c40970e5333c5db**. Existing Worker **82e0659a-ef96-42e0-b89a-fc9bd6eebef7**, Ready at 100% traffic. Native Cloudflare build **57e7f03d-0781-49c8-add4-bc67f848d834** succeeded; read-only Wrangler deployment listing independently confirmed the active 100% version. Public HTTP returned 200 with the exact build marker; genuine authenticated DOM exposed the same marker. Previous Worker 690c9111 remains available for rollback. No API redeployment or database migration was needed.

All release runs passed: source CI **39063711924**, PR CI **39063732796**, PR Worker checks **39063732832**, main CI **39064110217**, main Worker checks **39064110221**. The existing GitHub integration also reports success; the actual native Cloudflare build link and public build marker are the Worker evidence.

Fixed indefinite wallet waiting and later permission requests after local cancellation/logout in both the global wallet connection and Settings. A shared 35-second total deadline checks current identity between chain/address/chain requests, ignores late approvals, and releases controls. Dialog close, Escape, Settings exit/unmount and logout stop waiting. Retry is explicit; a wallet's already-open permission prompt cannot be withdrawn locally and the UI says so. No signature, approval transaction, automatic network switch or transaction submission was added.

The approved logo, colors, public layout, shared animated background, institutional top navigation and authentication requirements remain. The floating bottom-right Pause control was already removed; accessible motion preferences remain. Contract evidence/input continuity was audited and its existing busy locks/address and ABI evidence resets were correct. No financial or database source changed in this release.

## Verification evidence

| Check | Result and scope |
| --- | --- |
| New wallet unit tests | 18 passed; stalled stages, cancellation, late approvals, shared deadline, invalid account/network, rejection and explicit retry |
| New focused browser cases | 12 passed without retries; both wallet surfaces, close/Escape/logout/navigation/forget and delayed provider responses |
| Full local browser regression | 184 passed, zero skipped, failures or flaky cases; 217.9 seconds |
| Financial/backend regression | 221 DeFi tests and 30 API-edge tests passed; controlled RPC/database/identity fixtures are explicitly separate from live evidence |
| Builds/types/source checks | Next and Vinext production builds, TypeScript, frontend AST, repository invariants and secret-pattern scan passed |
| Local migration check | System Python lacks Alembic; actual isolated migration/PostgreSQL CI job is the required replacement evidence, not a claimed local pass |
| Local performance | Two checks at fourfold CPU passed; desktop LCP 992ms/CLS 0.033, mobile LCP 292ms/CLS 0.104. No overflow/browser errors/canvas drawing. Mobile layout shift remains an improvement item; these are local observations, not field/SLA certification |
| Dependency security | Existing narrow GHSA-vfj7-8cjw-p6xm Vinext build-chain exception remains. Ordinary npm audit reports seven high entries in that chain. The advisory gate passes with this explicit exception; the audit is not clean |
| Actual public deployment browser checks | **26 passed**, zero failures/skips/flaky cases, no retries, 85.5 seconds; exact commit, authentication/API gates, recovery/confirmation token scrubbing, accessibility, responsive navigation and background/motion controls |
| Production lab performance | Two checks passed at fourfold CPU: desktop LCP 2064ms/CLS 0; mobile LCP 2060ms/CLS 0. No overflow/browser errors. These single-run public-site measurements do not establish field Core Web Vitals, load capacity or uptime |
| CI database/security | Actual Ubuntu Alembic upgrade/downgrade/schema parity, isolated PostgreSQL migration/RLS/distributed controls/restore fixtures passed. Python dependency audit reported no known vulnerabilities. These do not replace the separate production database recovery drill |

Fresh genuine authenticated checks on this release: market observations/automatic block refresh; wallet dialog honestly reports absent injected provider; existing saved WETH contract inspection at block **26214489** observed 3124 code bytes and bounded decimals read **18** at **26214490** without saving changes; Morpho inspection at **26214492** produced real lending exposure. Exported planner receipt examined 59 allocations; all **six** alternatives and baseline exactly matched separate Python integer arithmetic with no application imports. Unrounded rational costs plus assumed fees were independently checked within budget as well as matching the model's per-token 1e-8 USD floor convention. The requested target was honestly unmet.

Settings loaded the genuine verified QA identity and all ten sections. Its browser-wallet selector immediately disclosed that no provider was available, remained enabled, and saved no address. The owner-bound report list loaded four existing comparisons without creating or deleting data. This verifies the absent-provider path; it does not certify a native wallet grant. Current-session and preference data were preserved. Fresh login/signup/recovery email sending was not repeated during this wallet-only release; dated earlier genuine delivery evidence remains separate.

Selected Morpho sequence at parent **26214501**, simulated next block **26214502**, succeeded in all three steps: reset allowance, exact approval and supply **3,659,207 raw WBTC units**. Independent reference checks matched both raw debt/health states, wallet/collateral delta, approval amount and 132,065 action gas total. Provider validation was true; state/block overrides false. No signing or submission. When the original snapshot aged beyond three minutes, calculations/alternatives were withheld; refresh at **26214509** restored calculation. Individual GasGuard at **26214513** honestly returned BLOCKED for insufficient allowance and failed call/gas estimate, with unknown fees and modeled health preserved. This is successful blocker handling, not a successful individual transaction call. The approval-inclusive sequence is the separate genuine successful simulation evidence.

Raw artifacts outside the repository: `wallet-lifecycle-full-browser-results-20261018.json`, `wallet-lifecycle-live-browser-results-20261018.json`, `pr86-ci.log`, `pr86-main-ci.log`, production performance JSON/PNGs, three downloaded live receipts, `check_live_planner_20261018.py`, and planner/sequence reconciliation JSON. Screenshots include `cloudflare-31a52fd-production-20261018.jpg` and the production market/contract/sequence/GasGuard views. No credentials or recovery keys belong in this public report or GitHub.

Full scenario matrix in repository: `docs/WORKFLOW_SCENARIO_COVERAGE.md`. Nine groups each contain ten or more realistic scenarios: LiquidationGuard, GasGuard, Defense Planner, market charts, wallet access, contracts/networks, authentication/navigation, Settings and reports/history. Multiple inputs within a named test are not misrepresented as separate named test totals. Injected wallet fixtures do not certify real native permission UI.

## Supported product and financial scope

- LiquidationGuard: Ethereum Aave V3 normal mode and validated bounded Morpho WBTC/USDC 86% LLTV; raw quantities, protocol-specific accounting, pinned blocks, oracle freshness and honest unsupported states.
- GasGuard: supported individual and bounded selected-strategy sequences, fees/balances/allowances, before/after effects and truthful blocked/unknown outcomes. No custody, hidden signing or execution.
- Defense Planner: capital/fee/balance-constrained alternatives, risk objective, shared wallet capital across independent liquidation domains and reproducible receipts. Search uses a bounded 5% grid and at most two actions, with no global-optimum/safety/execution guarantee.
- Real prior Aave (12 RPC scenarios) and bounded Morpho (eight RPC simulations plus four guards) sequence observations and five independently reconciled planner alternatives remain timestamped financial evidence. This release additionally checked the six fresh alternatives and successful single-supply sequence recorded above; it did not rerun the entire historical RPC scenario set or commission an independent financial audit.
- Market charts show real Chainlink/public Ethereum observations, bounded history, accessible tables, freshness and retry states. Historical gaps and unavailable 24h changes remain explicit. Browser-visible polling is not a continuous server tick database or guaranteed provider SLA.
- Authenticated Settings, owner-bound JSON reports, public-address wallet analysis, bounded contract/ABI reads, account/session handling and top navigation retain their supported workflows. Native wallet names/permissions remain provider controlled; contract code or ABI decoding is not source verification or safety certification.

Obsolete B1–B5/F1–F5 product interfaces and fragmented navigation were retired in earlier transformation releases. Reusable backend/security source and rollback history remain. No production users or data were removed by this release.

## Infrastructure, security and recovery

Existing GitHub repository, rivexis-web Worker/URL, Supabase project/authentication/data and Brevo integration retained. API34 is unchanged. Bounded beta quota remains 300 analysis requests/day globally and four/wallet/minute, enforced atomically; there is no in-memory quota bypass. No paid AI dependency. Added recurring service cost: **$0**. Total account billing/indefinite free-tier capacity is not certified.

Latest recorded production database audit: 61 public ordinary tables with RLS, none without; nine public security-definer functions, none executable by anon/authenticated. Existing pg_net-in-public and disabled leaked-password-protection warnings remain. Production PostgreSQL maintenance/current-version assurance remains a controlled operation; no database upgrade, extension removal, privilege widening or paid plan change was performed. No clean penetration-test certification is claimed.

Actual production logical recovery drill exported read-only with verified TLS and restored an isolated matching Supabase PostgreSQL instance. All 102 archived datasets/27,667 rows reconciled, including logical Vault recovery under a new isolated key. A portable authenticated encrypted kit was copied to the owner's private connected Drive and downloaded/hash/decryption-verified. The key was kept separate. Temporary access was revoked. This is not second-machine/full-service recovery or automated RPO/RTO certification.

## Remaining gates and next safe steps

1. Supply an existing owned sending domain/DNS authority; authenticate it in the current Brevo account and retest verification/recovery delivery. Existing delivery works, but signup verification was observed in Spam and inbox placement is not guaranteed.
2. A human configures/unlocks a real test wallet and handles protected permission steps; then verify native acceptance/rejection, pending requests, account/network changes, disconnect and permission removal. No private keys/seed capture/signing.
3. Place the recovery key in an approved independent owner-controlled destination, separate from the encrypted kit; perform second-machine and broader service/configuration recovery, retention and operational recovery objectives.
4. Resolve documented database/auth and dependency findings through controlled supported maintenance; independently assess institutional financial/security/operational assurance and sustained provider/load behavior.

These cannot be replaced with fabricated success messages, a new account, a paid upgrade or unsafe production mutation. There is no request to type “continue”; the checkpoint names exact remaining resource-dependent work.
