# Active API contracts

The browser uses same-origin `/api/v1` routes. `apps/web/lib/edge-api-proxy.ts` forwards bounded requests to the existing Supabase functions; clients cannot choose an RPC URL or supply administrative actors. Core features require the verified user session. Mutations also require the existing origin/CSRF controls. No service-role credential belongs in a client or example command.

| Contract | Input / output | Authority |
|---|---|---|
| POST `/api/v1/defi/snapshot` | `wallet`, optional supported `coverage`; status, positions, block/hash/time, oracle provenance, warnings and conditional liquidation evidence | `defi-http.mjs`, `defi-portfolio-rpc.mjs` |
| POST `/api/v1/defi/transaction` | Wallet, supported position/asset/action, decimal amount and optional validated repayment shares; simulation state, observed nonce, modeled before/after, fees and blockers | `defi-http.mjs`, `defi-rpc.mjs`, portfolio/Morpho adapters |
| POST `/api/v1/defi/sequence` | Validated bounded protocol sequence; ordered simulated steps and independent evidence/constraints | `defi-sequence.mjs`, `defi-morpho-sequence.mjs` |
| POST `/api/v1/on-chain/{contract,read,network,wallet}` | Chain 1 and bounded validated fields; pinned observations, explicit unknown metadata or unsupported state | `onchain-http.mjs` |
| GET/PATCH `/api/v1/defi/account-settings` | Current owner profile and validated preference schema; confirmed complete response required before success | `account-preferences.mjs`, API entrypoint |
| GET/POST `/api/v1/defi-reports` | Owner-private saved comparisons; live saves recomputed from fresh server evidence | API entrypoint and database quota/save routines |
| Authentication/session and retained historical endpoints | Existing signup/login/verification/recovery/session/logout and authorized history/workspace workflows | Active Edge entrypoints and `apps/web/e2e/browser-auth.spec.ts` / session tests |

Financial calculations themselves are deterministic shared modules. LiquidationGuard separates domains and conditional one-price thresholds; scenario shocks affect both collateral and debt in that token. Defense Planner enumerates bounded repayment/supply alternatives with shared wallet balances, budget, explicit fee reserve and risk objective. The current search is not globally optimal and cannot assume swaps, future liquidity or execution. GasGuard is a read-only assessment; slippage, MEV forecasts and advisory Proceed/Modify/Wait/Avoid labels are not implemented guarantees.

Invalid input returns422; unauthorized access401/403; actual exhausted quota429; unavailable quota/provider evidence503. Unknown write outcome is not retried or called successful. Boundaries:300 analyses/day globally, four/wallet/minute and20 owner reports under the current bounded beta. Check the validators/tests before extending contracts; do not infer a full OpenAPI specification from this summary. Legacy ten-engine API documentation remains historical in `docs/API_SPECIFICATION.md`.
