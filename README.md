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

[Current resumable checkpoint](RIVEXIS_PRODUCTION_COMPLETION_TRACKER.md), [20 October verified application evidence](docs/UNIFIED_WORKSPACE_CLOSEOUT_20261020.md), [supported workflow scenarios](docs/WORKFLOW_SCENARIO_COVERAGE.md), and [readiness boundaries](docs/PRODUCTION_READINESS.md). The [original transformation release](docs/DEFI_RELEASE_REPORT.md) and [original independent checks](certification-reports/defi-live-verification.json) remain dated historical evidence.

Last verified application: `4849a626d433c051f440d2b9aff434cc4435e277`, PR96/97, checked20October2026. See the [unified workspace closeout](docs/UNIFIED_WORKSPACE_CLOSEOUT_20261020.md):291 workflow cases pass per Chromium/Firefox/WebKit engine,30 actual-public checks pass per engine, and six genuine final-release planner alternatives independently reconcile exactly at block26231717. The [prior browser release](docs/BROWSER_COMPATIBILITY_CLOSEOUT_20261020.md), independent sequence evidence and [browser-storage release](docs/BROWSER_STORAGE_RESILIENCE_20261019.md) remain included. Recovery tag: `baseline/pre-defi-transformation-20261009`. Existing users and data remain intact; no new database migration or infrastructure change.

Actual verification/recovery email delivery and isolated production logical recovery have been verified within their recorded scope. Owned-domain authentication, consistent inbox placement, real native-wallet permission testing, independent recovery-key custody and broader institutional assurance remain unresolved. Added recurring services cost is $0; total account billing is not independently certified. Supported bounded workflows are ready for controlled early access; unrestricted institutional certification is not established. See the current checkpoint for exact evidence and next safe actions.

## Development and validation

Use the locked Node workspace dependencies with `npm ci`. The current web application is in `apps/web`; the active existing Supabase API is in `supabase/functions/rivexis-api`.

- `npm run dev:web`
- `npm run test:defi`
- `npm run test:api-edge`
- `npm run test:e2e`
- `npm --workspace @rivexis/web run test:compatibility` runs the bounded local Firefox/WebKit suites after installing the pinned browser packages.
- `npm run build:web`, `npm run typecheck:web`, `npm run lint:web`
- `npm run build` builds the existing Cloudflare Worker.
- `node scripts/verify-defi-live.mjs` verifies the public supported beta and records evidence.

The earlier ten-engine product documentation is retained in [legacy implementation notes](docs/LEGACY_IMPLEMENTATION_README.md) for backend/history reference. Those engines are not the current public product.
