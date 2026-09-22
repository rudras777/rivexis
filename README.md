# Rivexis

**Risk • Value • Execution • Intelligence System**

Rivexis is institutional blockchain intelligence and crypto-finance / DeFi risk decision infrastructure. It analyzes evidence before capital or transactions are committed and produces one explainable outcome: **PROCEED, MODIFY, WAIT, AVOID, or UNKNOWN**.

This repository is the **P37 production-MVP certification-outcome-integrity correction over P36** derived from the supplied Rivexis master build specification. It does not claim unconfigured providers are live and never fabricates blockchain state, wallet identity, prices, APYs, threat intelligence, simulations, confidence, or provider evidence.

## Implemented

- Next.js / React / TypeScript institutional public site and authenticated workspace.
- Exactly **10 engines**: B1–B5 and F1–F5.
- FastAPI API with authentication, role onboarding, organizations, workspace-scoped RBAC, server-side bearer-token revocation, saved analyses, history, monitors, alerts and HTML/JSON/PDF reports.
- Canonical Pydantic evidence/engine/decision models, provenance, freshness and source-conflict structures.
- Deterministic Rivexis decision policy with hard blockers, confidence/completeness adjustments and valid `UNKNOWN` outcomes.
- Provider registry, health/fallback resolution, explicit DEMO isolation and live/non-live distinction.
- Current external evidence: Blockaid EVM security scans, Nansen address labels, license-gated Arkham enrichment, and a replay-safe customer-forwarded Hypernative event ingress.
- Durable B3 alert delivery lifecycle: replay occurrence counting, pending/retry/dead-letter states, exponential retry scheduling, HMAC-signed delivery to an explicitly trusted Rivexis-controlled internal gateway, SLO metrics, manager requeue controls, and an independent alert-worker process.
- Reusable protocol-native evidence for F2–F5: direct contract bytecode, EIP-1967 implementation/admin/beacon slots, explorer verification/proxy metadata, direct AggregatorV3-compatible oracle state, and explicitly caller-declared governance/admin/dependency metadata.
- P11 registry-aware protocol-specific direct-state adapters for **Aave V3, Compound III/Comet and Morpho Blue**, including authoritative reserve/collateral/liquidation/oracle/position reads and an F3 protocol-native position path that does not require duplicate caller-modeled thresholds.
- Protocol-adapter capability discovery (`GET /api/v1/protocol-adapters`), versioned official deployment discovery (`GET /api/v1/protocol-deployments`), historical `at_block` replay, plus non-mutating staging certification (`scripts/certify_protocol_adapters.py`).
- P11 deployment registry: 8 reviewed records covering Aave V3 Ethereum/Base, Compound III USDC Ethereum/Base, and Morpho Blue Ethereum/Base/Arbitrum/Optimism; explicit mismatches are surfaced and never silently overwritten.
- P11 registry change-control: deterministic registry fingerprinting plus plan/approve/verify tooling that rejects same-version content changes and stale/tampered approvals.
- P11 historical protocol intelligence: normalized Aave/Compound/Morpho configuration/governance event timelines plus block-to-block configuration comparison with review materiality.
- P11 upstream registry attestation: Aave/Compound official GitHub-backed deployment sources are pinned to reviewed blob SHAs; Morpho official documentation records remain explicitly labeled reviewed content snapshots.
- P11 historical retrieval hardening: adaptive chunked `eth_getLogs`, duplicate-boundary protection, removed-log/reorg handling, and optional bounded block-timestamp hydration.
- P11 first-class protocol review artifacts: persisted draft/approved configuration reviews with audit trail and authenticated JSON/HTML/PDF rendering.
- P11 Protocol History UI presents normalized tables first, preserves raw evidence behind a disclosure, and supports saving/approving configuration reviews.
- P11 Morpho provenance: direct `isIrmEnabled`, official ChainlinkOracleV2 factory recognition, and official Adaptive Curve `rateAtTarget` state when supported.
- P11 deeper Morpho dependency evidence: runtime-code SHA-256 comparison fingerprints, Chainlink component-feed health/freshness, official Adaptive Curve `MORPHO()` binding verification, and direct `borrowRateView` economics when supported.
- P11 OpenTelemetry-compatible correlation: W3C `traceparent` at the API boundary, provider/webhook propagation, persisted trace/span IDs, and workspace-scoped trace correlation.
- P12 real OTLP/HTTP protobuf export through the official OpenTelemetry Python SDK when explicitly enabled, with fail-fast endpoint/dependency validation, exporter health counters, and authenticated `GET /api/v1/observability/status`.
- P12 provider/webhook child spans preserve W3C trace lineage and sampling flags instead of reusing the request span ID.
- P12 Redis rate-budget members include a per-worker UUID, closing a same-timestamp multi-replica sorted-set collision that could undercount shared provider budgets.
- P12 machine-readable staging/dependency certification orchestration keeps unavailable PostgreSQL, Redis, provider, archive-RPC, browser and audit gates as explicit `SKIP`, never false `PASS`.
- P13 tamper-evident staging evidence: deterministic source-tree SHA-256, per-gate duration/output hashes, runtime fingerprints, prerequisite-presence metadata only, and a separate evidence verifier.
- P13 PostgreSQL DR certification: destructive restore requires distinct approved targets plus an explicit apply flag, verifies all 53 application tables, measures dump/restore/RTO, and supports an operator-defined maximum RTO.
- P13 Redis certification now performs concurrent exact-timestamp multi-worker budget tests, exact cardinality enforcement, shared circuit checks, and p50/p95 latency reporting.
- P13 production-browser certification harness: Playwright public-route smoke tests, axe WCAG serious/critical checks, and response-security-header validation against `next start`; execution remains dependency-gated.
- P14 multi-run release certification bundle: independently sealed staging reports from PostgreSQL, Redis, provider, archive-RPC, frontend/browser and observability runners can be combined only when they share the identical source-tree fingerprint; any FAIL remains FAIL and SKIP never becomes PASS without real PASS evidence.
- P15 runner-profile binding: each sealed staging report declares an authorized runner profile, and a non-SKIP result is rejected if that profile is not permitted to satisfy the gate; `scripts/certification_plan.py` emits the exact gate/profile/prerequisite-name plan without credential values.
- P16 source-bound certification campaign manifests: every production runner report is tied to one sealed execution manifest, canonical report paths and the exact release fingerprint; complete certification also requires all planned specialized runner profiles to be observed, and every staging report must carry the full ordered nine-gate matrix.
- P17 Ed25519 organizational release attestation: a final artifact can be signed only after a complete `--require-complete` certification bundle; the signature binds the immutable artifact SHA-256/size, source fingerprint, execution manifest, certification-bundle seal, key ID and public-key fingerprint. Production private keys and release artifacts are required to remain outside the source repository.
- P18 external organizational release trust policy: signing and verification both require an out-of-repository trust root that authorizes the exact Ed25519 key fingerprint, key ID, ACTIVE/revoked state, validity window and release-number range; the attestation binds the trust-policy ID and canonical SHA-256.
- P19 multi-party release authorization: the external schema-v2 trust policy requires at least two distinct Ed25519 signatures and at least two required organizational roles; every signer signs the same canonical schema-v3 attestation body, and dropped/substituted/role-tampered signatures fail closed.
- P20 detached release ceremony: the coordinator creates one sealed source/artifact/certification request, each organizational role signs independently with exactly one external private key, and the coordinator assembles schema-v4 attestation using detached envelopes plus public keys only; the previous centralized multi-private-key signing CLI is removed.
- P21 anti-replay/freshness ceremony: external trust-policy schema v3 controls request TTL, maximum certification age and clock skew; each schema-v2 request receives a unique 256-bit ceremony ID and expiry, each detached signer must sign while the request is open and certification is still fresh at that signer timestamp, and the final schema-v5 attestation remains historically verifiable after ceremony expiry.
- P22 anti-rollback release lineage: a verified quorum attestation can advance an external hash-chained channel checkpoint only from an explicitly trusted predecessor head (or explicit genesis); release numbers must increase, artifact/attestation hashes are bound into each checkpoint, and deployment verification can require both the exact trusted head SHA-256 and a minimum accepted release floor.
- P23 release/configuration consistency: `.env.example`, runtime release metadata, current certification/signing documentation and operator CLI labels are synchronized to one release identity; regression tests prevent a stale deployment template from overriding telemetry with an older release version.
- P24 PostgreSQL migration/runtime credential separation: Alembic receives a dedicated migration connection while runtime uses the restricted application identity.
- P25 PostgreSQL one-shot migration isolation: Alembic/DDL runs only in a dedicated migration job using `RIVEXIS_MIGRATION_DATABASE_URL`; API and alert-worker runtime containers receive no migration credential.
- P26 PostgreSQL ORM auto-create fail-closed behavior: SQLAlchemy `create_all()` is SQLite-only and PostgreSQL refuses startup if runtime schema auto-create is requested.
- P27 PostgreSQL background-worker RLS hardening: the authenticated API remains on a `NOSUPERUSER NOBYPASSRLS` runtime role, while the cross-workspace alert-delivery worker uses a separate non-superuser `BYPASSRLS` service role restricted to effective SELECT+UPDATE on `alerts` only. Worker startup rejects superuser, schema-create, excess alert DML or access to any other Rivexis table.
- P29 shared alert-processing log confidentiality: daemon and manual/operator stdout are metadata-only.
- P30 outbound alert transport integrity: production webhook delivery requires HTTPS + HMAC, URL userinfo/fragments are rejected, retry bodies omit prior delivery-error text, and persisted transport failures use stable non-secret codes.
- P31 production access-control hardening remains intact: production startup rejects known/short auth secrets and enabled DEMO adapters; provider diagnostics/probes require authentication.
- P32 PostgreSQL service-identity hardening: API/worker logins must be standalone least-privilege roles with exact session identity, no parent-role/`SET ROLE` escalation path, no database/schema CREATE, no application-relation ownership and no administrative role attributes; API remains NOBYPASSRLS while the dedicated alerts-only worker retains narrowly scoped BYPASSRLS.
- P35 observability confidentiality: provider/RPC trace endpoints are sanitized, HTTP spans use route templates instead of concrete tenant IDs, alert spans omit alert IDs, and exported exception telemetry contains only exception class/type rather than raw messages or stack traces.
- P35 production OTLP transport guard: remote production collectors require HTTPS; loopback HTTP is allowed for a local sidecar, while endpoint userinfo/query/fragment components are rejected.
- P35 diagnostic isolation: authenticated tenant API users cannot invoke `deep=true` provider probes in production; trusted release certification probes providers directly from the controlled runner.
- P35 authentication CPU-abuse hardening: a distributed global authentication budget runs before login/signup scrypt work in addition to the existing per-account login budget; Supabase PostgreSQL is the preferred production backend and Redis remains supported.
- P36/P37 dependency certification integrity: runner-generated root `package-lock.json` no longer breaks the source seal; its SHA-256 is bound into dependency evidence, and previously floating frontend type packages are exact-version pinned.
- P37 provider certification outcome integrity: multi-line child output cannot promote an overall provider SKIP to PASS; partial provider skips remain compatible with a final real provider PASS.
- P34 tenant-revocation hardening: personal workspaces remain owner-based, while organization workspaces are authorized by current organization membership only; removing a member revokes creator access at both application RBAC and forced PostgreSQL RLS layers.
- P34 browser-session hardening: the web UI uses an HttpOnly session cookie plus CSRF protection instead of storing bearer credentials in `localStorage`; bearer authentication remains available for API/automation clients.
- P34 identity/onboarding hardening: production direct-add-by-email for new organization members is disabled; short-lived organization-bound membership claims require authenticated account possession and administrator acceptance, with out-of-band identity verification required operationally until a verified-email/invitation service is integrated.
- P34 organization OWNER-authority hardening: ADMIN can manage non-owner memberships but cannot create, demote, modify or remove OWNER membership; only OWNER can transfer OWNER authority, and the final OWNER cannot be demoted or removed.
- P34 authentication-abuse hardening: bounded login input, timing-balanced missing-user verification and a production PostgreSQL- or Redis-backed distributed login-attempt budget with fail-closed backend errors.
- P34 provider-secret provenance hardening: credential-bearing RPC/provider URLs and arbitrary upstream transport/error text are sanitized before telemetry, evidence, warnings or API responses; historical provider telemetry endpoints are scrubbed by migration.
- P34 webhook isolation/integrity: Hypernative ingress uses monitor-scoped derived credentials in production; outbound alert HMACs bind a timestamp, reject query/userinfo/fragment-bearing URLs, and never reflect prior free-form delivery errors.
- P34 production dependency guard: production requires PostgreSQL, distributed PostgreSQL/Redis provider controls and authentication throttling, a strong auth secret, DEMO disabled, direct organization email-add disabled and exact HTTPS browser origins.
- P34 certification strengthening: PostgreSQL RLS certification covers organization-member revocation, Redis certification covers distributed authentication budgets, and the protocol-adapter gate activates directly from concrete Aave/Compound/Morpho certification targets.
- P11 protocol investigation cases: normalized timeline capture, linked configuration reviews, analyst notes/disposition, audited status transitions, and authenticated JSON/HTML/PDF rendering.
- P11 retention and backup controls: bounded provider/audit retention with deletion disabled by default, plus non-destructive backup/restore certification tooling and explicit PostgreSQL restore opt-in.
- Provider runtime controls: retry/backoff, workspace-scoped budgets, cache, concurrent request coalescing, circuit breakers, cost/latency telemetry and persisted provider-request history.
- Supabase PostgreSQL control plane for distributed rate budgets, authentication throttling and circuit state; Redis remains an optional alternative.
- PostgreSQL production schema blueprint and Alembic migrations covering all **53 tables** with schema-contract verification.
- PostgreSQL FORCE-RLS policies and request-scoped user/workspace/organization context propagation.
- Docker deployment using a one-shot Alembic migration job, a dedicated `NOSUPERUSER NOBYPASSRLS` API role, and an isolated least-privilege alert-worker database role.
- Verification scripts for engine invariants, migrations, schema contract, secrets, frontend AST structure, PostgreSQL RLS, Redis multi-replica behavior, commercial provider probes and protocol-adapter live certification.

