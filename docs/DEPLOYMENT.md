# Deployment

## Target topology

- Frontend: Next.js on Cloudflare Workers using a compatible adapter, subject to build and runtime validation.
- API: containerized FastAPI; evaluate Cloudflare Containers against the application and worker requirements before production deployment.
- Database: Supabase PostgreSQL, with separate migration, API and alert-worker privileges.
- Provider-control plane: Redis is currently required by production startup for distributed rate budgets, authentication throttling and circuit state. An approved-stack replacement needs implementation and certification before removing it.
- Secrets: managed secret store; never expose provider secrets to browser JavaScript.
- Observability: structured logs, metrics/tracing and persistent `provider_requests` telemetry.

## Local container stack

`docker compose -f infrastructure/docker-compose.yml up --build`

The stack creates a migration owner (`rivexis_admin`), a dedicated runtime API role (`rivexis_app`) declared `NOSUPERUSER ... NOBYPASSRLS`, and an isolated alert-delivery role (`rivexis_alert_worker`) declared `NOSUPERUSER ... BYPASSRLS`. A one-shot `migrate` service receives `RIVEXIS_MIGRATION_DATABASE_URL`, runs Alembic, then hardens the worker role to SELECT+UPDATE on `alerts` only. The API and alert worker do **not** receive migration credentials. The API uses only the non-bypass app URL. The alert worker uses only its dedicated worker URL and validates at startup that it has BYPASSRLS but no schema CREATE, no INSERT/DELETE on alerts and no DML on any other Rivexis table. Compose also configures Redis for distributed provider controls.

## Production database security

Application authorization is mandatory. PostgreSQL RLS is defense in depth, not a replacement for endpoint authorization. Migrations enable and force RLS on tenant-scoped resources, including provider telemetry. Request middleware/store operations propagate verified user/workspace/organization context into transaction-local PostgreSQL settings.

For managed PostgreSQL, keep `DATABASE_URL` on the least-privilege runtime role and inject `RIVEXIS_MIGRATION_DATABASE_URL` only into a separate one-shot migration job. Do not place the migration credential in API or worker runtime environments. The migration role owns/changes schema objects; the runtime role should receive only the table/sequence privileges required by the application. Do not reuse the local development passwords from `infrastructure/docker-compose.yml`.

Before production, execute `scripts/certify_postgres_rls.py` against staging with:

- `RIVEXIS_RLS_ADMIN_DATABASE_URL`: migration/fixture-capable role.
- `RIVEXIS_RLS_APP_DATABASE_URL`: the exact non-superuser/non-`BYPASSRLS` role used by the API.
- `RIVEXIS_RLS_WORKER_DATABASE_URL`: the exact non-superuser `BYPASSRLS` alert-delivery role, restricted to SELECT+UPDATE on `alerts` only.

The certification script rejects unsafe application roles and adversarially checks cross-tenant reads/writes plus organization-admin context.

## Provider runtime

For multi-instance deployments set `RIVEXIS_PROVIDER_CONTROL_BACKEND=redis` and `REDIS_URL`. Redis coordinates rate budgets and circuit state. Provider response cache values are currently process-local, while request/cost history is persisted to PostgreSQL.

Configure per-provider budgets/cost estimates with environment variables documented in `.env.example`. Validate commercial provider limits and licensing before enabling production traffic.

## Mandatory external release gates

1. Dependency-resolved frontend install, strict TypeScript check and Next.js production build.
2. Playwright E2E, responsive visual regression and WCAG 2.2 AA automation.
3. Ruff, pip-audit, npm audit and repository/history secret scans in provisioned CI.
4. Real managed-PostgreSQL RLS certification using the application role.
5. Network-enabled smoke/failure/rate-limit testing for every configured live provider.
6. Managed secret rotation, backups/restore test, production observability and incident-response runbooks.
7. Load/failure tests for Redis/provider budgets/circuit behavior under multiple API replicas.

Never enable ambiguous DEMO behavior in production or represent unavailable evidence as live.

## P10 external-provider, protocol-adapter, deployment-registry and alert-delivery staging

Before enabling commercial/enriched evidence in production:

