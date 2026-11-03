# Oracle round validation — 3 November 2026

Direct WETH and capped stablecoin oracle paths previously checked the update timestamp but omitted the round start checks already used by the WBTC composite path. All three paths now share positive round/answer/start/update checks, start <= update, answered-in-round completeness, nonfuture updates and the existing inclusive freshness limits. Invalid evidence keeps the position unsupported. Coverage, source identities, accounting mathematics and execution restrictions are unchanged.

Two Aave snapshot regressions reproduced acceptance of invalid starts before the fix: zero start and start after update. Both now withhold modeling. Sixteen additional validation cases cover freshness boundaries, stale/future timestamps, malformed rounds and incomplete answers. Synthetic fixtures remain separate from live evidence.

## Validation

- DeFi suite: 313 passed, zero failures/skips.
- API-edge suite: 42 passed, zero failures/skips.
- API-edge TypeScript check passed.
- Deno 2.9.6 check passed for API, decision reports, alerts and alert dispatch.
- Fresh read-only Ethereum RPC snapshot after the fix: block 26333520, hash `0xe71e3cf31fc6006b9ab4d56c6846f14ee98eb49b2336d70658997bad5c0e2f7f`; the existing certified reference wallet returned READY without warnings, with WETH/WBTC/USDC/USDT validated and pool accounting reconciled. This is dated evidence, not a continuous availability promise.

## Release checkpoint

Existing Supabase project `ivszvufdonfgwjpfgwii`, function `rivexis-api`, version 38, verify_jwt=false, 25 files saved outside Git for rollback. Application authorization remains enforced inside the API. No database, user, RLS, authentication-provider, infrastructure-plan or UI change is required. Deploy after review/required CI; replace only the two changed runtime modules in the captured bundle and preserve every other deployed file and JWT setting. Read back the result and record the actual function version separately.

Raw test logs, live snapshots and rollback bundle are saved in task outputs outside Git. No private credentials are included here. Broader limitations in the production runbook still apply; this change is not an institutional security certification.
