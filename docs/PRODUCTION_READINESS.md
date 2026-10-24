# RIVEXIS production readiness

Updated25October2026, Asia/Calcutta. **GO for the documented small, controlled public beta; unrestricted institutional certification remains unavailable.** This record supersedes stale current-status rows in earlier revisions. Dated financial, wallet, recovery and deployment evidence keeps its original scope.

## Current verified production and pending patch

PR114 is deployed at the existing [production URL](https://rivexis-web.rudrasingh0718.workers.dev/) as2b1bfcdcb54df97e0123ae3453879999ae24672d; existing Workerc809325b at100%, native build78638997-e650-4ee0-ae7d-a5ab3267b8e4 Ready. Its eight exact-head workflows pass:336 fixtures per Chromium/Firefox/WebKit,90 actual-public checks,295 financial/auth and29 strict audit-policy cases. Footer/diagram changes preserve the approved design and financial/backend/authentication source.

The [25October security review](SECURITY_REVIEW_20261025.md) adds explicit write-origin rejection and a128KiB proxy upload cap. It has separate candidate/release gates; this source record does not predeclare promotion. Use its final PR and repository progress checkpoint for exact tested source, merge, native deployment and public checks.

## Supported acceptance

| Area | Status and evidence |
|---|---|
| LiquidationGuard | Validated Ethereum AaveV3 normal mode and one Morpho WBTC/USDC86%LLTV market; pinned blocks, protocol integer arithmetic, stale/reorg/unsupported guards. Other modes/chains/markets remain unsupported. |
| Defense Planner | Shared capital/token/fee budget;5% grid/at most two actions per alternative; independent protocol risk domains and reproducible receipts. No global-optimum, safety or execution guarantee. Genuine23October receipts reconcile independently. |
| GasGuard and selected sequences | Validated individual calls and bounded same-protocol one/two-action previews, explicit allowance/balance/provider blockers, exact approvals in simulations only. No signing/submission, arbitrary or cross-protocol sequence promise. |
| Markets/charts | Genuine oracle/fee observations, gap/freshness labels, accessible tables, bounded visible-tab polling and history recovery. No invented24-hour history or continuous-server/SLA claim. |
| Accounts/Settings/reports | Verified account required; owner-filtered private reports; secure preference persistence and ten Settings sections. Existing genuine acceptance and295 failure/edge/auth-model tests remain separately dated. |
| Wallet/contracts | Real24October MetaMask existing-grant connection/reconnect and chain-change passed13 checks. Fresh consent/rejection, native account-change and provider-disconnect paths remain unverified. Bounded ABI reads and explicit unverified source/ABI remain. |
| Database protection | Fresh25October ACTIVE_HEALTHY/Postgres17.11.0.003;61 public tables/zero without RLS, zero public client-callable security definers, six sensitive tables deny direct client SELECT, no public views. No database mutation. |
| Dependencies/security | Fresh25October npm zero findings;29 strict gate tests,295 financial/auth tests and source secret-pattern check pass. New proxy hardening requires its own exact-head release. Pattern scanning is not complete secret detection. |
| Recovery |20October isolated logical restore reconciles102entries/32,179rows; approved23October owner-only encrypted copy verified. No new backup/restore/key access is part of this patch. |
| Free-first capacity | Existing shared300 analyses/day/four per wallet/minute and20 reports/account; current Worker/Supabase/Brevo retained, added recurring service costUSD0. Total billing and unlimited scale not certified. |

## Remaining limits

| Gate | Remaining work |
|---|---|
| Platform security WARNs | Existing nonrelocatable pg_net namespace warning and Pro-only leaked-password protection. No unsafe extension relocation or silent paid upgrade.19 no-policy RLS INFO findings intentionally deny client access. [Security boundaries](SECURITY.md). |
| Email assurance | Owner explicitly retained current verified sender for limited beta. Owned-domain authentication and consistent inbox placement remain uncertified; prior mail in Spam retained. No domain purchase is required for this accepted beta decision. |
| Native wallet full acceptance | Existing-grant/chain-change acceptance passed; fresh native consent/rejection/account-change/disconnect requires separate observed evidence. |
| Independent recovery | Independent key custody, second-machine/full-service reconstruction, retention/RPO/RTO remain unverified. |
| Institutional operations | Sustained field/load/provider measurements and independent security/operating review remain open. Earlier variable performance samples are retained, not replaced by an SLA. |

The [launch handoff](LAUNCH_HANDOFF_20261024.md), [genuine beta acceptance](BETA_LAUNCH_20261024.md), [operations](SUPPORTED_BETA_OPERATIONS_20261020.md) and [recovery/platform review](LAUNCH_GATES_REVIEW_20261023.md) retain details. Earlier withdrawn Braces and pre-upgrade PostgreSQL/native-wallet absence rows are historical. The24October Undici/Zod/fast-uri patch shipped in PR108; fresh zero findings supersede its initial detection. No self-test or cosmetic deployment closes the independent assurance gates above.
