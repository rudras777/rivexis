# Rivexis Architecture Decisions

Last updated: 2026-09-23

Only material decisions belong here. Routine refactors and UI edits do not.

## 2026-09-23 — Preserve FastAPI as the authoritative application backend

**Decision:** Keep the existing FastAPI/Pydantic/SQLAlchemy backend and business logic.

**Alternatives considered:** Replacing the backend with a Worker-native implementation or moving core behavior into the frontend.

**Rationale:** The repository already contains substantial tested auth, RBAC, evidence, engine, reporting, provider and operational logic. A rewrite would add risk and could weaken deterministic/security guarantees.

**Consequence:** The free Cloudflare API Worker remains a transparent degraded boundary until a FastAPI-capable deployment is explicitly approved.

## 2026-09-23 — Keep current custom authentication; do not migrate to Supabase Auth now

**Decision:** Preserve the reviewed custom browser session, CSRF, token-version revocation, organization/workspace membership and RLS context mapping.

**Alternative considered:** Immediate migration to Supabase Auth.

**Rationale:** No verified migration benefit currently outweighs compatibility and authorization risk. Supabase remains the PostgreSQL platform, not an implicit identity migration.

**Consequence:** Any future auth migration requires an incremental mapping and revocation/isolation proof.

## 2026-09-23 — Use Supabase PostgreSQL for primary persistence and distributed runtime controls

**Decision:** Continue the approved Supabase PostgreSQL architecture, including PostgreSQL-backed provider/auth budgets and circuit state.

**Alternative considered:** Making Redis mandatory.

**Rationale:** The runtime-control migration is applied in the active Supabase project and removes a production requirement for a separate Redis service on the approved stack.

**Consequence:** Redis remains optional; production roles must stay separated and least-privilege.

## 2026-09-23 — Keep the free API preview honest rather than emulating FastAPI

**Decision:** The free API Worker may expose health and explicit 503 application responses only; it must not imitate successful application behavior.

**Rationale:** This preserves evidence integrity and prevents fake authentication, intelligence, monitoring or reports.

**Consequence:** The frontend must detect degraded/unverifiable API state and communicate it before application actions.

## 2026-09-23 — Do not blindly enable RLS on reference/system tables

**Decision:** Treat the current non-RLS reference/system-table observation as an access-model review item, not an automatic migration.

**Evidence:** Supabase's security advisor returned no findings and a direct privilege query returned no explicit table grants for `anon` or `authenticated`.

**Rationale:** Enabling RLS without matching policies can break the existing least-privilege runtime model; absence of RLS is not by itself proof of public Data API access when grants are removed.

**Consequence:** Re-evaluate immediately if Data API exposure or grants to browser-facing roles change.

## 2026-09-23 — Global service availability is a first-class UI state

**Decision:** The web app checks the API health endpoint client-side and renders explicit degraded/unverifiable copy while remaining quiet when the service reports ready/healthy.

**Rationale:** The same frontend can run against local, degraded-free-preview and future production API origins without hard-coding a false production state.

**Consequence:** Workspace and auth actions remain visible for product discovery, but current service limitations are no longer hidden.
