# Aave defense sequence production integration

Updated 2026-10-14 (Asia/Calcutta). Existing repository/infrastructure; no redesign or financial-kernel change.

## Authorized scope

Expose a bounded next-block sequence assessment for one or two selected Aave normal-mode repayment/collateral-supply actions. Required approvals are reset-to-zero then exact aggregate amounts when existing allowance is insufficient. No raw client calldata, balance/state/block overrides, signatures, custody or chain submission. Morpho sequence preview remains unsupported.

The authenticated existing API dispatches /api/v1/defi/sequence through the same distributed quota and existing cookie/CSRF controls. Request bodies remain bounded to 4096 UTF-8 bytes. Input errors precede quota/RPC. Provider errors remain unavailable evidence rather than fake successful results.

## Implementation

- Fresh validated Aave snapshot; one lending account, known active reserves and normal mode only.
- Aggregate wallet/debt constraints across up to two actions; supplies require existing eligible collateral.
- Exact canonical parent, next simulated block/time, validation flag and complete per-call status/gas/return data.
- Actual account and wallet token observations before/after, retained partial state and explicit BLOCKED status on any reverted step.
- Conservative native gas-limit reserve includes observer calls. Gas totals are not an execution fee quote; observers consume simulation nonces/fees.
- Selected-alternative workspace panel retains existing styling, evidence export and clear current-price versus stressed-model distinction.
- Input, alternative, snapshot and planning-context changes cancel/suppress obsolete replies; samples/restored/stale evidence cannot open the control.

## Actual engine evidence

New production engine (not deployed API yet) succeeded via the existing public RPC at Ethereum parent 26185267. Exact USDT approval + 1 USDT repayment + 2 USDT repayment: four action/approval steps; wallet USDT 2000000000 -> 1997000000 raw; debt 1498821749142 -> 1498522130811 base; observed health 1632963348170182713 -> 1633289847020552131. No state override or transaction submission. Full evidence outside repo: outputs/production-sequence-engine-real-probe.json.

This single actual engine probe is distinct from the twelve prior historical Aave certification scenarios and new deterministic tests; it does not certify every arbitrary sequence, future inclusion, wallet ownership or market shock execution.

## Verification and rollback

202 financial/API/account tests passed; 12 new engine scenario cases and three HTTP quota/input/provider regressions included. Deno check, frontend AST, TypeScript and Next production build passed. First new browser run 9/10: the sample-switch test omitted navigation back to the Frontier after the existing sample operation returned to Portfolio. Corrected test navigation; final browser run pending. A later type check caught untyped test setup helpers; these now use Playwright Page and typecheck/build passed again.

Existing deployed API31 ACTIVE source captured completely before changes: outputs/defense-sequence-api31-rollback.json, SHA256 f8f82d904891762dac0100eb415f4b5e5609ef5129b6c58fda514d3368e930c1. Existing verify_jwt=false is retained because custom verified-cookie/getUser/CSRF checks precede financial dispatch. No auth/RLS/schema change. Existing Worker 9043afe / 2d56cbc9 rollback retained.

CI, API deployment, Cloudflare deployment and actual authenticated production verification are pending. Do not claim this feature shipped until all are verified. Remaining recovery/domain/native-wallet and broader institutional-certification gates remain open. Added recurring cost $0; existing quotas/provider limits preserved.

## Current documentation

Ethereum method semantics: https://ethereum.github.io/execution-apis/api/methods/eth_simulateV1/ . Current Supabase changelog checked: CBC TLS 1.2 removal starts no earlier than 2026-11-10; modern existing browser/Node/Deno clients require no weakening or account change (https://supabase.com/changelog/cbc-tls-ciphers-deprecated).

Final focused browser run: all ten passed, zero retries, 13.6 seconds. Full CI and deployed checks remain pending.

Final engine hardening verifies observed starting token balances against the exact snapshot and successful aggregate token consumption against both proposed amounts. Captured source oracle inputs and provider provenance are retained. All 203 financial/API tests passed, including 13 sequence-engine cases. Final actual reconciled engine probe passed again at parent 26186189; USDT 2000000000 -> 1997000000 raw. Evidence: outputs/production-sequence-engine-reconciled-probe.json. CI must certify this final source revision before deployment.

Release regression review found that mixed Aave/Morpho two-action cards must retain their independent-preview limitation. Sequence wording is now conditional on all actions being Aave; the existing cross-protocol browser assertion remains unchanged. Superseded CI runs are not release evidence; final exact-source CI and focused cross-protocol regressions are required.

## Verified release (2026-10-14, Asia/Calcutta)

