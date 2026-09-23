# Rivexis Production Readiness

Last updated: 2026-09-23

Allowed states: **PASS, FAIL, BLOCKED, NOT STARTED, NOT APPLICABLE**.

| Area | State | Evidence / blocker |
|---|---|---|
| Repository baseline and source control | PASS | Private repo, `main` verified at `daa5cc1` before this milestone. |
| Durable execution planning | PASS | Build plan, backlog, architecture decisions, deployment status and this readiness matrix are maintained in-repo. |
| Ten-engine architecture | PASS | Repository preserves exactly B1–B5 and F1–F5 plus existing invariant coverage. |
| Deterministic decision/UNKNOWN policy | PASS | Incomplete, stale, conflicting or unavailable requested evidence no longer becomes PROCEED/MODIFY/AVOID through aggregate scoring; it remains WAIT/UNKNOWN except where an explicit hard blocker independently requires AVOID. |
| Canonical persisted decision inputs | PASS | PR #10 rehydrates persisted analysis IDs before decision scoring; adversarial API coverage proves a forged client copy cannot replace stored risk/confidence/blocker/conflict data. Duplicate analysis IDs or duplicate specialist engines cannot silently skew aggregate weighting. |
| Versioned analysis/decision provenance | PASS | Engine results persist `analysis_framework_version`; decisions persist `decision_methodology_version`, analysis IDs, engine versions/statuses/framework versions, evidence sources/count, unresolved conflict count and canonical-persistence verification. Grounded explanations expose the same provenance. |
| Analysis/report provenance presentation | NOT STARTED | Canonical provenance now exists in the API model, but decision HTML/PDF and the engine-result UI still need structured, truthful presentation of versions, status, evidence sources, conflicts and missing data. |
| Supabase project health | PASS | Project is `ACTIVE_HEALTHY` in `ap-south-1`. |
| Supabase schema/runtime controls | PASS | 53 product tables + 2 runtime-control tables; runtime-control migration present. |
| Supabase browser-role exposure review | PASS | Security advisor has no findings; direct check found no explicit `anon`/`authenticated` table grants. Re-check if grants/Data API exposure changes. |
| Frontend free preview | PASS | Public site reachable on Cloudflare Workers. |
| Honest free-tier API boundary | PASS | `/health` reports degraded and application routes are designed to return 503 rather than fake FastAPI behavior. |
| Global degraded-service UX | PASS | Root-level health check and accessible degraded/unverifiable disclosure implemented; retained through current CI. |
| Workspace shell access-state UX | PASS | Loading, zero-workspace, 401 session-ended, 403 access-unavailable and 503/generic service failure paths fail closed; targeted Playwright coverage passed. |
| Responsive/keyboard shell UX | PASS | Skip link, focus-visible treatment, `aria-current`, narrow-view navigation/logout and mobile recovery states are covered; authenticated shell Axe has no serious/critical blockers after the logout contrast correction. |
| Browser auth/onboarding repository coverage | PASS | HttpOnly-cookie/CSRF architecture, non-enumerating login/signup behavior, safe browser error copy, submit locking, existing-workspace resume, hard-reload CSRF recovery and ambiguous-create reconciliation are covered by API + Playwright tests. |
| Browser session lifecycle repository coverage | PASS | Hard-reload workspace continuity, CSRF recovery for logout, duplicate-submit locking, confirmed logout cleanup, already-revoked 401 cleanup, post-logout fail-closed access, generic non-401 logout failure handling, revoked-session CSRF rejection and invalid-CSRF non-revocation are covered by API + Playwright tests. |
| Workspace collection/query isolation | PASS | Authenticated workspace context and workspace-keyed query namespace are implemented; History and Saved Analyses explicitly carry active workspace IDs; API + Playwright coverage proves foreign-workspace reads fail closed and old collection data is not reused across workspace switches. |
| Provider state boundary | PASS | Shared/global provider registry configuration is separated from active-workspace runtime telemetry; empty runtime state is explicit and no provider activity/readiness is fabricated. |
| In-place workspace switching across audited tools | PASS | Engine, monitor, investigation and protocol-history local result state is reset/guarded by workspace identity; delayed old-workspace responses are discarded and Playwright proves no reload is used to obtain isolation. |
| Workspace dashboard/activity/settings completion | PASS | Dashboard separates static product metadata from authorized active-workspace History activity; History and Saved Analyses use supported-field summaries; Settings lists authorized workspace/organization data, membership roles and creation outcomes without implying unsupported member administration. PR #9 browser coverage preserves in-place switch isolation across these surfaces. |
| Current milestone CI | PASS | PR #10 CI run #144 (`35830902047`) passed API, web/Playwright/Axe, invariants/secret scan and PostgreSQL migration/runtime-control jobs. |
| Live deployment of current milestone | BLOCKED | Source is CI-green but this change has not yet been verified on the Cloudflare Worker; no deployment action is claimed. |
| Live FastAPI runtime | BLOCKED | Cloudflare Containers requires Workers Paid; no paid activation authorized. |
| Production custom domain/TLS | BLOCKED | No domain owned/configured for Rivexis. |
| Production auth secret installation | BLOCKED | Requires action-time production credential setup. |
| Least-privilege production API DB credential | BLOCKED | Role model exists; final runtime credential must be configured into the live API environment. |
| Isolated production migration run | BLOCKED | Requires the real production deployment path/credential at launch. |
| Real browser auth/onboarding/session E2E | BLOCKED | Repository-level browser/API evidence is green, but the current free preview has no live FastAPI runtime, so deployed browser certification cannot be claimed. |
| Brevo transactional email | BLOCKED | Phone verification, owned domain, DKIM/SPF/DMARC review, credentials and real Gmail delivery verification remain. |
| Live provider certification | BLOCKED | Requires configured/licensed Rivexis-owned provider targets and credentials. |
| Arkham | BLOCKED | Must remain license-gated until explicit commercial approval. |
| Hypernative provider-native contract | BLOCKED | Requires actual documented/customer webhook or API signing contract. |
| Production backup/restore exercise | NOT STARTED | Procedure tooling exists; destructive restore must use an approved disposable target. |
| Production observability validation | BLOCKED | Runtime instrumentation exists; real deployment/export target evidence is not complete. |
| Performance/load certification | NOT STARTED | Must run against representative deployed infrastructure. |
| Accessibility/browser production certification | BLOCKED | Repository harness exists; full deployed-browser evidence is not complete. |
| Production release certification bundle | BLOCKED | External gates remain unavailable/SKIP until real Rudra/Rivexis-owned targets supply evidence. |
| Incident/runbook readiness | NOT STARTED | Required runbooks remain a future operational milestone. |

## Launch rule

Rivexis must not be called production-ready while any launch-required item above is FAIL, BLOCKED or NOT STARTED. A deployed preview, local PASS or skipped external certification is not production evidence.
