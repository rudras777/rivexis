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
- PR #10 (`Harden decision evidence integrity and uncertainty semantics`) passed CI run #144 (`35830902047`) and merged as `deca453077f51101ef853161d07836a26472778d`.
- PR #11 (`Expose truthful analysis provenance in reports and engine results`) passed CI run #154 (`35831726073`) and merged as `5795344fea5b4e3b83103114fbdb7891a223e399`.

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

Milestone D is complete at repository-test level. Milestone E now has two CI-verified slices: canonical persisted evidence/uncertainty semantics at the decision boundary, plus truthful version/evidence provenance in decision reports and engine result UI.

Acceptance targets for Milestone E:
- audit the shared analysis request/result/decision models and UI so evidence, provenance, confidence, conflicts and UNKNOWN conditions are represented consistently rather than engine-by-engine ad hoc;
- ensure direct-state, provider-grounded and demo inputs remain distinguishable in persisted analysis/history/report outputs;
- make stale, partial, unavailable and conflicting evidence visible without converting uncertainty into a positive/negative recommendation;
- standardize version/methodology identifiers needed to reproduce or review an analysis;
- verify analysis/detail/report surfaces never claim provider evidence that was not actually used;
- keep workspace authorization and in-place switch isolation across every new analysis/result surface;
- add targeted API/domain/Playwright coverage and require full CI before advancing to Milestone F.

## Completed evidence

- Milestones A–D are complete at repository-test level; production/browser certification remains separately gated by real deployment evidence.
- Browser web auth uses HttpOnly cookies plus CSRF; no bearer token is introduced into browser storage.
- The authenticated shell is workspace-query-scoped; foreign workspace reads fail closed; delayed engine/monitor/investigation/protocol-history results cannot render after a switch.
- Dashboard/History/Saved/Settings surfaces are workspace-authorized and truthful; provider registry state remains separated from workspace runtime telemetry.
- Shared engine outputs persist `analysis_framework_version`; decisions persist `decision_methodology_version` plus analysis IDs, engine versions/statuses/framework versions, evidence providers/count, unresolved conflict count and canonical-persistence verification.
- Persisted `analysis_id` values are rehydrated from server-side analysis storage before decision scoring. Client-submitted changes to risk score, confidence, severity, blockers, warnings, conflicts or summary cannot override the stored analysis payload.
- Repeating one persisted analysis ID, or submitting multiple results from the same specialist engine, returns explicit UNKNOWN instead of silently changing aggregate weighting.
- Requested evidence in `PARTIAL`, `STALE_DATA`, `CONFLICTING_DATA`, provider-unavailable or other non-COMPLETED states remains WAIT/UNKNOWN until resolved, except where an explicit hard blocker independently requires AVOID.
- Grounded explanations expose decision methodology/provenance without generating a new risk score.
- API/domain regression coverage includes an adversarial forged-safe-payload test proving a high-risk persisted B2 result remains authoritative.
- PR #10 final head `c817b0a9774faf1612faa4da61269d3b99911e4d` passed CI run #144 (`35830902047`) and merged as `deca453077f51101ef853161d07836a26472778d`.
- Decision HTML/PDF now disclose methodology version, canonical-persistence verification, evidence count/sources, unresolved conflicts, specialist engine status/version/framework and persisted analysis references.
- Engine result UI now renders structured status/risk/confidence/version/evidence/conflict/missing-data/assumption fields and keeps raw normalized JSON behind an explicit disclosure rather than using raw JSON as the only result presentation.
- Engine result banners are derived from actual result state: demo, provider unavailable, partial, conflicting, stale, completed-with-recorded-evidence, or completed-with-no-recorded-evidence. A zero-evidence result is never called provider-grounded.
- Playwright proves a provider-unavailable result with zero evidence says no evidence is recorded, and a partial B5 result names `lifi` only because that provider appears in the returned evidence array.
- Report tests prove canonical verification wording is driven by the persisted flag and PDF generation remains self-contained.
- PR #11 final head `c57b93b89326922a1dab28d49b71199f1e20ed45` passed CI run #154 (`35831726073`) across API regression/audit, frontend type/build/vinext/audit/Playwright/Axe, invariants/secret checks and PostgreSQL migration/runtime-control certification.
- PR #11 merged to `main` as `5795344fea5b4e3b83103114fbdb7891a223e399`.

## Dependencies and blockers

- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval (or another explicitly approved FastAPI-capable platform).
- **Custom domain:** BLOCKED on user domain choice/purchase approval.
- **Production email:** BLOCKED on Brevo phone verification, owned domain, domain authentication and action-time credential approval.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths remain UNKNOWN/unavailable.
- **Production secrets:** creation/rotation requires action-time confirmation where specified by the project mandate.
- **Real deployed browser/auth certification:** BLOCKED until a live FastAPI runtime is available; repository-level browser/API evidence is not production evidence.
- **Production certification:** remains incomplete until real Rudra/Rivexis-owned targets supply external gate evidence.

## Next action

Finish the Milestone E audit by carrying persisted analysis status/provenance into workspace History without exposing raw payloads. History should distinguish demo/live, status, framework/engine version, evidence count/sources, provider consensus and conflict count using only canonical persisted fields; decision history should expose decision state/methodology/canonical-input verification where supported. Preserve the existing 50-record cap disclosure, workspace isolation and in-place switch behavior, then gate the slice on full CI before deciding whether Milestone E can advance to Milestone F.
