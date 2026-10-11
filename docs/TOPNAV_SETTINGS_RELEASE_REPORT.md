# RIVEXIS — verified top navigation and Settings release

Existing production: https://rivexis-web.rudrasingh0718.workers.dev

Deployed commit: `7be2c1c41012ae2d8c7123383584666c97c254fd`. PR54 implemented the transformation; PR55 corrected Supabase-prefixed account routing discovered during authenticated production verification. No new website, repository, Worker, Supabase project or paid service was created.

## Delivered

All authenticated pages use the shared horizontal header, five product destinations, responsive mobile menu and account menu. The feature sidebar and public theme toggle are removed. Shared controls use the approved Obsidian/Graphite/Teal/Ivory/Champagne palette, Geist typography, consistent hover/focus/disabled states and reduced motion. Repetitive promotional Free/Read Only badges were removed; accurate security and execution disclosures remain. Existing landing composition, vector logo, depth/cursor effects and mandatory verified authentication are retained.

| Settings section | Supported behavior |
|---|---|
| Profile | Validated display name, verified email/account facts; preserves unrelated metadata |
| Appearance | Account-persisted Dark/Light/System and density; appearance-only device cache |
| Security | Retained secure recovery entry and truthful security information |
| Sessions | Current-browser logout; explicitly confirmed other-refresh-session revocation, with JWT-expiry disclosure |
| Connected Wallets | Ethereum address selection without signatures; up to five public analysis addresses; copy/remove/default ordering |
| Notifications | Existing essential verification/recovery delivery; truthful unavailable risk-email state |
| Financial Preferences | Grouped USD totals, health-factor precision/timezone, protocol/budget/target/fee/objective defaults for empty analyses |
| Accessibility | Device-aware/reduced motion, higher contrast, larger interface text, keyboard tabs/focus |
| Privacy | Owner profile/preferences and up to20 saved risk receipts exported; selective appearance-cache clearing |
| Account Management | Preserved authorized workspace/organization controls at /workspace/settings/workspaces |

Preferences never authorize access. API ownership comes from the validated cookie session; verified email and CSRF gates are retained. Unknown fields, privileged claims, inconsistent decimal budgets and oversized bodies fail closed. Existing analyses and exact financial values remain intact when display/default preferences change. Sample loading now respects the selected authenticated route.

## Release evidence

- 78 financial/API/auth/account tests, including the actual Supabase-prefix Edge routing regression;30 retained backend/report/email tests pass.
- 66 full browser tests pass locally (110.46seconds), in PR54/55 CI and final main CI. No failed/flaky/skipped tests reported. Four additional control cases extend Settings QA to14 passing targeted tests (15.7seconds): clipboard/default addresses, unsupported network rejection, Settings logout/CSRF and Light-theme accessibility/USD grouping. These test-only additions are on the evidence branch.
- Nine real production guest tests pass against the exact final commit (40.96seconds), without mocks or retries. Settings and financial routes/APIs withhold guest access.
- Next/Vinext builds, types, AST, Deno, secret scan, invariants, PostgreSQL/RLS migration certification and both Worker dry-run jobs pass. Final main CI38135146621 and Worker checks38135146710 succeed.
- Cloudflare native build `d36b1c44-7e05-4b19-8a1c-c94448c57ce4` is Ready/SUCCESS for7be2c1c. Existing Worker rivexis-web receives100% traffic on version `d231f92c` (dashboard abbreviation; full UUID not captured). Existing commands/root/token retained.
- Existing Supabase API26 ACTIVE, SHA256 `b79b9991735a1bd2697db110c9363abab99bc71fa827b1fe3328c418663dfba8`; all20 deployed source files match the prepared source. The17 pre-existing runtime dependencies, including financial models, remain unchanged from API24. Existing custom cookie authentication configuration is preserved.
- Real authenticated Settings GET/PATCH succeeded; Light survived a reload; System saved; original Dark restored. Live mobile375px layout fits with no document overflow; default viewport restored. Account-menu/mobile navigation and saved-report loading verified. No other-device session revocation or real wallet permission grant was performed.

## Financial and export verification

Fresh Aave block26168888: observed health1.625; −20%WETH scenario1.300. The bounded planner examined20 allocations; a2000USDT repayment modeled health1.500 and a target-reaching alternative, with modeled capital/assumed fees$2023.05. Alternative2 handed1935.636916USDT to GasGuard and modeled stressed health1.493, correctly below target.

Fresh GasGuard block26168897, nonce73, returned BLOCKED: allowance insufficient; eth_call/gas estimation unverified, gas/fee unknown. Current-oracle modeled health before1.625/after1.866 differs from the hypothetical stressed planner domain. No approval, signing or transaction submission occurred. The three-minute freshness gate was independently observed withholding new calculations; refresh succeeded at26168909.

Independent Decimal arithmetic from displayed token/oracle inputs reconciles health1.625, stress1.300, repayment1.500/1.493 and the$1535.4975 conditional WETH threshold. This is a display-level reconciliation because displayed collateral is truncated; exact base-unit/protocol/reference tests are separate and passing. Coverage remains Ethereum Aave normal mode and one validated Morpho WBTC/USDC86%LLTV market. Search is bounded, not a proof of global optimality or safety. Independent transaction calls do not certify multi-action execution.

The actual live account export downloaded to the existing Downloads folder:61,615bytes, SHA256 `cbe2712db7a1b95ae65d7c63ea69be879c163518cba495cacef6023143116c2f`. Its four historical live receipts reproduce their stored alternatives exactly and repeated canonical results are deterministic. No authentication-secret keys are present. Raw private profile/receipt data was not committed or published; the output reproduction audit is sanitized. This resolves the earlier native download/canonical-reproduction verification gap.

## Infrastructure, security and limits

No user or production record deleted; no schema migration, dependency addition, plan upgrade or new recurring service. User access remains without payment. Last direct provider-plan evidence (Oct10) recorded Cloudflare Workers Free, Supabase Free and Brevo Free; no plan/account settings changed in this release. Additional paid services:$0. Future unlimited traffic or zero charges are not guaranteed;300global live-RPC operations/day,4/wallet/minute and20reports/owner remain enforced.

Public tables without RLS:0. Existing server-only/no-policy tables remain denied to ordinary clients. Existing advisories remain: [pg_net in public](https://supabase.com/docs/guides/database/database-linter?lint=0014_extension_in_public) and [leaked-password protection disabled](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection). The unchanged narrow npm exception covers the unpatched build-tool braces advisory GHSA-vfj7-8cjw-p6xm; other high/critical findings fail CI. No new critical finding was identified by this release's checks; this is not a comprehensive security certification.

Unsupported self-service MFA/email changes/account deletion and automated DeFi emails remain explicitly disclosed. Session revocation was tested through actual Edge routing/provider stubs, not against the user's active devices. Fresh owner-inbox signup/verification/recovery completion remains unverified; historical Brevo delivery is preserved evidence. Thus broader end-to-end production readiness is not claimed complete.

Rollback: baseline/pre-topnav-settings-20261011, full source bundle work/rivexis-pre-topnav-settings.bundle and actual API24 source backup work/rivexis-api24-rollback.json. Saved preferences are non-authorization metadata and existing user data remain preserved. Resumption record: docs/INSTITUTIONAL_COMPLETION_PROGRESS.md and this report on docs/topnav-settings-release-evidence.
