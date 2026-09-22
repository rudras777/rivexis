# Rivexis Build Execution Plan

Last updated: 2026-09-23  
Authoritative project mandate: `Rivexis_Master_Build_Prompt.txt`

## Current verified baseline

- Repository: private `rudras777/rivexis`; default branch `main`.
- Baseline verified at chat start: `daa5cc1c924a9c3a0214aad24a93dd00d4a732ca` (`Add honest free-tier API fallback`).
- Frontend: Next.js 16 / React 19 / TypeScript on Cloudflare Workers using vinext.
- API: FastAPI remains the authoritative application backend. The free Cloudflare Worker at `rivexis-api.rudrasingh0718.workers.dev` is an explicit degraded placeholder, not a replacement API.
- Live frontend preview was reachable on 2026-09-23 at `https://rivexis-web.rudrasingh0718.workers.dev`.
- Live API `/health` was verified on 2026-09-23 as `status=degraded` with the FastAPI runtime unavailable on the approved free-tier stack.
- Supabase project `ivszvufdonfgwjpfgwii` is `ACTIVE_HEALTHY` in `ap-south-1`.
- Supabase contains 53 logical product tables plus 2 runtime-control tables; the runtime-control migration is present.
- Supabase security advisor returned no findings. A generic table-list advisory notes 19 non-RLS tables, but a direct privilege check found no explicit table grants to `anon` or `authenticated`; do not enable RLS blindly unless the access model changes.
- CI workflow contains API regression/audit, frontend type/build/vinext/audit/Playwright, invariant/secret/migration checks, and real PostgreSQL migration/runtime-control checks.
- Final PR #1 CI run #25 (`35793408514`) passed all four jobs: API, web, invariants and PostgreSQL migrations/runtime controls.
- PR #1 was merged to `main` as `ca16f39898b6392a022372ffe04cc595278a1fb6`.
- PR #2 (`Harden authenticated workspace shell states`) passed CI run #35 (`35794008464`) and merged to `main` as `773a2faa2a6653c79972e98df505f01b15d702ea`.
- PR #3 (`Harden responsive and keyboard workspace shell`) passed CI run #48 (`35794960918`) and merged to `main` as `926265f2c0e44a5a0f74caf6c815c2cf0e638f72`.
- PR #4 (`Harden browser authentication and resumable onboarding`) passed CI run #65 (`35795979200`) and merged to `main` as `543dcccff3a2b094c504d68453000685648c96ec`.
- PR #5 (`Harden browser session restoration and logout lifecycle`) passed CI run #77 (`35798213551`) and merged to `main` as `158eedd7a13bf0dd0089a5d60138dcd18de6f46d`.
- PR #6 (`Harden workspace switching and provider state boundaries`) passed CI run #93 (`35799257420`) and merged to `main` as `b1c857bed25706d959bc55bbbb8fc40e863bbba4`.

## Milestone sequence

1. **A — Baseline and product audit**
   - Verify repository, live preview, Supabase state, CI definition, routes, API contracts, migrations, tests and known production gates.
   - Maintain this durable plan, backlog, architecture decisions, deployment status and readiness matrix.
2. **B — Design system and application shell**
   - Make availability/degraded state globally visible and accessible.
   - Normalize loading, empty, error, partial and stale states.
   - Improve responsive/keyboard shell behavior without rewriting the established design.
3. **C — Authentication and onboarding**
   - Complete backend-connected browser auth/session/CSRF/onboarding journeys in runnable environments.
   - Keep email verification/recovery blocked until a real approved delivery path exists.
4. **D — Workspace foundations**
   - Finish dashboard, switching, activity, provider state, settings, saved/history foundations.
5. **E — Analysis framework**
   - Standardize input, evidence, provenance, conflicts, decisions, versions and report behavior.
6. **F — Ten-engine completion**
   - Complete B1–B5 and F1–F5 end to end, prioritizing deterministic/direct-state paths.
7. **G — Monitoring, investigations and reports**
   - Complete monitor/alert lifecycle, cases, JSON/HTML/PDF and authorized download/storage.
8. **H — Institutional controls**
   - Invitation/role administration, audit views, review/approval and policy settings.
9. **I — Production deployment**
   - Activate the prepared FastAPI Cloudflare Container only after explicit paid-plan approval and production-secret/domain gates.
10. **J — Production certification and launch**
    - Run real external-provider, browser/auth/email, RLS, backup/restore, performance, accessibility, security and operational certification.

## Current active milestone

**Milestone D — Workspace foundations: migrate remaining workspace-local state and switching boundaries**

Milestone C is complete in the runnable repository harness. The first Milestone D integrity slice is also complete: authenticated pages now have a typed active-workspace context and workspace-keyed query namespace; History and Saved Analyses are explicitly scoped to the active workspace; provider configuration health is separated from workspace runtime telemetry; and API/browser tests prove foreign-workspace reads fail closed and old workspace collection data is not reused across switches.