## Ten engines

| ID | Engine | Non-demo path |
|---|---|---|
| B1 | Transaction Simulation | Tenderly when configured; RPC dry-run fallback; standard calldata decoding; verified-ABI resolution; optional `debug_traceCall` call-tree/state-diff normalization |
| B2 | Transaction & Contract Security | RPC + deterministic calldata/approval rules + optional Etherscan verification + credentialed Blockaid address/transaction scans |
| B3 | Threat & Monitoring | RPC snapshots/change detection + optional Chainlink-compatible feed state + Blockaid point-in-time screening + replay-safe Hypernative forwarding ingress; provider-native continuous streaming still requires deployment-specific certification |
| B4 | Entity & Fund-Flow | RPC state + optional Etherscan history + Nansen labels + license-gated Arkham enrichment/conflict handling; unlabeled entities remain `UNKNOWN ADDRESS` |
| B5 | Route & Bridge Intelligence | LI.FI quote normalization; remains partial without independent bridge/security evidence |
| F1 | Portfolio & Exposure | CoinGecko references + supplied positions/native-wallet context |
| F2 | Protocol Risk | DeFiLlama fundamentals + direct/caller-declared protocol-native evidence + Aave V3 / Compound III / Morpho Blue protocol adapters |
| F3 | Position & Liquidation | Protocol-native Aave/Compound/Morpho position/liquidation state when supplied; generic Chainlink-compatible feed + deterministic position model remains the fallback |
| F4 | Yield & Strategy Risk | DeFiLlama Yields + optional protocol-native contract/oracle/governance evidence; APY is never treated as safety proof |
| F5 | Treasury Allocation & Scenario | CoinGecko references + Rivexis concentration/stress calculations + multiple optional protocol-native dependency checks |

