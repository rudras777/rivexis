# RIVEXIS

**Risk · Value · Execution · Analysis**

DeFi Risk & Decision Intelligence on the existing Cloudflare and Supabase infrastructure.

Production application: https://rivexis.rvea.info/

Original recovery/compatibility URL: https://rivexis-web.rudrasingh0718.workers.dev/

## Current product

- Portfolio Intelligence / LiquidationGuard: block-consistent Ethereum Aave V3 and bounded Morpho position evidence and fixed-point health-factor modeling.
- Risk Scenario Lab: asset-specific collateral and debt price shocks.
- Defense Frontier: budget, wallet balance and assumed fee constraints; repayment/collateral alternatives; zero-cost current-state baseline; reproducible evidence.
- Transaction Intelligence / GasGuard: supported read-only protocol transaction simulation, fees, allowances and modeled position effects.
- Monitoring & Reports: five bounded browser checks, owner-scoped account receipts, JSON exports and retained historical records.
- Responsive institutional UI, shared dark/light themes, existing authentication and tenant security.

The initial core is free to users. Supported financial coverage is deliberately bounded: normal-mode Aave V3 with validated WETH/USDC/USDT/WBTC oracle adapters. The pinned Ethereum Morpho WBTC/USDC market at 86% LLTV is also validated, with explicit separate or combined coverage. Other Morpho markets, eMode, isolation and unvalidated modes remain unsupported. The model does not guarantee safety, global optimality or execution. No custody, signing, automatic execution or paid AI dependency.

## Engineering ownership and current evidence

[Architecture](ARCHITECTURE.md), [infrastructure inventory](INFRASTRUCTURE.md), [database](DATABASE.md), [API contracts](API.md), [security](SECURITY.md), [deployment](DEPLOYMENT.md), [operations](OPERATIONS.md), [contributing](CONTRIBUTING.md), [handover](HANDOVER.md) and [changelog](CHANGELOG.md) are the current engineering entrypoints. [Engineering standards](docs/architecture/ENGINEERING_STANDARDS.md) apply across editors and development tools.

The [founder guide](docs/development/FOUNDER_DEVELOPMENT_GUIDE.md) explains setup, routine edits and production-impacting commands; the [quick reference](docs/development/QUICK_REFERENCE.md) lists common tasks. [Governance assessment](docs/governance/ENGINEERING_GOVERNANCE_REPORT.md) distinguishes verified controls from unfinished reconstruction, inventory and transfer work.

The 3 November governance release is PR126 / `e4a23c1e528ff053ba10f443d9ffe34f7461fc64`, with existing Supabase API version 40. Its six required checks passed, with 349 fixture tests per Chromium/Firefox/WebKit, 98 compiled-Worker cases and 74 live checks across both application hosts. A genuine authenticated Aave inspection passed on the updated frontend. [Release acceptance](docs/governance/RELEASE_ACCEPTANCE_20261103.md) records exact scope and identities. The earlier [authenticated acceptance](docs/AUTHENTICATED_ACCEPTANCE_20261103.md) records financial workflows, MetaMask address access, Settings persistence and report save/reopen against API 39. [The resumable checkpoint](RIVEXIS_PRODUCTION_COMPLETION_TRACKER.md) records later work; a static release SHA is not a claim that every future documentation commit has been deployed.

Existing recovery evidence remains dated: the 20 October logical restore and 23 October encrypted off-device round trip are not current full-service recovery certification. Domain/infrastructure details are in the [production runbook](docs/RVEA_PRODUCTION_RUNBOOK.md). Supported bounded beta use is separate from unrestricted institutional or organizational-transfer readiness.

## Development and validation

Use Node 24/npm 11 and the locked workspace dependencies with `npm ci`. The safe `npm run dev:web` preview blocks production API forwarding; authenticated local workflows use isolated browser fixtures. Full independent Supabase reconstruction remains incomplete. The current web application is in `apps/web`; the active existing Supabase API is in `supabase/functions/rivexis-api`.

- `npm run dev:web`
- `npm run test:defi`
- `npm run test:api-edge`
- `npm run test:e2e`
- `npm --workspace @rivexis/web run test:compatibility` runs the bounded local Firefox/WebKit suites after installing the pinned browser packages.
- `npm run build:web`, `npm run typecheck:web`, `npm run lint:web`
- `npm run build` builds the existing Cloudflare Worker.
- Historical financial verification scripts require explicit operator authentication and may write dated report paths; use the authenticated product acceptance workflow and reviewed live browser harness rather than overwriting historical evidence.

The earlier ten-engine product documentation is retained in [legacy implementation notes](docs/LEGACY_IMPLEMENTATION_README.md) for backend/history reference. Those engines are not the current public product.