A hard reload remains intentionally enforced on workspace switch because several legacy tool pages still keep workspace-local results or selections in component state. Removing that boundary before those pages are migrated could leave a result from the previous workspace visible after a switch even when subsequent API calls are correctly scoped.

Acceptance targets for the next slice:
- migrate Monitors, Investigations, Protocol History and engine-runner workspace identity from imperative `localStorage` access/component-local carryover to the authenticated workspace context or an equivalently keyed boundary;
- clear or re-key selected results, reviews, latest engine results and mutation state whenever workspace identity changes;
- only after all audited workspace-local surfaces are safe, remove the hard reload switch boundary and prove in-place switching cannot display old-workspace data;
- preserve API authorization as the authoritative tenancy control; client workspace context remains UX/cache state, never a security boundary;
- keep global provider configuration state separate from workspace-owned runtime history and telemetry;
- continue explicit loading, empty, partial, unavailable and error states without fabricated provider readiness or data;
- targeted API + Playwright coverage plus full CI remain green.

## Completed evidence

- Milestone A repository/service audit and durable execution controls are complete.
- Milestone B global availability, fail-closed workspace shell, responsive/keyboard behavior and authenticated-shell accessibility are CI-verified.
- Browser web auth continues to use HttpOnly cookies plus CSRF; no bearer token is introduced into browser storage.
- Browser login and signup use non-enumerating user-facing error copy and lock duplicate submits while requests are pending.
- Browser-facing signup conflicts no longer confirm whether an account exists; backend regression tests prove known-account and unknown-account login failures return the same 401 detail.
- Login/signup UI does not render arbitrary backend identity detail.
- Email verification and password recovery are explicitly labeled unavailable until the approved delivery path is configured; no fake delivery capability is claimed.
- Onboarding checks for an existing authorized workspace before creating another, recovers CSRF after hard reload, persists the active workspace only after confirmation, and reconciles an ambiguous create response against the authorized workspace list before asking the user to retry.
- Browser session continuity is preserved across hard reloads without browser bearer-token storage.
- Explicit logout obtains/reuses CSRF, prevents duplicate transitions while pending, clears active-workspace and in-memory CSRF state only after confirmed logout or an already-ended 401 session, and routes to the unauthenticated surface.
- If logout cannot be confirmed because of a non-401 service failure, Rivexis retains local workspace context and exposes a generic retry warning instead of silently pretending the session ended.
- Revoked/expired sessions cannot refresh CSRF, clear local client session state, and fail closed on subsequent workspace access without rendering backend detail.
- Invalid-CSRF logout attempts are rejected without silently revoking an otherwise valid server session.
- The authenticated shell now exposes a typed workspace context plus workspace-scoped React Query namespace and clears workspace-query memory on logout/revocation and before workspace changes.
- History and Saved Analyses no longer use static query keys with imperative `localStorage` workspace reads; each request/key carries the active workspace ID and renders explicit loading, empty and generic fail-closed error states.
- Provider Health now distinguishes shared/global provider registry configuration from active-workspace provider runtime telemetry. A workspace with no provider activity renders an explicit empty state instead of implied readiness.
- Workspace Settings routes existing workspace selection through the shell rather than duplicating storage/reload switching logic.
- Dashboard copy identifies the active workspace while continuing to state that API authorization is authoritative.
- API regression coverage proves a foreign workspace ID is rejected for history, saved analyses, monitors and provider-runtime reads.
- Playwright coverage switches between two workspace identities and proves History does not reuse the prior workspace's collection data; provider runtime telemetry changes with workspace identity while global registry health remains shared.
- The reload-on-switch boundary is intentionally retained until legacy tool pages with workspace-local component state are migrated; this is a safety control, not an unresolved cache workaround.
- PR #6 head `37da88820f5b4e766b4d2779f7f3dc0c61081436` passed PR CI run #93 (`35799257420`) across API regression/audit, frontend type/build/vinext/audit/Playwright/Axe, invariants/secret checks and PostgreSQL migration/runtime-control certification.
- PR #6 merged to `main` as `b1c857bed25706d959bc55bbbb8fc40e863bbba4`.

## Dependencies and blockers

- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval (or another explicitly approved FastAPI-capable platform).
- **Custom domain:** BLOCKED on user domain choice/purchase approval.
- **Production email:** BLOCKED on Brevo phone verification, owned domain, domain authentication and action-time credential approval.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths must remain UNKNOWN/unavailable.
- **Production secrets:** creation/rotation requires action-time confirmation where specified by the project mandate.
- **Real deployed browser/auth certification:** BLOCKED until a live FastAPI runtime is available; repository-level browser/API evidence is not production evidence.
- **Production certification:** remains incomplete until real Rudra/Rivexis-owned targets supply external gate evidence.

## Next action

Continue Milestone D by migrating Monitors, Investigations, Protocol History and engine-runner workspace-local result/selection state to the authenticated workspace context or workspace-keyed state. Prove old-workspace results cannot survive a switch. Remove the hard reload switch boundary only after all audited surfaces are safe, then gate the change on targeted browser/API tests and full CI.