## Repository

```text
rivexis/
  apps/web/                  Next.js / React / TypeScript UI
  apps/api/                  FastAPI / Pydantic / SQLAlchemy API
  packages/                  Shared domain/package boundaries
  providers/                 Provider-category contracts/integration notes
  docs/                      Product, data, security and deployment docs
  infrastructure/            Docker, PostgreSQL, schema and role setup
  scripts/                   Verification and RLS-certification tooling
  tests/                     Cross-stack scenario fixtures
```

## Local development

1. Copy `.env.example` to `.env` and set `RIVEXIS_AUTH_SECRET`.
2. Start Postgres/Redis: `docker compose -f infrastructure/docker-compose.yml up -d postgres redis`.
3. API: `cd apps/api && python -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]' && alembic upgrade head && uvicorn rivexis_api.main:app --reload --port 8000`.
4. Web: from repository root run `npm install && npm run dev:web`.
5. Open `http://localhost:3000`; API docs are at `http://localhost:8000/docs`.

For a containerized local stack, use `docker compose -f infrastructure/docker-compose.yml up --build`. The one-shot `migrate` service applies Alembic as `rivexis_admin`; API and alert-worker start only after migration completion and connect as the non-superuser `rivexis_app` role.

## Provider control plane

Default development mode keeps rate-budget and circuit state in memory. For the approved Supabase deployment, set `RIVEXIS_PROVIDER_CONTROL_BACKEND=postgres` and `RIVEXIS_AUTH_RATE_LIMIT_BACKEND=postgres`; PostgreSQL transactions and advisory locks coordinate the controls across API replicas. Redis remains available by selecting `redis` for both backends and configuring `REDIS_URL`. Cache values remain process-local because provider responses may be arbitrary Python structures; production multi-replica deployments should use a serialization-safe shared cache if cross-worker cache reuse is required.

