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

**Milestone C — Browser authentication and onboarding journeys**

Milestone B is complete and CI-verified. The next priority is to validate and harden the existing browser session, CSRF and onboarding flow against the real FastAPI contract in runnable test environments while keeping production email verification/recovery explicitly blocked until Brevo/domain prerequisites exist.

Acceptance targets:
- browser signup/login/logout use HttpOnly session-cookie flows and CSRF protections without exposing bearer tokens to browser storage;
- session restoration and revoked/expired-session recovery are deterministic;
- onboarding persists the intended workspace/role state and safely resumes/retries after recoverable failures;
- authentication errors do not enumerate accounts or leak sensitive backend detail;
- email verification/recovery is represented as unavailable until a real approved delivery path is configured;
- targeted API + Playwright security/browser tests and full CI remain green.

## Completed evidence

- Milestone A repository/service audit and durable execution controls are complete.
- Global API availability state is accessible and does not misrepresent the free degraded API.
- Authenticated workspace shell fails closed during loading, empty, revoked-session and unavailable-service states.
- Workspace API errors preserve HTTP status through typed `ApiError` handling while withholding backend detail from shell recovery copy.
- Responsive/keyboard shell now includes a visible-on-focus skip link, explicit focus treatment, `aria-current` active navigation, mobile/tablet workspace navigation, and mobile-accessible logout.
- Axe identified a 2.44:1 contrast defect on the newly visible logout button; the component contrast was corrected rather than suppressing the WCAG rule.
- Playwright covers keyboard focus order, mobile navigation/overflow, mobile recovery actions and authenticated shell states.
- Authenticated workspace Axe coverage has no serious/critical WCAG blockers after the contrast correction.
- PR #3 head `bcef483333152973898fd26a6b5efb5e49355a93` passed CI run #48 across API regression/audit, frontend type/build/vinext/audit/Playwright/Axe, invariants/secret checks and PostgreSQL migration/runtime-control certification.
- PR #3 merged to `main` as `926265f2c0e44a5a0f74caf6c815c2cf0e638f72`.

## Dependencies and blockers

- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval (or another explicitly approved FastAPI-capable platform).
- **Custom domain:** BLOCKED on user domain choice/purchase approval.
- **Production email:** BLOCKED on Brevo phone verification, owned domain, domain authentication and action-time credential approval.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths must remain UNKNOWN/unavailable.
- **Production secrets:** creation/rotation requires action-time confirmation where specified by the project mandate.
- **Production certification:** remains incomplete until real Rudra/Rivexis-owned targets supply external gate evidence.

## Next action

Begin Milestone C by auditing the current browser signup/login/logout/session/CSRF/onboarding implementation and existing tests, then implement the highest-value unblocked browser-auth/onboarding gap without introducing fake email verification or recovery.
