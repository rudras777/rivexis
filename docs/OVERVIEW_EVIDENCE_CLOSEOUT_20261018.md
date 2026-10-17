# Overview and market evidence release closeout

18 October 2026, Asia/Calcutta. Existing production URL: https://rivexis-web.rudrasingh0718.workers.dev/ . Approved design, infrastructure and financial logic retained.

## Released application

[PR87](https://github.com/rudras777/rivexis/pull/87) merged source `f597a949b67812127779acd3b57a24dc171ebfd4` as **6c5623909f9d25099cea3042c4d01bb24bde8b44**. Existing Worker **cceee7cf-1d18-4e05-be28-a5fa9974a25a**, native build **f98c8810-d968-4f53-a10f-6b2df3ab1746**, is Ready with 100% configured allocation. Dashboard and read-only Wrangler listing agree; the previous PR86 Worker remains available for rollback. Public HTTP and genuine authenticated DOM expose the exact merge marker. API34 and the production database were unchanged.

Retained Overview metrics now disclose snapshot age and become stale after 180 seconds. Invalid/unsupported timestamp evidence is withheld; historical and educational values retain their classification. Samples do not fabricate an on-chain block. Aging adds no financial RPC. Market quotes say “Latest quote not reverified” when the associated block observation exceeds 90 seconds, retaining genuine history and retry behavior. No calculation, provider, quota, account, branding, CSS or layout changes.

## Test evidence

| Check | Actual result |
| --- | --- |
| New Overview cases | 16 passed; no inspection, fresh/zero/stale, invalid/future time, unsupported, historical/sample, route return, aging without another financial read, accessibility/no overflow at 320/768/1440px |
| Focused market and Overview regression | 35 passed, zero failures/skips/retries/flaky cases, 52.1 seconds |
| Source and PR CI | 39065915702 and 39065919315 succeeded on final source; Worker validation39065919335 succeeded on attempt2 |
| Main CI | [39066406169](https://github.com/rudras777/rivexis/actions/runs/39066406169) succeeded: 200 browser cases, 221 DeFi, 30 API-edge, 10 sequence fixtures, 21 market-feed, 12 client API, 18 wallet lifecycle unit tests, Python/security/PostgreSQL checks |
| Main Worker validation | [39066406110](https://github.com/rudras777/rivexis/actions/runs/39066406110) succeeded; actual Cloudflare native build independently succeeded |
| Actual public browser checks | 26 passed in 79.7 seconds, zero failures/skips/flaky cases/retries; build identity, mandatory auth/API gates, token scrubbing, navigation, responsive/accessibility/background/motion controls |
| Public performance | Two additional checks at fourfold CPU; desktop LCP1740ms, mobile1812ms, CLS0 for both; no overflow or browser errors. Single-run lab measurements, not Lighthouse, field metrics, load capacity or uptime certification |
| Builds/source | Next and Vinext builds, TypeScript and frontend AST passed |

The first strengthened hidden-tab recovery assertion failed because its mock used the Node clock while the browser advanced 125 seconds. Fixture RPC timestamps now use the same browser clock; the age/recovery assertions remain. The first failure and corrected 35-case JSON/logs are preserved outside the repository. Controlled fixture cases are not represented as real provider observations.

## Genuine authenticated follow-up

The existing QA workspace inspected the supported public Morpho reference at **block26214750**. Overview showed **$9,882,336.31 collateral**, **$6,826,428.64 debt**, the identical source block and **18 seconds** of age. Market context independently refreshed: block26214761, real oracle history increased from three to four points, and fee history reached16 observations. Retained market evidence initially showed “Latest quote not reverified” while its block was stale, then recovered to fresh after a real observation. No provider failure or clock was injected into this production session.

Actual elapsed-time verification observed age148 seconds, then178 seconds, then all three cards changed to **“Stale snapshot · refresh in LiquidationGuard”** after the three-minute boundary, preserving the original balances and block26214750. No extra financial read was made to age those cards. The financial workspace also withheld scenario/action calculations until refreshed. Explicit refresh returned **block26214768**, debt **$6,826,430.92** with newly accrued raw debt6827452.995736 USDC, preserving collateral121.42747912 WBTC. The observation chart gained its second actual point. Overview then replaced the old evidence block and debt and restored the observed-snapshot classification.

The financial receipts from PR86 retain their original dated scope: six planner alternatives/baseline and a successful approval-inclusive Morpho supply simulation independently reconciled against raw integer arithmetic. PR87 did not alter financial models or recertify arbitrary markets.

A default Python-urllib HTTP probe was rejected by Cloudflare1010/403. The identified `RIVEXIS-release-check/1.0` HTTP probe returned200 with the exact deployment marker at20:48:37Z; real-browser checks also passed. No Cloudflare security rule was changed or weakened. This distinction is retained in the local release manifest.

## Remaining boundaries

Decision: **READY FOR CONTROLLED EARLY ACCESS**, not unrestricted institutional certification. Existing owned email domain/DNS authority, human-controlled native wallet permissions, independent key custody/second-machine/full-service recovery, and controlled security/operational assurance remain gates. Brevo delivery works but Spam placement was observed. No new spending, credentials, permissions, signing or destructive actions were introduced.

Final genuine resource check: the existing Cloudflare account's Domains inventory displayed **No data available**, with no search filter entered. The account has the retained web/API Workers, but no existing DNS zone for sending-domain authentication. Brevo still offers domain setup. No domain purchase/addition, account switch or DNS/SMTP change was made. This verifies the missing resource; it is not a request to repeat credentials already available. The local domain-inventory screenshot preserves the result without placing account screenshots in the public repository.

Fresh Supabase advisors retain extension-in-public and leaked-password-protection WARN groups plus19 intentionally private RLS-without-policy INFO findings. The [braces advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) lists no patched version; the existing narrowly scoped build-tool exception remains, with no clean-audit claim. Supported Ethereum Aave normal mode/bounded Morpho scope, bounded 5% planner grid/max two actions, public-provider availability/history limitations and atomic300/day global plus4/wallet/minute beta quotas remain. Added recurring services cost **$0**, not a guarantee of indefinite free capacity or total account billing.

Raw evidence outside the repository: `overview-evidence-release-proof-20261018.json`, `pr87-main-ci.log`, `pr87-live-browser-results-20261018.json`, per-device PR87 performance JSON, `evidence-freshness-focused-results-20261018.json`, original fixture-clock failure JSON, and genuine production/deployment screenshots. Recovery keys, decrypted archives and private account records are excluded. This documentation checkpoint does not initiate another application deployment merely to change its own commit reference.