Workspace-scoped endpoints expose runtime and persisted operational evidence:

- `GET /api/v1/providers/runtime`
- `GET /api/v1/providers/runtime/requests`
- `GET /api/v1/providers/runtime/usage`

## Protocol-native adapters

P11 retains the read-only Aave V3, Compound III/Comet and Morpho Blue adapters beneath F2–F5, strengthens Morpho dependency provenance, and adds historical protocol event/configuration comparison surfaces. Use `GET /api/v1/protocol-adapters` for the input/read contract, `GET /api/v1/protocol-deployments` for registry discovery/fingerprint, `POST /api/v1/protocol-history/timeline` for normalized protocol events, and `POST /api/v1/protocol-config/compare` for two-block configuration review, and `/api/v1/protocol-config/reviews*` for persisted review/approval/rendering. See `docs/PROTOCOL_ADAPTERS.md`, `docs/PROTOCOL_DEPLOYMENT_REGISTRY.md`, `docs/PROTOCOL_HISTORY.md`, `docs/PROTOCOL_INVESTIGATIONS.md`, `docs/OBSERVABILITY.md`, and `docs/BACKUP_RETENTION.md`. Registered core addresses can be auto-filled; explicit caller addresses always win and conflicts are reported as `MISMATCH`.

All adapters accept optional `at_block` for archive-block replay. Registry changes use `scripts/registry_update_governance.py`; changed content cannot keep the same registry version and an approval artifact must bind reviewer/approval ID to the base and proposed fingerprints. Live adapter certification remains opt-in through `scripts/certify_protocol_adapters.py`.

