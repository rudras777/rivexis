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
