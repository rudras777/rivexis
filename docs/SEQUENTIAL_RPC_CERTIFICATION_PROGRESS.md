# Sequential RPC certification continuation

## Scope and implementation

Branch: test/aave-sequential-rpc-certification. Preserve the existing website, financial kernels, infrastructure, user data and approved design.

Added scripts/certify_aave_sequence_rpc.mjs: a bounded, reproducible certification command using the existing ethereum.publicnode.com endpoint. Only eth_chainId, eth_getBlockByNumber, eth_call and eth_simulateV1 are allowed. Signing, broadcasting, unlocking and provider-state writes are rejected before network access. Requests have deadlines, redirect rejection, strict response identities, payload/request caps and final parent-hash verification.

The provider executes sequential calls in ephemeral state. Validation is enabled; no account balance, nonce, code, storage, oracle or block override is supplied. Existing token/native balances must fund the cases. Signature checks are skipped by the provider, so this establishes neither ownership nor signature authorization. Four observer calls accompany each case and also consume simulated gas/nonces; their totals are not production gas quotes.

The captured parent is Ethereum block 26184704, hash 0xbfcdaf20cab9469fcbbba501149cd0177068d9c964d4ee68a8218f02ec5235d6. This is historical state certification, not fresh current portfolio evidence. Child blocks are ephemeral parent+1 with the provider's normal +12-second progression. Results retain raw call statuses, returns, logs, gas and revert payloads.

## Actual cases and safety checks

All 12 actual cases passed twice before the final metadata update:

1. Baseline lending/token reads retain state.
2. Zero allowance blocks repayment.
3. Exact approval then one USDT repayment.
4. One approval and two sequential repayments share changing debt and allowance state.
5. Repayment exceeds the exact allowance and reverts.
6. Zero repayment reverts without exposure change.
7. Supported WETH withdrawal updates wallet assets and health.
8. Over-withdrawal reverts.
9. One USDT borrow increases debt and wallet assets.
10. Borrow beyond collateral capacity reverts.
11. Withdrawal, exact WETH approval and resupply consume evolving real token balances.
12. Repeating the repayment simulation begins from the unchanged historical parent and produces identical observed outcomes.

Expected failures retain provider revert evidence; legacy USDT failures have empty revert data. They are not replaced with invented readable protocol reasons. Every result is checked for exact call count/status, parent identity, gas, timestamp and decoded before/after asset/debt/health effects.

Ten unit tests cover mutation-method rejection, overlapping RPC response identities, provider/malformed failures, request/payload limits, chain/reorganization/eMode rejection, sample/unsupported/unfunded inputs, captured replay and corrupted/false-success evidence. They run in CI without public RPC calls. The captured replay fixture is explicitly historical; it is not a mocked live success claim.

## Security, access and costs

Fresh read-only Supabase checks: ACTIVE_HEALTHY, PostgreSQL 17.6.1.166; 61 public tables with zero missing RLS; nine public security-definer functions with zero anon/authenticated execute access. Advisors report 19 informational private-table/no-policy findings and two known warnings (pg_net in public and leaked-password protection disabled). Leaked-password protection requires Pro according to current official docs; no plan upgrade or auth/database mutation was made.

Automatic approval review rejected starting a local Anvil fork process, returning only “blocked by policy.” It was not bypassed. The read-only RPC alternative succeeded and no local fork service was started. A pinned official Anvil package was downloaded and integrity verified outside the repository; the repository gains no package dependency or permanent service.

No signatures, transactions, account changes, credentials, state overrides, database mutation, new paid service or recurring infrastructure cost. Production API31 and individual GasGuard behavior remain unchanged. This tooling certifies the listed Aave scenarios; it does not expose a new production sequence feature or certify Morpho/arbitrary sequences, market shocks, future execution or liquidation safety.

## Evidence, release and remaining work

Task outputs/aave-sequential-rpc-certification.json retains the complete actual call evidence; certification-reports/aave-sequential-rpc-reference.json contains a small labelled replay. Existing readiness matrix was rewritten because it still incorrectly described the retired ten-engine product and obsolete deployment blockers. Previous matrix remains in Git history.

Final safety rerun: ten passed. A later historical-parent rerun failed explicitly because the provider no longer served that state. The earlier successful full evidence is retained as outputs/aave-sequential-rpc-certification-initial-success.json; the diagnosed failure is retained as outputs/aave-sequential-rpc-historical-unavailable.json. The harness now invalidates old success files before parsing/probing and writes FAILED on provider/input failures; no automatic retry or silent latest-block fallback. Real probes are paced and capped.