## Security boundary

Rivexis reads, analyzes and simulates. It never requests private keys, seed phrases or recovery phrases; signing remains user-controlled. Application authorization remains mandatory even with RLS enabled. PostgreSQL deployments receive FORCE-RLS policies on tenant-scoped resources and use transaction-local identity context. A staging certification script validates the effective PostgreSQL service identity, not only direct flags: API/worker logins must have exact session identity, no parent-role/`SET ROLE` escalation path, no admin/DDL/ownership authority, and NOINHERIT. The API is NOBYPASSRLS; the dedicated alert worker is BYPASSRLS but has no DML beyond SELECT+UPDATE on `alerts`.

## Verification

Run `bash scripts/verify.sh` from a clean checkout. Current P37 local verification:

- **261/261 pytest PASS**
- **69 OpenAPI path templates**
- exactly **10 engines**
- deployment registry invariant: **8 official-source records PASS**
- canonical registry fingerprint + explicit plan/approve/verify governance gate PASS
- protocol history/configuration comparison regressions PASS
- **53/53** migration/schema table parity
- schema contract: **511 columns, 102 FK edges, 20 unique constraints, 11 named indexes**
- clean Alembic upgrade/downgrade
- static secret scan PASS
- frontend AST + duplicate-key gate: **38 TS/TSX files PASS**; browser-certification harness presence PASS
- local OTLP/HTTP protobuf export certification PASS (linked spans, W3C parent preservation, exception-payload redaction)
- Redis same-timestamp cross-worker budget uniqueness regression PASS
- Docker/RLS-role contract tests PASS
- alert-worker payload/error log-redaction adversarial tests PASS
- clean release archive hygiene PASS (no generated SQLite DBs, caches or Python bytecode)
- ZIP compressed-data integrity PASS
- P37 sealed execution-manifest-bound multi-run certification bundle + tamper/source/profile/missing-runner/omitted-gate/cross-campaign regression tests PASS
- P37 time-bounded detached signing-request/envelope/quorum-assembly + freshness/trust-policy contract tests PASS (ephemeral test keys only; no production key/policy bundled)
- P37 anti-rollback lineage genesis/predecessor/head-hash/monotonic-release/tamper/minimum-release contract tests PASS
- API/package/runtime/configuration version source-of-truth contract PASS (`3.4.3`, release `P37`)

The local runtime has no real PostgreSQL staging endpoint, Redis multi-replica target, commercial provider credentials/certification target, archive-RPC target, dependency-resolved frontend package installation, or Rivexis organizational signing-key quorum/trust policy. No lockfile, audit, browser, Ruff/pip-audit, external-gate, or organizational-signing PASS is fabricated. Adversarial PostgreSQL RLS certification, real Redis multi-replica certification, credentialed provider smoke certification, Next.js production build/typecheck, Playwright/WCAG, and npm/pip audits therefore remain external release gates.

See `FINAL_ENGINEERING_REPORT.md`, `docs/VERIFICATION_RESULTS.md`, `docs/STAGING_CERTIFICATION.md`, `docs/BROWSER_CERTIFICATION.md`, `docs/OBSERVABILITY.md`, `docs/DEPLOYMENT.md` and `docs/SECURITY.md` for the full production status.
