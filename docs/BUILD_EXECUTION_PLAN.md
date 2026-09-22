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
- PR CI run #21 (`35793197939`) passed all four jobs after the root-layout syntax fix: API, web, invariants and PostgreSQL migrations/runtime controls.

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

**Milestone B — Consistent workspace loading, empty, error and degraded states**

The global availability boundary is complete and CI-verified. The next highest-value shell work is to make authenticated workspace data failures intentional and accessible rather than leaving query failures, empty workspaces or unavailable API calls implicit.

Acceptance targets:
- workspace shell distinguishes loading, empty, unauthorized/session-expired and service-unavailable states;
- navigation and workspace selector do not imply a usable authenticated workspace while API data is unavailable;
- error/retry copy is non-sensitive and keyboard/screen-reader usable;
- existing responsive layout remains intact;
- targeted Playwright coverage plus TypeScript/build/vinext/e2e checks stay green.

## Completed evidence

- Milestone A repository and service baseline verified on 2026-09-23.
- Existing architecture, deployment, security, provider, staging-certification, test and verification documents reviewed.
- Current frontend routes and workspace/auth entrypoints inspected.
- Current Cloudflare free-preview behavior verified.
- Current Supabase project/schema/migrations/security-advisor state verified.
- Direct Supabase role-grant check confirmed no explicit `anon`/`authenticated` table grants.
- Durable execution files required by the master mandate were added.
- Global API availability state was added to the root layout.
- Degraded free-preview and unverifiable API states are textually disclosed and use an accessible status region.
- PR CI run #21 passed API regression/audit, frontend type/build/vinext/audit/Playwright, invariants/secret checks, and PostgreSQL migration/runtime-control certification.

## Dependencies and blockers

- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval (or another explicitly approved FastAPI-capable platform).
- **Custom domain:** BLOCKED on user domain choice/purchase approval.
- **Production email:** BLOCKED on Brevo phone verification, owned domain, domain authentication and action-time credential approval.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths must remain UNKNOWN/unavailable.
- **Production secrets:** creation/rotation requires action-time confirmation where specified by the project mandate.
- **Production certification:** remains incomplete until real Rudra/Rivexis-owned targets supply external gate evidence.

## Next action

Merge the CI-green global service-availability milestone to `main`, then continue Milestone B by hardening `AppShell` loading/empty/error/session states and adding browser coverage. Do not move to Milestone C until the shell no longer hides authenticated data/service failures.