PR78 merged. Final source ad5309b79e5afbf9c49dade6262512306260ad29; deployed main 0469f0280fb5cadc4d516b8d84389f2b93c9fe67. Branch CI 38469400788, PR CI 38469410133 and Worker gates 38469410188 passed. Main CI 38470051268, main Worker gates 38470051284 and native deployment 38470050059 completed successfully. All 161 browser tests, 203 financial/API/account tests and ten retained sequential-certification safety tests passed. Final focused 19 browser cases passed, including the unchanged mixed-protocol and historical regressions. Superseded initial CI 38468603010 had two failures on the mixed-protocol disclosure assertion; fixed conditionally without deleting those assertions. It is not counted as passing release evidence.

Existing Cloudflare rivexis-web native build e2034aac-000f-4d04-8f77-ec42211b3770 is Ready (45 seconds), active version a135662d. Authoritative traffic meter aria-valuenow=100 and matching deployment row verified. Independently, HTTP root status 200 and existing real-browser rivexis-build metadata equal the full deployed main hash.

Existing Supabase rivexis-api is ACTIVE version 32; all 22 retrieved deployed files byte-match the prepared upload. Source artifact SHA256 f9ffa0f3c3e2ac538c71bdafaf895107938afa8b6fa4ef2b00d27d785e84a2b8. verify_jwt=false remains unchanged, with the existing custom verified-cookie/getUser/CSRF gates preserved byte-for-byte. Complete API31 rollback and verified API32 source archives retained outside checkout. No auth, RLS, schema, secrets, SMTP, project, paid-plan or financial-kernel changes.

Final actual public-production browser run: 26 passed / unexpected 0 / flaky 0 / skipped 0, no retries, started 2026-10-13T21:23:32.998Z, duration 77617.792 ms. Retained JSON SHA256 05da428c4e2b739bbf76604cdff338428c7e854805f2639ea75da04ca13a5d02. New POST /api/v1/defi/sequence without credentials returned 401 Authentication required and no financial evidence. The guest suite is separate from actual authenticated financial verification.

## Actual authenticated production financial evidence

The existing real QA session inspected a genuine Aave wallet, calculated a 3000 USD budget / 25 USD assumed fee / 1.8 target alternative, ran the selected sequence and exported the actual receipt. Parent 26186242, hash 0x7f026de1370e8a57cca8725b488f730deb9995bdea50ba1918c1beb1b146a796; simulated next block 26186243. All three steps succeeded: reset USDT approval, approve exact 1489394360 raw, repay 1489394360 raw. Actual wallet USDT 2000000000 -> 510605640. Observed health 1633506366394589367 -> 1813481984435523127. Action/approval gas 232173; conservative simulation limit reserve 6254437987000000 wei includes observer gas limits and is not an execution fee quote.

Independent checks decoded both approvals, verified exact token consumption, unchanged collateral and debt reduction 148749999932 base against oracle-valued 148749999931 (one base-unit difference from protocol rounding). With the actual single 83% WETH collateral, both observed Aave Origin health factors recomputed exactly using retained weighted fixed-point arithmetic. There was no transaction submission, wallet signature, fabricated funding or price/state override.

Real stale-evidence behavior also verified: after three minutes, the sequence control was withheld. Refresh/recalculate/repeat succeeded at parent 26186261 -> simulated 26186262. Same intended action and identical starting/ending wallet balances prove independent ephemeral operations, not real token spending. First receipt SHA256 add4b02e60f5b16a4c77615110eb66c5d35a63632b3f8db3c5e06d353c688ce8; repeat SHA256 bdce7c6ace42dccc34f776424e185ea83df1bbde8b5bc2a6a4403a09119bb697.

Artifacts outside repository, task outputs: defense-sequence-live-receipt.json; defense-sequence-live-repeat-receipt.json; defense-sequence-live-independent-financial-check.json; defense-sequence-live-guest-gate.json; defense-sequence-production-public-results.json; defense-sequence-main-ci-evidence.txt; defense-sequence-cloudflare-proof.txt; defense-sequence-live-metrics.jpg; defense-sequence-live-result.jpg; defense-sequence-live-ui.txt; defense-sequence-live-repeat-ui.txt; defense-sequence-api31-rollback.json; defense-sequence-api32-deployed.json. Credentials/tokens are excluded from published progress.

## Resume boundary

This bounded Aave sequence feature is shipped and verified. Production UI demonstrated one selected financial action plus its approvals; the same final engine's separate genuine probe demonstrated two financial repayments. Tests/probes do not certify all arbitrary wallets or sequences. Morpho/cross-protocol sequences remain explicitly unsupported. Current-state sequence success does not re-certify the planner's stressed risk objective, future capital prices, inclusion or safety; fresh input/oracle provenance remains exported.

Full production PostgreSQL backup/restore access, email sending-domain DNS authentication and actual native-wallet permission testing remain unresolved institutional-launch gates. Preserve beta scope, quotas, unsupported states and free-first billing. Added recurring cost $0; total account billing is not independently certified. Final evidence lives on docs/defense-sequence-release-evidence; production stays on the exact tested main commit to avoid a needless evidence-only deployment.