1. Configure provider credentials only in the backend secret store.
2. Set a controlled `RIVEXIS_CERTIFICATION_ADDRESS` / `RIVEXIS_CERTIFICATION_CHAIN` and run `scripts/certify_live_providers.py`.
3. Do not enable Arkham unless legal/commercial review has approved the deployment and `RIVEXIS_ARKHAM_LICENSE_APPROVED=true` is intentionally set.
4. For Hypernative, configure `HYPERNATIVE_WEBHOOK_SECRET` only for the Rivexis forwarding boundary. Separately certify the actual customer/provider webhook or API signature contract when supplied; do not represent the Rivexis forwarding secret as provider-native authentication.
5. Use `RIVEXIS_REQUIRE_LIVE_PROVIDER_CERTIFICATION=true` in release CI when provider certification must be mandatory rather than a skip.
6. Use `RIVEXIS_REQUIRE_REDIS_CERTIFICATION=true` when real multi-worker Redis certification is mandatory.


## Durable alert delivery worker

P10 retains the existing tenant-scoped `alerts` table as a durable outbound-delivery queue. The environment-level `RIVEXIS_ALERT_WEBHOOK_URL` is a **single global sink**, so in P34 production it is permitted only when `RIVEXIS_ALERT_WEBHOOK_SCOPE=internal_gateway`: a Rivexis-controlled multi-tenant delivery boundary, never a customer-specific endpoint. Configure the URL, scope and `RIVEXIS_ALERT_WEBHOOK_SECRET`. Production refuses delivery unless the receiver uses HTTPS, an HMAC secret is present and the scope is explicitly `internal_gateway`. The worker signs `timestamp + "." + canonical JSON body` with HMAC-SHA256 and emits `X-Rivexis-Timestamp` plus `X-Rivexis-Signature`. URL userinfo, query strings and fragments are rejected. Unsigned/plain-HTTP delivery is permitted only for explicit non-production development testing.

Docker Compose includes the independent `alert-worker` process (`python -m rivexis_api.workers.alerts`). It polls only due workspaces. Delivery failures use bounded exponential retry scheduling; exhausted items enter `dead_letter` and require an authorized manager requeue. Replayed external threat events increment `occurrence_count` and `last_seen_at` on the existing alert rather than enqueueing duplicates. Worker stdout is intentionally metadata-only: it emits aggregate cycle counters and exception class names, never alert/workspace IDs, alert payloads, webhook bodies or free-form error messages.

Operational endpoints:

- `POST /api/v1/alerts/process-due?workspace_id=...` — manager-only manual drain.
- `POST /api/v1/alerts/{alert_id}/requeue` — manager-only dead-letter recovery.
- `GET /api/v1/alerts/delivery-metrics?workspace_id=...` — 24-hour queue/SLO view.

A missing webhook URL is a safe degraded state: pending alerts are not consumed and Rivexis does not claim delivery. A configured but unsafe production target (plain HTTP, missing HMAC secret, or missing/wrong `internal_gateway` scope) is also fail-closed and leaves pending alerts unconsumed. Transport errors are reduced to stable codes before persistence, and retry request bodies never include the previous `last_delivery_error` text. Before production, test the actual receiver, HMAC verification, timeout behavior, retries, dead-letter recovery, burst handling and target delivery SLO under realistic load.

### Protocol-adapter staging certification

Configure a controlled real RPC plus one or more adapter targets and run:

```bash
PYTHONPATH=apps/api python scripts/certify_protocol_adapters.py
```

Supported target groups are `RIVEXIS_CERT_AAVE_*`, `RIVEXIS_CERT_COMPOUND_*`, and `RIVEXIS_CERT_MORPHO_*`. Set `RIVEXIS_REQUIRE_PROTOCOL_ADAPTER_CERTIFICATION=true` in release staging to make absent/failing adapter targets fatal. The script uses only read calls and sends no transaction. Archive the observed block and evidence with the release record.

A target address is not proof of official deployment identity. Maintain a separately approved deployment registry/allowlist before institutional production.

### P10 deployment registry

Run `PYTHONPATH=apps/api python scripts/check_deployment_registry.py` and `PYTHONPATH=apps/api python scripts/check_registry_governance.py` in CI. Review `docs/PROTOCOL_DEPLOYMENT_REGISTRY.md` before changing any official address snapshot. Prepare registry changes with `scripts/registry_update_governance.py plan`; changed content cannot keep the same registry version, and an approved plan binds reviewer/approval ID to both base and proposed SHA-256 fingerprints before release application.