A fresh real snapshot was explicitly refreshed and exported through the existing authenticated website. All twelve cases then passed on parent block 26184896, hash 0xd40df8e2d8ce11ea6a93689ad379b1a9b37c88eb8f0c3c541ec425442f89bbc5. Run 2026-10-13T16:56:22.740Z -> 2026-10-13T16:56:31.951Z. Final complete evidence SHA256: b4bfc437c261fda06c87c35148b0254eca0b987cdf8df2068559ed0a3c0e7595. This records only that parent state; historical-state availability from the free provider is not guaranteed. Production multi-action integration requires further validation and cannot be represented as shipped by this certification script.

PR76 passed branch and main release gates (150 CI browser, 187 financial, ten sequential safety tests, builds/types/security and PostgreSQL fixtures). Main 2303dd359f4b3e4c358d6ca14e7bb08fa5155f2a was independently observed at the existing public URL and Cloudflare active version 5a946385 with 100% traffic (native build 95a9eeb6-7301-4eac-8e61-08536cad46d2). The first final live run had 11 passes and two failures: motion-control hydration timing and a cumulative nine-route/four-API test timeout. Original screenshots/traces/JSON are preserved outside the repository in outputs/sequential-release-first-live-run. These failures are not counted as passed; the next corrective release and retest are pending. Remaining launch access gates: full production backup/restore, email-domain DNS authentication and native-wallet approval testing. Production multi-action integration and broader sequence certification remain separate work.

Official method semantics: https://geth.ethereum.org/docs/interacting-with-geth/rpc/ns-eth and https://ethereum.github.io/execution-apis/api/methods/eth_simulateV1/ . Password protection availability: https://supabase.com/docs/guides/auth/password-security . Advisor remediation: https://supabase.com/docs/guides/database/database-linter?lint=0014_extension_in_public .

Final normal-mode check also reads Pool.getUserEMode at the exact parent and rejects nonzero modes before any sequence. The final actual rerun passed twelve cases at parent 26184896, 2026-10-13T17:14:13.890Z -> 2026-10-13T17:14:28.884Z. Evidence: outputs/aave-sequential-rpc-final-mode-check.json, SHA256 7c43f0da27f78375dcd134ea282422cb87427e0de2e939c5c3fbb17549eb60b5. Ten safety tests passed.

## Corrective release and final production retest

PR77 source ea34669259882b16b6c3ca12e320eac080264a4f corrects an observed motion-control hydration race: server-rendered buttons stay disabled until their client handler effect mounts. The live motion check requires active motion before pause/resume, avoiding an initially static false positive. The original guest test exhausted one shared 30-second budget across nine page navigations and four API checks; each assertion now has its own independent test, retaining every access restriction without blanket timeout inflation.

Local production build/typecheck passed. All nine local background tests passed, including a JavaScript-disabled regression for pre-hydration state. The first local invocation incorrectly set an external localhost URL without starting its server; connection-refused results were corrected by using the configured managed test server and are not claimed as product checks.

Branch CI 38442072222 and PR CI 38442128339 passed all gates; 151 browser cases, 187 financial cases and ten sequential safety cases passed. Worker gates 38442128411 passed. PR77 merged as 9043afe3cdd15d40208b992317f6d43350b1154e. Existing Cloudflare native build dd0e3687-c895-459e-9945-ff993c975623 is Ready; active version 2d56cbc9 receives 100% traffic. Independent HTTP root returned 200 with exact rivexis-build metadata; existing real browser also confirmed that metadata. No separate Worker or deployment configuration was created.

Final actual-production run: 26 passed, zero failed, no retries, 2.2 minutes. All checks use the explicit existing production URL and exact intended commit. Test count increased by splitting the existing compound guest-access check; these are not 13 additional financial scenarios. No credentials were submitted by this guest harness and no fake authenticated session was claimed. JSON: outputs/motion-release-live-results.json. Deployment proof: outputs/motion-release-cloudflare-proof.txt. Real-browser screenshot: outputs/motion-release-live-browser.jpg. First failed-run traces remain retained separately.

This release preserves financial logic, appearance, production API31, accounts, data and integrations. Actual twelve-case sequential certification and prior real authenticated financial evidence remain separate from the guest release harness. Institutional gates listed above remain unresolved. Added recurring cost remains zero.

Final main CI 38442742214, Worker validation 38442742262 and native build job 38442743181 all completed successfully. Final live run started 2026-10-13T17:58:09.539Z, duration 134386.977 ms, expected 26 / unexpected 0 / flaky 0 / skipped 0. Retained JSON SHA256: 462210280088135b85fb606e0c7b30e1108b7ef183edf74efb03ab8cf6d90e1f. Main CI's 151 browser / 187 financial / ten safety results are retained in outputs/motion-release-main-ci-evidence.txt. Final evidence is committed on docs/motion-release-evidence; production remains the exact tested main commit, avoiding an unnecessary evidence-only deployment.
