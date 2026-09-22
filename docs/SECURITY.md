# Security

Implemented controls include scrypt password hashing, expiring signed tokens, server-side token-version revocation, organization RBAC (`OWNER`/`ADMIN`/`ANALYST`/`VIEWER`), workspace-scoped authorization, request IDs, security headers, strict validation, audit records, no-private-key/seed handling, static secret-pattern scanning and PostgreSQL RLS preparation/identity propagation.

Provider/runtime controls include workspace-scoped budgets, retry/backoff, circuit breaking, concurrent request coalescing, persistent request/cost telemetry and optional Redis distribution for budget/circuit state. These are defense-in-depth controls, not substitutes for provider-side quotas or an edge WAF.

Background-service logging is data-minimized: the cross-tenant alert worker never serializes alert records, workspace/alert identifiers, tenant payload evidence, webhook bodies or free-form delivery/database errors into stdout. Its cycle logs contain aggregate counters only.

Outbound alert delivery is fail-closed in production: configured receivers must use HTTPS and HMAC-SHA256 authentication. URL userinfo/fragments are forbidden, free-form transport exceptions are not persisted, and local `last_delivery_error` diagnostics are excluded from outbound retry bodies. Development may use unsigned HTTP only when the environment is explicitly non-production.

## P5 external-integration controls

- Blockaid/Nansen/Arkham keys remain backend-only.
- Arkham requires `RIVEXIS_ARKHAM_LICENSE_APPROVED=true` in addition to credentials.
- Hypernative forwarding uses a separate `HYPERNATIVE_WEBHOOK_SECRET` and `X-Rivexis-Webhook-Secret`; comparison is constant-time.
- Hypernative forwarded events must reference an existing monitor in the supplied workspace; raw provider payload is capped at 64 KiB; workspace/provider/external-event keys are persistently unique so replayed events reuse the original alert.
- The forwarding endpoint explicitly reports that provider-native signature verification was not performed. A deployment must implement the actual customer/provider signing contract when available rather than infer one.

Production still requires managed identity/SSO as applicable, real non-superuser PostgreSQL RLS certification, real Redis multi-replica/load testing, managed secret rotation, dependency/browser audits, provider credential/license certification, backup/restore validation and incident-response procedures.
Production startup is fail-closed for application authentication: `RIVEXIS_AUTH_SECRET` must be a non-placeholder secret of at least 32 characters and `ENABLE_DEMO_ADAPTER` must be false. Provider inventory, status, individual-provider health and resolution/deep-probe endpoints require bearer authentication so anonymous callers cannot inspect operational provider state or consume configured provider/RPC quota.

## P35 observability, diagnostics and authentication-abuse hardening

P35 treats telemetry as an external data boundary. Provider/RPC URLs may contain credentials and concrete HTTP paths may contain tenant/resource identifiers, so exported spans contain sanitized provider provenance and FastAPI route templates only. Rivexis tracing helpers no longer export arbitrary exception messages or stack traces; exception telemetry is reduced to the exception type/class plus ERROR status. Remote production OTLP collectors must use HTTPS, while HTTP is accepted only for loopback sidecars. OTLP endpoint userinfo, query strings and fragments are rejected.

Authenticated provider diagnostics remain available for shallow operational state, but production tenant API calls cannot trigger `deep=true` provider probes because those probes consume GLOBAL provider/RPC control-plane capacity. Controlled release certification calls provider adapters directly instead.

P35 also adds a Redis-backed global authentication-attempt budget before login/signup scrypt work. This complements—not replaces—the per-account budget and prevents rotating random identifiers from bypassing all shared CPU-abuse controls. Production validates a bounded global budget and fails closed when the Redis authentication backend is unavailable.

## P34 production trust-boundary hardening

P34 makes current organization membership—not workspace creator lineage—the authority for organization workspaces at both application and PostgreSQL RLS layers. Browser credentials move to HttpOnly cookies with CSRF protection; API bearer tokens remain supported for non-browser clients. Production login throttling and provider controls require Redis so horizontal replicas share abuse/rate state.

Provider/RPC endpoint strings are secret-bearing and must never be emitted verbatim to telemetry/evidence. P34 sanitizes provenance and converts arbitrary upstream/transport failures into stable public messages. Hypernative ingress uses monitor-scoped credentials; outbound alert HMAC signatures bind a timestamp and body. The single global production alert sink must be explicitly scoped as a Rivexis-controlled `internal_gateway`, never a tenant/customer-specific receiver.

Rivexis does not claim that account email ownership is cryptographically verified. Production direct-add-by-email is disabled for new members. Administrators accepting an organization membership claim must verify the intended recipient through an independent channel until a verified-email/invitation system is connected.