### P10 protocol history staging

`POST /api/v1/protocol-history/timeline` uses `eth_getLogs` and is limited by `RIVEXIS_PROTOCOL_HISTORY_MAX_BLOCKS` (50,000 by default). Certify provider log-range limits and archive retention before production. `POST /api/v1/protocol-config/compare` executes protocol-native reads at both requested blocks and therefore requires archive-capable RPC state for historical blocks. Event absence must never be treated as proof that no governance action occurred.
## P31 production startup guard

For `RIVEXIS_ENV=production` or `prod`, set a unique `RIVEXIS_AUTH_SECRET` of at least 32 characters and set `ENABLE_DEMO_ADAPTER=false`. Startup fails closed for missing/known-placeholder/short secrets or enabled DEMO mode. Operational provider diagnostics/probes are authenticated API surfaces in P31.



## P32 PostgreSQL service-identity guard

For every PostgreSQL runtime service identity, P32 validates the effective login rather than only direct role flags. The API and alert-worker connections must satisfy `current_user == session_user`; be NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION, NOINHERIT and LOGIN; have no parent-role membership (including transitive membership that would permit `SET ROLE`); have no database/schema CREATE authority; and own no application relations.

The API connection must additionally be NOBYPASSRLS. The dedicated alert worker must be BYPASSRLS and is accepted only when its effective DML is exactly SELECT+UPDATE on `alerts` and no DML on any other Rivexis table. These checks run in startup/runtime validation and the `postgres-rls` certification profile.

On managed PostgreSQL platforms, do not assume a newly created login is safe because its direct `rolsuper`/`rolbypassrls` flags look correct. Provider-created parent memberships can still create a `SET ROLE` escalation path. Create standalone Rivexis service roles via SQL where necessary, revoke inherited memberships, and verify the exact production credentials with `scripts/certify_postgres_rls.py` before certification.

## P34 production security contract

For production (`RIVEXIS_ENV=production`/`prod`), P34 fails closed unless the runtime uses PostgreSQL, `RIVEXIS_PROVIDER_CONTROL_BACKEND=redis`, `RIVEXIS_AUTH_RATE_LIMIT_BACKEND=redis`, a configured `REDIS_URL`, a unique authentication secret of at least 32 characters, `ENABLE_DEMO_ADAPTER=false`, `RIVEXIS_ALLOW_DIRECT_ORG_MEMBER_ADD=false`, and an explicit list of exact HTTPS browser origins. Wildcard, credential-bearing, path/query/fragment origins are rejected.

The browser uses an HttpOnly session cookie and CSRF header for unsafe methods. Bearer authentication remains supported for API/automation clients. Organization workspaces are authorized by current organization membership only; creator lineage does not survive membership removal. The PostgreSQL RLS policy and staging certifier enforce the same rule.

Provider/RPC URLs must be treated as secret-bearing transport configuration. P34 stores only sanitized provenance labels/origins and exposes stable public provider errors, never raw transport URLs or arbitrary upstream bodies. Migration `0010` scrubs previously stored provider endpoint text.

Production Hypernative forwarding uses monitor-specific derived credentials. Production outbound alert webhooks require HTTPS, no userinfo/query/fragment, and a timestamp-bound HMAC signature. Receivers should enforce an acceptable timestamp/replay window in addition to verifying the signature.

Production direct creation of a new organization member from an email string is disabled. The current membership-claim flow proves authenticated Rivexis account possession and requires administrator acceptance; until a verified-email invitation service is integrated, administrators must perform out-of-band identity verification before accepting a claim.

## P35 observability and authentication-abuse production contract

P35 adds two production fail-closed boundaries. First, a non-loopback OTLP collector must use HTTPS; OTLP endpoint userinfo, query strings and fragments are rejected. Loopback HTTP remains valid for a local collector sidecar. Second, production authentication uses both the existing per-account Redis budget and `RIVEXIS_AUTH_GLOBAL_ATTEMPTS_PER_MINUTE` (default `300`) as a global pre-scrypt budget so rotating account identifiers cannot force unbounded password-verification work. The global budget must remain between 10 and 10000 in production.

Production tenant API callers may read shallow provider status but cannot trigger `deep=true` provider diagnostics. Deep provider probing is release/operator work and is performed directly by controlled certification runners so a tenant cannot consume the GLOBAL provider probe budget.
