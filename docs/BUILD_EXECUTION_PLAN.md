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
- PR #1 passed CI run #25 (`35793408514`) and merged as `ca16f39898b6392a022372ffe04cc595278a1fb6`.
- PR #2 passed CI run #35 (`35794008464`) and merged as `773a2faa2a6653c79972e98df505f01b15d702ea`.
- PR #3 passed CI run #48 (`35794960918`) and merged as `926265f2c0e44a5a0f74caf6c815c2cf0e638f72`.
- PR #4 passed CI run #65 (`35795979200`) and merged as `543dcccff3a2b094c504d68453000685648c96ec`.
- PR #5 passed CI run #77 (`35798213551`) and merged as `158eedd7a13bf0dd0089a5d60138dcd18de6f46d`.
- PR #6 passed CI run #93 (`35799257420`) and merged as `b1c857bed25706d959bc55bbbb8fc40e863bbba4`.
- PR #7 (`Complete safe in-place workspace switching`) passed CI run #105 (`35800016602`) and merged as `40950c29037ad35689c1d19a33924d430107c256`.

## Milestone sequence

1. **A — Baseline and product audit**
2. **B — Design system and application shell**
3. **C — Authentication and onboarding**
4. **D — Workspace foundations**
5. **E — Analysis framework**
6. **F — Ten-engine completion**
7. **G — Monitoring, investigations and reports**
8. **H — Institutional controls**
9. **I — Production deployment**
10. **J — Production certification and launch**

## Current active milestone

**Milestone D — Workspace foundations: activity, dashboard truthfulness and settings completion**

Milestone C is complete in the runnable repository harness. Milestone D now has two CI-verified integrity slices:

1. authenticated pages use a typed active-workspace context and workspace-keyed query namespace; History, Saved Analyses and provider runtime are explicitly workspace-scoped; foreign-workspace reads fail closed; and shared provider registry state is separated from workspace runtime telemetry;
2. workspace switching is now safely in-place. Engine outputs, monitor results, investigation selections/cases and protocol-history results/reviews are reset or ignored when their originating workspace is no longer active. The prior hard reload safety boundary has been removed only after browser race tests proved stale Workspace A responses cannot render in Workspace B.

Acceptance targets for the remaining Milestone D work:
- audit and complete dashboard/activity data so every displayed workspace metric or recent item is either backed by an authorized API response or clearly labeled as static product metadata;
- complete workspace settings states for authorized workspace/org lists, creation outcomes and permission-aware actions without implying unsupported administration controls;
- improve History and Saved Analyses from raw JSON foundations into useful, truthful workspace-scoped summaries where existing API fields support it;
- preserve in-place switch isolation across all new workspace data surfaces;
- keep provider/global-vs-workspace boundaries explicit and never fabricate provider activity or connectivity;
- targeted API + Playwright coverage plus full CI remain green.

## Completed evidence

- Milestone A repository/service audit and durable execution controls are complete.
- Milestone B global availability, fail-closed workspace shell, responsive/keyboard behavior and authenticated-shell accessibility are CI-verified.
- Browser web auth uses HttpOnly cookies plus CSRF; no bearer token is introduced into browser storage.
- Login/signup/onboarding and session/logout/revocation flows are repository-level CI verified with non-enumerating errors, duplicate-submit protection, hard-reload continuity, CSRF recovery and fail-closed session termination behavior.
- Email verification and password recovery remain explicitly unavailable until a real approved delivery path exists; no fake delivery capability is claimed.
- The authenticated shell exposes a typed workspace context plus workspace-scoped React Query namespace and clears workspace query memory on logout/revocation and before workspace changes.
- History and Saved Analyses explicitly carry the active workspace ID and expose loading, empty and generic fail-closed errors rather than raw backend detail.
- Provider Health separates shared/global registry configuration from active-workspace runtime telemetry; empty runtime state is explicit.
- API regression coverage proves foreign workspace IDs are rejected for history, saved analyses, monitors and provider-runtime reads.
- Playwright proves History and provider runtime change with workspace identity without reusing old workspace data.
- Engine runs now capture their origin workspace and discard delayed results after a workspace switch.
- Monitor list/mutation state is workspace-keyed, latest results reset on switch, and delayed old-workspace monitor responses are ignored.
- Investigation lists/selections reset on workspace changes; delayed create/update/attach/report completions are guarded by origin workspace/epoch.
- Protocol History results/reviews reset on workspace changes; delayed timeline/compare/review/report completions are guarded by origin workspace/epoch.
- The shell no longer reloads the browser when changing workspaces.
- New Playwright race coverage starts operations in Workspace A, switches to Workspace B before completion, proves A results never render, and asserts the workspace-list endpoint is called only once so a hidden reload cannot satisfy the tests.
- PR #7 head `c540b4a552d7d3ee0575fc08ca3ebdd21e4adfdb` passed CI run #105 (`35800016602`) across API regression/audit, frontend type/build/vinext/audit/Playwright/Axe, invariants/secret checks and PostgreSQL migration/runtime-control certification.
- PR #7 merged to `main` as `40950c29037ad35689c1d19a33924d430107c256`.

## Dependencies and blockers

- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval (or another explicitly approved FastAPI-capable platform).
- **Custom domain:** BLOCKED on user domain choice/purchase approval.
- **Production email:** BLOCKED on Brevo phone verification, owned domain, domain authentication and action-time credential approval.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths remain UNKNOWN/unavailable.
- **Production secrets:** creation/rotation requires action-time confirmation where specified by the project mandate.
- **Real deployed browser/auth certification:** BLOCKED until a live FastAPI runtime is available; repository-level browser/API evidence is not production evidence.
- **Production certification:** remains incomplete until real Rudra/Rivexis-owned targets supply external gate evidence.

## Next action

Continue Milestone D by auditing workspace dashboard/activity/settings/history/saved API contracts and UI surfaces. Replace static or raw-data placeholders only where existing authorized API evidence supports a better truthful view, add targeted browser/API coverage, and gate the slice on full CI before deciding whether Milestone D is complete enough to advance to Milestone E.
