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

**Milestone B — Responsive and keyboard application-shell hardening**

Global service availability and authenticated workspace access states are now complete, CI-verified and merged. The remaining Milestone B priority is to make the authenticated shell robust across narrow viewports and keyboard-only use without hiding navigation, creating focus traps, or changing the established institutional visual system.

Acceptance targets:
- workspace navigation remains usable at desktop, tablet and mobile widths;
- keyboard focus is clearly visible and follows a logical order;
- active navigation state is programmatically exposed, not color-only;
- workspace switching remains labeled and usable without pointer input;
- shell state/recovery actions remain responsive;
- targeted Playwright/accessibility coverage plus TypeScript/build/vinext/e2e checks stay green.

## Completed evidence

- Milestone A repository and service baseline verified on 2026-09-23.
- Existing architecture, deployment, security, provider, staging-certification, test and verification documents reviewed.
- Current Cloudflare free-preview behavior and Supabase project/schema/migration/security state verified.
- Durable execution files required by the master mandate were added.
- Global API availability state was added to the root layout with accessible degraded/unverifiable disclosure.
- Authenticated workspace shell now fails closed while access is loading or unavailable.
- The web API helper preserves HTTP status through a typed `ApiError`, enabling explicit 401/403/503 handling without rendering backend detail strings.
- Valid no-workspace sessions receive an explicit onboarding state; expired/revoked sessions receive a login recovery state; unavailable application APIs suppress authenticated navigation and workspace content and provide retry/public-site recovery.
- Playwright covers loading, empty-workspace, revoked-session and service-unavailable shell states.
- PR #2 head `192c62029f2fb8a0f25f6c4e1a8a2ac0fe02fd39` passed CI run #35 across API regression/audit, frontend type/build/vinext/audit/Playwright, invariants/secret checks and PostgreSQL migration/runtime-control certification.
- PR #2 merged to `main` as `773a2faa2a6653c79972e98df505f01b15d702ea`.

## Dependencies and blockers

- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval (or another explicitly approved FastAPI-capable platform).
- **Custom domain:** BLOCKED on user domain choice/purchase approval.
- **Production email:** BLOCKED on Brevo phone verification, owned domain, domain authentication and action-time credential approval.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths must remain UNKNOWN/unavailable.
- **Production secrets:** creation/rotation requires action-time confirmation where specified by the project mandate.
- **Production certification:** remains incomplete until real Rudra/Rivexis-owned targets supply external gate evidence.

## Next action

Continue Milestone B with responsive and keyboard shell hardening, including programmatic active-navigation state and targeted accessibility/browser coverage. Move to Milestone C only after those shell acceptance targets are CI-green.
