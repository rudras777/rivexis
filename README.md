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

[Current resumable checkpoint](RIVEXIS_PRODUCTION_COMPLETION_TRACKER.md), [20 October verified application evidence](docs/ACCOUNT_RESPONSE_RECOVERY_20261020.md), [supported workflow scenarios](docs/WORKFLOW_SCENARIO_COVERAGE.md), and [readiness boundaries](docs/PRODUCTION_READINESS.md). The [original transformation release](docs/DEFI_RELEASE_REPORT.md) and [original independent checks](certification-reports/defi-live-verification.json) remain dated historical evidence.

Last verified application: `4ad0ddb0177add65fd0748202e64ed6115638c69`, PR98, checked 20 October 2026. [Account-response recovery closeout](docs/ACCOUNT_RESPONSE_RECOVERY_20261020.md): 305 workflow cases pass per Chromium/Firefox/WebKit engine and 30 actual-public cases pass per engine. Genuine Settings/profile/preferences and the exact deployed identity are verified. Financial models remain unchanged from the [prior unified release](docs/UNIFIED_WORKSPACE_CLOSEOUT_20261020.md), including its independently reconciled planner and sequence receipts. [Supported-beta operations](docs/SUPPORTED_BETA_OPERATIONS_20261020.md) records safe incident response and rollback. Recovery tag: `baseline/pre-defi-transformation-20261009`. Existing users/data remain intact; no new migration, credential, paid service or infrastructure change.

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
