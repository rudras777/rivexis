# Test Plan

## Backend gates

- Python compileall.
- Pytest across auth/RBAC/workspace isolation, all ten engines, all five decision outcomes where applicable, evidence/conflict/freshness handling, provider fallback/demo isolation and persistence/reporting.
- B1 selector/ABI/trace/state-diff tests.
- P5 Blockaid malicious/benign normalization and B3 screening tests.
- P5 Nansen provenance, Nansen-vs-Arkham conflict and Arkham license-gate tests.
- P5 protocol-native bytecode/explorer/EIP-1967 proxy-admin-beacon/oracle/governance evidence tests and F2/F3/F4/F5 integration tests.
- P5 Hypernative forwarding-ingress authentication, monitor/workspace binding, persistence and replay/idempotency tests.
- Provider retry/backoff, cache, budget, circuit, request coalescing and telemetry tests.
- FastAPI lifespan/OpenAPI checks.
- Alembic upgrade/table/schema-contract/downgrade verification.

## Staging certification gates

- `scripts/certify_postgres_rls.py`: real managed PostgreSQL, admin fixture role + exact non-superuser/non-`BYPASSRLS` API role + dedicated non-superuser BYPASSRLS alert-worker role restricted to SELECT+UPDATE on alerts.
- `scripts/certify_redis_distributed.py`: real Redis cross-worker budget/circuit behavior.
- `scripts/certify_live_providers.py`: controlled target plus configured Blockaid/Nansen/Arkham provider credentials. Arkham must also pass the license-approval gate.
- Hypernative: certify the actual customer webhook/API and provider-native signing contract separately; the repository's Rivexis shared-secret ingress is not equivalent to provider-native signature verification.

## Frontend gates

- npm dependency installation.
- strict TypeScript typecheck.
- Next.js production build.
- Playwright E2E, responsive visual regression and WCAG 2.2 AA automation.

## Security gates

- source/history secret scan;
- npm audit / pip-audit / Ruff where provisioned;
- adversarial RLS tests;
- external callback/auth abuse tests;
- provider timeout/rate-limit/malformed-response tests.

No test may convert unavailable live evidence into synthetic passing evidence.

- P6 durable alert delivery: replay occurrence counting, success, retry, dead-letter, requeue, no-sink safe degradation, SLO metrics and worker discovery.


## P10 protocol-history and registry-governance gates

- Stable canonical registry SHA-256 fingerprint.
- Registry same-version content mutation rejection.
- Explicit PENDING_APPROVAL -> APPROVED reviewer/change-control workflow.
- Tampered/stale approval rejection.
- Aave Pool Configurator event normalization.
- Compound Configurator/governance event normalization.
- Morpho IRM/oracle-factory provenance and Adaptive Curve state.
- Block-to-block protocol configuration comparison and deterministic materiality.
- Protocol-history/configuration endpoints require authenticated workspace write access.
- Frontend Protocol History page AST/duplicate-key validation.
