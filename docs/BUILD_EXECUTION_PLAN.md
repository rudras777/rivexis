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

**Milestone C — Browser session restoration, logout and revocation journeys**

Browser signup/login and onboarding are now hardened and CI-verified. The remaining unblocked Milestone C priority is to prove browser-session continuity and termination behavior end to end in the repository harness: hard-reload CSRF recovery, explicit logout, revoked/expired session recovery, and safe client-state cleanup.

Acceptance targets:
- an authenticated browser session restores after a hard reload without browser bearer-token storage;
- unsafe cookie-authenticated logout obtains/reuses CSRF correctly and clears client workspace/CSRF state;
- logout/revocation returns the browser to a safe unauthenticated state and subsequent workspace access fails closed;
- expired/revoked sessions route through the existing explicit recovery state without leaking backend detail;
- concurrent/double-submit behavior does not produce duplicate state transitions;
- real production/browser certification remains BLOCKED until a live FastAPI runtime exists;
- targeted API + Playwright security/browser tests and full CI remain green.

## Completed evidence

- Milestone A repository/service audit and durable execution controls are complete.
- Milestone B global availability, fail-closed workspace shell, responsive/keyboard behavior and authenticated-shell accessibility are CI-verified.
- Browser web auth continues to use HttpOnly cookies plus CSRF; no bearer token is introduced into browser storage.
- Browser login and signup use non-enumerating user-facing error copy and lock duplicate submits while requests are pending.
- Browser-facing signup conflicts no longer confirm whether an account exists; backend regression tests also prove known-account and unknown-account login failures return the same 401 detail.
- Login/signup UI does not render arbitrary backend identity detail.
- Email verification and password recovery are explicitly labeled unavailable until the approved delivery path is configured; no fake delivery capability is claimed.
- Onboarding checks for an existing authorized workspace before creating another, recovers CSRF after hard reload, persists the active workspace only after confirmation, and reconciles an ambiguous create response against the authorized workspace list before asking the user to retry.
- Playwright covers browser auth error masking, submit locking, no bearer localStorage, existing-workspace resume, hard-reload CSRF recovery and ambiguous-create reconciliation.
- Initial PR #4 browser CI exposed only ambiguous test selectors caused by Next.js' route announcer sharing role=alert; selectors were narrowed to the form-owned alert without changing application behavior.
- PR #4 head `338a8291e786e244295c6bf80496581d8e2c8756` passed CI run #65 across API regression/audit, frontend type/build/vinext/audit/Playwright/Axe, invariants/secret checks and PostgreSQL migration/runtime-control certification.
- PR #4 merged to `main` as `543dcccff3a2b094c504d68453000685648c96ec`.

## Dependencies and blockers

- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval (or another explicitly approved FastAPI-capable platform).
- **Custom domain:** BLOCKED on user domain choice/purchase approval.
- **Production email:** BLOCKED on Brevo phone verification, owned domain, domain authentication and action-time credential approval.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths must remain UNKNOWN/unavailable.
- **Production secrets:** creation/rotation requires action-time confirmation where specified by the project mandate.
- **Production certification:** remains incomplete until real Rudra/Rivexis-owned targets supply external gate evidence.

## Next action

Continue Milestone C with browser session restoration, explicit logout and revocation journeys, including hard-reload CSRF recovery and client-state cleanup. Keep live production browser certification blocked until a real FastAPI runtime is deployed.
