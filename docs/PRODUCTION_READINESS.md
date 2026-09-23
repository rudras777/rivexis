# Rivexis Production Readiness

Last updated: 2026-09-23

Allowed states: **PASS, FAIL, BLOCKED, NOT STARTED, NOT APPLICABLE**.

| Area | State | Evidence / blocker |
|---|---|---|
| Repository baseline and source control | PASS | Private repository; durable milestone evidence is maintained in-repo. |
| Durable execution planning | PASS | Build plan, deployment status, ten-engine contract audit and readiness matrix are maintained in-repo. |
| Ten-engine architecture | PASS | Repository preserves exactly B1–B5 and F1–F5 plus invariant coverage. Milestone F audits completion quality engine by engine. |
| Ten-engine live contract integrity | PASS | PRs #13–#15 normalize current live result/evidence versions and source consensus, fail closed on explicit F3 authoritative-adapter failure, and promote unresolved provider conflicts to `CONFLICTING_DATA`. Latest full gate: PR #15 CI #187 (`35836050226`). |
| Deterministic decision/UNKNOWN policy | PASS | Incomplete, stale, conflicting or unavailable requested evidence cannot become PROCEED/MODIFY/AVOID through aggregate scoring; it remains WAIT/UNKNOWN except where an explicit hard blocker independently requires AVOID. |
| Canonical persisted decision inputs | PASS | Persisted analysis IDs are rehydrated before decision scoring; adversarial API coverage proves a forged client copy cannot replace stored risk/confidence/blocker/conflict data. Duplicate analyses/engines cannot silently skew weighting. |
| Versioned analysis/decision provenance | PASS | Engine results persist analysis framework version; decisions persist methodology, analysis IDs, engine versions/statuses/framework versions, evidence sources/count, unresolved conflicts and canonical-input verification. |
| Analysis/report provenance presentation | PASS | Decision HTML/PDF and engine-result UI present versions, statuses, evidence and missing/conflicting states from returned/persisted fields without inventing provider grounding. |
| Persisted History provenance | PASS | PR #12 adds on-demand canonical analysis/decision provenance from existing authorized detail endpoints, without raw payload dumping or eager per-row fan-out. Detail is workspace-keyed and cleared on switch. |
| Milestone E — Analysis framework | PASS | PRs #10–#12 establish canonical evidence, fail-closed uncertainty semantics, versioned provenance and truthful engine/report/History presentation. PR #12 CI #164 (`35832725687`) is the final Milestone E repository gate. |
| Supabase project health | PASS | Project was verified `ACTIVE_HEALTHY` in `ap-south-1`. |
| Supabase schema/runtime controls | PASS | 53 product tables + 2 runtime-control tables; runtime-control migration present. |
| Supabase browser-role exposure review | PASS | Prior review found no explicit `anon`/`authenticated` table grants; re-check if grants/Data API exposure changes. |
| Frontend free preview | PASS | Public Cloudflare preview was reachable at last verification. |
| Honest free-tier API boundary | PASS | Free API preview reports degraded and application routes intentionally fail rather than simulating the FastAPI application. |
| Workspace shell/auth/session repository coverage | PASS | HttpOnly cookie + CSRF, fail-closed access states, session recovery/logout and workspace authorization are covered by API + Playwright tests. |
| Workspace collection/query isolation | PASS | Workspace-keyed queries and API authorization prevent foreign-workspace collection/detail reuse. |
| In-place workspace switching across audited tools | PASS | Engine, monitor, investigation, protocol-history and History provenance state are reset/guarded by workspace identity; browser tests prove old-workspace state cannot satisfy new-workspace views. |
| Provider state boundary | PASS | Global provider registry configuration remains separate from workspace runtime telemetry; absence remains explicit. |
| Current milestone CI | PASS | PR #15 final head `34f66a0abd9794efd9352b73e733212cc5a2a350` passed API, web/Playwright/Axe, invariants/secret scan and PostgreSQL migration/runtime-control CI #187 (`35836050226`). PR #13/#14 also passed full CI before merge. |
| Live deployment of current merged source | BLOCKED | Current source is CI-green but has not been independently verified on the Cloudflare Worker; no deployment claim is made. |
| Live FastAPI runtime | BLOCKED | Cloudflare Containers requires Workers Paid or another approved FastAPI-capable platform; no paid activation authorized. |
| Production custom domain/TLS | BLOCKED | No Rivexis production domain is configured. |
| Production auth secret installation | BLOCKED | Requires action-time production credential setup. |
| Least-privilege production API DB credential | BLOCKED | Final runtime credential must be configured into the live API environment. |
| Isolated production migration run | BLOCKED | Requires the real production deployment path/credential at launch. |
| Real browser auth/analysis E2E | BLOCKED | Repository harness is green, but the free preview has no live FastAPI runtime, so deployed end-to-end certification cannot be claimed. |
| Brevo transactional email | BLOCKED | Phone verification, owned domain, DKIM/SPF/DMARC review, credentials and real delivery verification remain. |
| Live provider certification | BLOCKED | Requires configured/licensed Rivexis-owned provider targets and credentials. |
| Arkham | BLOCKED | Must remain license-gated until explicit commercial approval. |
| Hypernative provider-native contract | BLOCKED | Requires an actual documented/customer webhook or API signing contract. |
| Production backup/restore exercise | NOT STARTED | Destructive restore must use an approved disposable target. |
| Production observability validation | BLOCKED | Runtime instrumentation exists; real deployment/export evidence is incomplete. |
| Performance/load certification | NOT STARTED | Must run against representative deployed infrastructure. |
| Accessibility/browser production certification | BLOCKED | Repository harness is green; deployed-browser evidence is incomplete. |
| Production release certification bundle | BLOCKED | External gates remain unavailable until real Rivexis-owned targets supply evidence. |
| Incident/runbook readiness | NOT STARTED | Required operational runbooks remain a future milestone. |

Milestone F remains active in `BUILD_EXECUTION_PLAN.md`; this readiness matrix records only controls that have reached one of the allowed terminal/readiness states above. The current ten-engine integrity controls are PASS, while deeper engine-capability completion continues under the active milestone plan.

## Launch rule

Rivexis must not be called production-ready while any launch-required item above is FAIL, BLOCKED or NOT STARTED. Repository CI, previews or skipped external certification are not production evidence.
