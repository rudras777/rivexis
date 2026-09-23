# Rivexis Build Execution Plan

Last updated: 2026-09-23  
Authoritative project mandate: `Rivexis_Master_Build_Prompt.txt`

## Current verified baseline

- Repository: private `rudras777/rivexis`; default branch `main`.
- Frontend: Next.js 16 / React 19 / TypeScript on Cloudflare Workers using vinext.
- API: FastAPI is the authoritative application backend. The free Cloudflare Worker API is an explicit degraded placeholder, not a replacement runtime.
- Supabase project `ivszvufdonfgwjpfgwii` is `ACTIVE_HEALTHY` in `ap-south-1`; 53 logical product tables plus 2 runtime-control tables were previously verified.
- CI covers API lint/tests/audit, frontend type/build/vinext/audit/Playwright/Axe, invariants/secret/migration checks, and real PostgreSQL migration/runtime-control checks.
- Milestone D final workspace-foundation slice: PR #9, CI #129 (`35828771358`), merge `22a999d018e8c84dd907d48a973d58406aa5ed33`.
- Milestone E decision-integrity slice: PR #10, CI #144 (`35830902047`), merge `deca453077f51101ef853161d07836a26472778d`.
- Milestone E report/engine provenance slice: PR #11, CI #154 (`35831726073`), merge `5795344fea5b4e3b83103114fbdb7891a223e399`.
- Milestone E History provenance slice: PR #12 final head `b7c3b7e3c974ea901c3d920278b1c42f6396fcbc`, CI #164 (`35832725687`), merge `ad136be86f8536bbd5d2e917d7dc8a086b376ac4`.

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

**Milestone F — Ten-engine completion**

Milestone E is complete at repository-test level. The shared analysis/decision framework now preserves canonical evidence, uncertainty, versioning and provenance from persisted engine output through decisioning, explanations, reports, engine-result UI and workspace History.

### Milestone F acceptance targets

- audit all ten specialist engines B1–B5 and F1–F5 against their intended live-provider/direct-state contracts, deterministic/demo behavior and current tests;
- identify exact repository-level gaps rather than treating absent commercial credentials as code defects;
- ensure each engine has a versioned output contract, explicit evidence/provider provenance, deterministic missing-data semantics and safe `PARTIAL`, `STALE_DATA`, `CONFLICTING_DATA`, `PROVIDER_UNAVAILABLE` or other UNKNOWN-compatible states where evidence is incomplete;
- prohibit synthetic provider facts, unsupported “safe” conclusions and silent fallback from live mode to demo assumptions;
- verify engine-specific hard blockers, confidence, evidence freshness and provider consensus are reproducible and covered by focused tests;
- preserve workspace authorization, canonical persistence, decision integrity and in-place switch isolation;
- keep license/customer-contract gated providers such as Arkham or undocumented Hypernative-native contracts explicitly blocked rather than fabricating integration behavior;
- require full CI before declaring the ten-engine repository implementation complete enough to advance to Milestone G.

## Milestone E completed evidence

- `analysis_framework_version` is persisted on shared engine outputs and `decision_methodology_version` on decisions.
- Decisions rehydrate persisted `analysis_id` records before scoring. Caller-supplied changes to risk, confidence, severity, blockers, warnings, conflicts or summary cannot override canonical stored evidence.
- Duplicate persisted analysis references and duplicate specialist-engine inputs cannot silently distort aggregate weighting; the shared decision model returns explicit UNKNOWN.
- Requested non-COMPLETED evidence—including partial, stale, conflicting or provider-unavailable results—cannot become PROCEED/MODIFY/AVOID through aggregate scoring. It remains WAIT/UNKNOWN unless an explicit hard blocker independently requires AVOID.
- Decisions persist analysis IDs, engine versions/statuses/framework versions, evidence providers/count, unresolved conflicts and canonical-persistence verification. Grounded explanations expose the same provenance without generating a new score.
- Decision HTML/PDF reports expose methodology/canonical-input verification and specialist/evidence provenance from the persisted decision payload only.
- Engine result UI distinguishes demo, provider-unavailable, partial, conflicting, stale, completed-with-evidence and completed-with-no-recorded-evidence states. Provider names are displayed only when present in returned evidence.
- Workspace History keeps the capped summary endpoint lightweight and loads canonical persisted analysis/decision provenance only on user request through existing authorized detail endpoints; raw payloads are not dumped in the History view.
- History provenance detail queries are active-workspace keyed and selected detail is cleared on workspace changes. Playwright proves Workspace A provenance does not remain visible after switching to Workspace B.
- PR #12 initially exposed a TypeScript closure-narrowing issue; it was corrected without changing behavior, and only the subsequent full-green CI #164 is accepted as merge evidence.

## Existing platform integrity retained

- Browser auth uses HttpOnly cookies plus CSRF; browser bearer-token storage is not introduced.
- Workspace reads/writes fail closed and remain permission-aware.
- Engine/monitor/investigation/protocol-history delayed responses from an old workspace are discarded after switching.
- Shared/global provider registry configuration is separate from active-workspace runtime telemetry.
- Product constants are labeled as static metadata; workspace activity comes from authorized workspace APIs.
- External/provider absence remains explicit UNKNOWN/unavailable rather than fabricated evidence.

## Dependencies and blockers

- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval or another explicitly approved FastAPI-capable platform.
- **Custom domain:** BLOCKED on user domain choice/purchase approval.
- **Production email:** BLOCKED on Brevo phone verification, owned domain, domain authentication and action-time credential approval.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths remain UNKNOWN/unavailable.
- **Production secrets:** creation/rotation requires action-time confirmation where specified by the project mandate.
- **Real deployed browser/auth/analysis certification:** BLOCKED until a live FastAPI runtime is available; repository-level browser/API evidence is not production evidence.
- **Production certification:** incomplete until real Rudra/Rivexis-owned targets supply external gate evidence.

## Next action

Start Milestone F with a ten-engine contract audit. Build a precise B1–B5/F1–F5 matrix covering engine version, live evidence source(s), direct-state versus indexed/provider evidence, provider-unavailable behavior, partial/conflict/stale semantics, hard blockers, freshness/confidence and current tests. Patch the highest-risk engine inconsistency first, add focused regression coverage, and gate every slice on full CI.
