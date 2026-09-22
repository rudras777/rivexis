# API Specification

Base path: `/api/v1`.

Authentication: `POST /auth/signup`, `POST /auth/login`, `POST /auth/logout`, `GET /me`, `PATCH /me/role`.

Workspaces/organizations: workspace CRUD plus organization membership and RBAC administration endpoints.

Portfolios: `POST /portfolios`, `GET /portfolios/{id}`.

Analyses: named B1–B5/F1–F5 analysis endpoints plus generic `/analysis/{engine_id}`. Analysis lookup and evidence/source/conflict endpoints are under `/analyses/{id}`.

Monitoring: monitor CRUD, B3 point-in-time checks, replay-safe external threat ingress, persistent alert queue processing/requeue and delivery/SLO metrics.

Decisions: `POST /decisions/analyze`, `GET /decisions/{id}`, `GET /decisions/{id}/explanation`.

Reporting/history: `POST /reports`, `GET /reports/{id}`, `GET /history`.

Saved analyses: list/create/archive/delete surfaces.

Provider operations: provider registry/status/resolve plus authenticated runtime/request/usage telemetry.

## Protocol intelligence surfaces — P10

- `GET /protocol-adapters` — supported read-only protocol adapter capability contract.
- `GET /protocol-deployments` — versioned official deployment snapshot, canonical registry SHA-256 fingerprint, optional `adapter` and `chain_id` filters.
- `POST /protocol-history/timeline` — authenticated, workspace-scoped normalized protocol configuration/governance event timeline across `from_block`/`to_block`.
- `POST /protocol-config/compare` — authenticated, workspace-scoped protocol adapter snapshot comparison across two blocks with deterministic review materiality.
- `POST /protocol-config/reviews` — persist a comparison as a draft review artifact.
- `GET /protocol-config/reviews/{id}` — retrieve the persisted review payload and approval state.
- `POST /protocol-config/reviews/{id}/approve` — manager-only explicit review approval.
- `GET /protocol-config/reviews/{id}/render?format=json|html|pdf` — authenticated rendering from the persisted artifact.

Protocol adapters accept optional `at_block` for archive-state replay. Protocol-history endpoints are read-only and never sign or broadcast transactions.


P10 history retrieval uses bounded adaptive `eth_getLogs` chunks, excludes removed logs by default, and can optionally hydrate block timestamps with a bounded request count. Registry discovery exposes per-record upstream source-attestation metadata.

## P34 browser-session and organization-membership additions

Browser clients may use `POST /api/v1/auth/web/signup` and `POST /api/v1/auth/web/login`, which set an HttpOnly session cookie and return a CSRF token rather than a bearer token. `GET /api/v1/auth/web/csrf` recovers the CSRF value after an SPA reload. Unsafe cookie-authenticated API methods require `X-Rivexis-CSRF`. Existing bearer-token auth routes remain available for API/automation clients. `POST /api/v1/auth/logout` revokes the current token version and clears the browser cookie.

Production direct new-member-by-email is disabled. The P34 organization membership-claim endpoints bind a short-lived claim to the authenticated claimant, target organization and token version; an authorized organization administrator accepts the claim. Claim acceptance is authorization, not proof of email ownership, so deployment policy must include out-of-band identity verification until an email-verification/invitation provider is integrated.
