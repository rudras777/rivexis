# RIVEXIS analysis service recovery

2026-10-13: continue existing-production functional engineering. No UI, financial-model, data or account changes.

## Confirmed defects and fixes

- LiquidationGuard/GasGuard quota RPC exceptions escaped the handler; missing, null or non-boolean confirmation falsely appeared to be quota exhaustion. Catch outages, accept only explicit `true`, return 429 only for explicit `false`, otherwise return 503 before any Ethereum call.
- A broad message regex treated provider errors containing “invalid” or “unsupported” as user input errors and could reflect provider diagnostics. Snapshot evidence failures now return sanitized 503. Only an exact allowlist of plain local transaction-constraint errors, including bounded token-decimal precision, returns 422. Unsupported snapshot states remain represented by their existing protocol results.
- Preserve atomic global/wallet quotas and recheck on every explicit retry. No bypass, automatic request retry, inferred financial result, signing or submission added.

## Verification and release gates

- Actual HTTP handler tests cover both endpoints, nine quota conditions each, explicit recovery after an outage, and provider invalid-parameter/unsupported-method responses. External services are fixtures; no production quota or provider outage is induced.
- Thirteen focused HTTP tests and all 187 financial/account tests pass. Deno validation passes. PR and main CI passed, including 135 browser tests, retained API tests, security/invariant checks, both builds and PostgreSQL fixture restore.
- Existing deployed API30 bundle fetched in full (21 files); rollback saved outside the repository as `outputs/analysis-quota-api30-rollback.json`. Retain every deployed runtime file; replace only `defi-http.mjs` when deploying.
- PR73 merged. API31 is ACTIVE. All 21 fetched runtime files exactly match the intended bundle; only `defi-http.mjs` differs from API30. Existing custom cookie/CSRF/getUser authentication and `verify_jwt=false` remain unchanged.

## Verified live release

- Source commit `6761236feef543c7b1ef236c83641751a597114a`; deployed main commit `d0bc374256697d00c71955705fa2e0ee4db8f5b6`.
- Existing Worker `rivexis-web`, Cloudflare build `dbfd96bf-f552-4311-b722-4de9b01b37e1`, version prefix `5af3e67c`: Ready. Active traffic meter `aria-valuenow=100`. Independently loaded public build marker matched the exact main commit. URL unchanged: https://rivexis-web.rudrasingh0718.workers.dev/ . No overlapping manual Worker deployment.
- PR CI `38402398895`, branch CI `38402390181`, Worker validation `38402398873`, main CI `38403259655` and main Worker `38403259610` all passed.
- Final actual-production browser suite: 13 passed in 1.3 minutes; zero skips or retries.
- Retained labelled QA identity recovered through genuine Brevo/Supabase delivery, then signed in normally. No new account created and no other user's credentials changed. Secrets stayed in test-process memory and were excluded from evidence.
- Before release: genuine Aave snapshot plus successful 0.001 WETH withdrawal preview and nine invalid transaction cases all passed (11 checks). Snapshot and transaction read their own current blocks; they are not assumed to share a block.
- At preview block 26183777, genuine `eth_call` and gas estimation succeeded, with gas 255644, no blockers, and modeled health 1.629216355338661363 -> 1.629077836613369316. A separate block/hash-pinned Aave oracle read reconciled the collateral decrease within one raw USD unit of integer rounding. Debt remained unchanged; fee reserve fit observed native balance. Initial separate snapshot price was excluded because its block differed.
- After API31: repeated 0.002 WETH withdrawal preview succeeded at block 26183798, a fresh snapshot remained READY, and guest transaction access returned401. On the final exact public build, actual browser controls also displayed `SUCCEEDED AT BLOCK` with gas and fees and no error alert. Initial browser assertion used the raw enum spelling; corrected to the displayed label before confirming success.
- Successful preview means the supported read-only call and estimate succeeded at the observed block. No signature/submission, future-inclusion guarantee, ownership claim, pending-state/MEV coverage or multi-action fork certification is implied.

## Artifacts and rollback

Outside repository, task `outputs` directory: `analysis-recovery-model-tests.txt`, `analysis-recovery-live-gasguard.json`, `analysis-recovery-gasguard-numerical-checks.json`, `analysis-recovery-api31-live.json`, `analysis-recovery-browser-preview.txt`, `analysis-recovery-successful-gasguard.png`, `analysis-recovery-final-production-results.json`, `analysis-recovery-cloudflare.txt`.

API31 runtime bundle SHA256 reported by Supabase: `20d81520962106ee122970a5f721b015ac79a3fc786f4561716e35381090fd58`.

API30 rollback JSON SHA256: `ebc9a23c042d6238cce83dc40c5802282ff89cbc63df22196aad95cc6be443d1`.

No schema/policy changes, user/data deletion, new service, billing upgrade or recurring cost added. Previous Worker `b139276c` and the full API30 archive remain available. Final evidence is on `docs/analysis-recovery-release-evidence`.

## Unresolved launch gates

Production PostgreSQL backup/restore access, authenticated email sending domain and native-wallet/successful fork simulation certification remain unavailable/unverified. Prior fresh live signup/recovery, Settings, saved reports and ten genuine-data stress checks are documented in `CLIENT_RELIABILITY_PROGRESS.md`. This change does not resolve those institutional-launch gates or certify all transaction execution.
