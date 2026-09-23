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
- PR #9 (`Complete truthful workspace dashboard and settings summaries`) passed CI run #129 (`35828771358`) and merged as `22a999d018e8c84dd907d48a973d58406aa5ed33`.

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

**Milestone E — Analysis framework: evidence, provenance, conflicts, decisions and versioned outputs**

Milestone D is complete at repository-test level. Workspace identity is typed and query-scoped, in-place switching is race-tested across audited tools, dashboard activity is backed by authorized workspace history while static product counts are explicitly labeled as metadata, History/Saved Analyses use supported-field summaries, and Settings lists only authorized workspace/organization data without implying unsupported member administration.

Acceptance targets for Milestone E:
- audit the shared analysis request/result/decision models and UI so evidence, provenance, confidence, conflicts and UNKNOWN conditions are represented consistently rather than engine-by-engine ad hoc;
- ensure direct-state, provider-grounded and demo inputs remain distinguishable in persisted analysis/history/report outputs;
- make stale, partial, unavailable and conflicting evidence visible without converting uncertainty into a positive/negative recommendation;
- standardize version/methodology identifiers needed to reproduce or review an analysis;
- verify analysis/detail/report surfaces never claim provider evidence that was not actually used;
- keep workspace authorization and in-place switch isolation across every new analysis/result surface;
- add targeted API/domain/Playwright coverage and require full CI before advancing to Milestone F.

## Completed evidence

- Milestone A repository/service audit and durable execution controls are complete.
- Milestone B global availability, fail-closed workspace shell, responsive/keyboard behavior and authenticated-shell accessibility are CI-verified.
- Milestone C browser auth/onboarding/session/logout/revocation is complete in the runnable repository harness; real deployed browser certification remains blocked without a live FastAPI runtime.
- Milestone D workspace foundations are complete at repository-test level.
- Browser web auth uses HttpOnly cookies plus CSRF; no bearer token is introduced into browser storage.
- Email verification and password recovery remain explicitly unavailable until a real approved delivery path exists; no fake delivery capability is claimed.
- The authenticated shell exposes a typed workspace context plus workspace-scoped React Query namespace and clears workspace query memory on logout/revocation and before workspace changes.
- History, Saved Analyses and provider runtime explicitly carry the active workspace ID; foreign workspace reads fail closed.
- Provider Health separates shared/global registry configuration from active-workspace runtime telemetry; empty runtime state is explicit.
- Engine, monitor, investigation and protocol-history delayed results are guarded against rendering after a workspace switch; switching is in-place and does not use a browser reload as an isolation mechanism.
- Workspace dashboard product constants are labeled as static product metadata; recent activity is loaded from the active workspace's authorized History API and is workspace-keyed.
- History renders supported analysis/decision fields and explicitly states the 50-record API cap is not a lifetime total.
- Saved Analyses renders only supported active saved-reference fields and states that archived entries are excluded by the API default.
- Settings renders authorized workspace and organization lists, organization membership roles and creation outcomes while explicitly stating member administration is not exposed on that page.
- Playwright covers dashboard activity switching, structured History/Saved rendering, organization membership/creation truthfulness, prior workspace collection isolation and delayed-response switch races.
- Initial PR #9 browser CI exposed two test-contract problems only: a legacy History mock used an unsupported `label` field, and a strict `ANALYST` selector matched both workspace and organization tables. Tests were corrected to the real API schema and scoped organization row.
- PR #9 final head `55dbcb2a2ba1373dc0504734e802d75826de0048` passed CI run #129 (`35828771358`) across API regression/audit, frontend type/build/vinext/audit/Playwright/Axe, invariants/secret checks and PostgreSQL migration/runtime-control certification.
- PR #9 merged to `main` as `22a999d018e8c84dd907d48a973d58406aa5ed33`.

## Dependencies and blockers

- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval (or another explicitly approved FastAPI-capable platform).
- **Custom domain:** BLOCKED on user domain choice/purchase approval.
- **Production email:** BLOCKED on Brevo phone verification, owned domain, domain authentication and action-time credential approval.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths remain UNKNOWN/unavailable.
- **Production secrets:** creation/rotation requires action-time confirmation where specified by the project mandate.
- **Real deployed browser/auth certification:** BLOCKED until a live FastAPI runtime is available; repository-level browser/API evidence is not production evidence.
- **Production certification:** remains incomplete until real Rudra/Rivexis-owned targets supply external gate evidence.

## Next action

Start Milestone E by auditing shared analysis/decision schemas, engine result persistence, explanation/report generation and the engine result UI. Identify the smallest cross-engine inconsistency in evidence/provenance/conflict/UNKNOWN representation, fix it centrally where possible, add targeted API/domain/browser coverage, and gate the slice on full CI.
