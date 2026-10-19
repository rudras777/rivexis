# RIVEXIS

**Risk · Value · Execution · Analysis**

DeFi Risk & Decision Intelligence on the existing Cloudflare and Supabase infrastructure.

Live website: https://rivexis-web.rudrasingh0718.workers.dev

## Current product

- Portfolio Intelligence / LiquidationGuard: block-consistent Ethereum Aave V3 and bounded Morpho position evidence and fixed-point health-factor modeling.
- Risk Scenario Lab: asset-specific collateral and debt price shocks.
- Defense Frontier: budget, wallet balance and assumed fee constraints; repayment/collateral alternatives; zero-cost current-state baseline; reproducible evidence.
- Transaction Intelligence / GasGuard: supported read-only protocol transaction simulation, fees, allowances and modeled position effects.
- Monitoring & Reports: five bounded browser checks, owner-scoped account receipts, JSON exports and retained historical records.
- Responsive institutional UI, shared dark/light themes, existing authentication and tenant security.

The initial core is free to users. Supported financial coverage is deliberately bounded: normal-mode Aave V3 with validated WETH/USDC/USDT/WBTC oracle adapters. The pinned Ethereum Morpho WBTC/USDC market at 86% LLTV is also validated, with explicit separate or combined coverage. Other Morpho markets, eMode, isolation and unvalidated modes remain unsupported. The model does not guarantee safety, global optimality or execution. No custody, signing, automatic execution or paid AI dependency.

## Release and recovery evidence

[Current resumable checkpoint](RIVEXIS_PRODUCTION_COMPLETION_TRACKER.md), [19 October verified application evidence](docs/FINANCIAL_DISPLAY_CLOSEOUT_20261019.md), [supported workflow scenarios](docs/WORKFLOW_SCENARIO_COVERAGE.md), and [readiness boundaries](docs/PRODUCTION_READINESS.md). The [original transformation release](docs/DEFI_RELEASE_REPORT.md) and [original independent checks](certification-reports/defi-live-verification.json) remain dated historical evidence.

Last verified application: `5247672bbe1eceb377c2862b90c611549e959071`, PR94, checked19 October2026. See the [browser-storage release evidence](docs/BROWSER_STORAGE_RESILIENCE_20261019.md) for exact CI/live evidence and unresolved launch boundaries; [release-gate closeout](docs/AUDIT_GATE_INTEGRITY_20261019.md) retains parent financial/audit evidence. Subsequent builds can be deployed by the retained Cloudflare integration; inspect the public build marker and latest checkpoint for current identity. Recovery tag: `baseline/pre-defi-transformation-20261009`. Existing users and historical data remain intact; quota and receipt tables are additive.

Actual verification/recovery email delivery and isolated production logical recovery have been verified within their recorded scope. Owned-domain authentication, consistent inbox placement, real native-wallet permission testing, independent recovery-key custody and broader institutional assurance remain unresolved. Added recurring services cost is $0; total account billing is not independently certified. Supported bounded workflows are ready for controlled early access; unrestricted institutional certification is not established. See the current checkpoint for exact evidence and next safe actions.

## Development and validation

Use the locked Node workspace dependencies with `npm ci`. The current web application is in `apps/web`; the active existing Supabase API is in `supabase/functions/rivexis-api`.

- `npm run dev:web`
- `npm run test:defi`
- `npm run test:api-edge`
- `npm run test:e2e`
- `npm run build:web`, `npm run typecheck:web`, `npm run lint:web`
- `npm run build` builds the existing Cloudflare Worker.
- `node scripts/verify-defi-live.mjs` verifies the public supported beta and records evidence.

The earlier ten-engine product documentation is retained in [legacy implementation notes](docs/LEGACY_IMPLEMENTATION_README.md) for backend/history reference. Those engines are not the current public product.
