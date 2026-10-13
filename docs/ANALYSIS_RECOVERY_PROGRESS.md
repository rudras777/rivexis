# RIVEXIS analysis service recovery

2026-10-13: continue existing-production functional engineering. No UI, financial-model, data or account changes.

## Confirmed defects and fixes

- LiquidationGuard/GasGuard quota RPC exceptions escaped the handler; missing, null or non-boolean confirmation falsely appeared to be quota exhaustion. Catch outages, accept only explicit `true`, return 429 only for explicit `false`, otherwise return 503 before any Ethereum call.
- A broad message regex treated provider errors containing “invalid” or “unsupported” as user input errors and could reflect provider diagnostics. Snapshot evidence failures now return sanitized 503. Only an exact allowlist of plain local transaction-constraint errors, including bounded token-decimal precision, returns 422. Unsupported snapshot states remain represented by their existing protocol results.
- Preserve atomic global/wallet quotas and recheck on every explicit retry. No bypass, automatic request retry, inferred financial result, signing or submission added.

## Verification and release gates

- Actual HTTP handler tests cover both endpoints, nine quota conditions each, explicit recovery after an outage, and provider invalid-parameter/unsupported-method responses. External services are fixtures; no production quota or provider outage is induced.
- Thirteen focused HTTP tests pass. Full financial/account suite and Deno validation are being completed.
- Existing deployed API30 bundle fetched in full (21 files); rollback saved outside the repository as `outputs/analysis-quota-api30-rollback.json`. Retain every deployed runtime file; replace only `defi-http.mjs` when deploying.
- Branch `fix/analysis-quota-recovery`. CI, deployment and real-public-URL verification pending at this checkpoint.

## Unresolved launch gates

Production PostgreSQL backup/restore access, authenticated email sending domain and native-wallet/successful fork simulation certification remain unavailable/unverified. Prior fresh live signup/recovery, Settings, saved reports and ten genuine-data stress checks are documented in `CLIENT_RELIABILITY_PROGRESS.md`. This change does not resolve those institutional-launch gates or certify all transaction execution.
