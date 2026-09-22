# Rivexis Production Readiness

Last updated: 2026-09-23

Allowed states: **PASS, FAIL, BLOCKED, NOT STARTED, NOT APPLICABLE**.

| Area | State | Evidence / blocker |
|---|---|---|
| Repository baseline and source control | PASS | Private repo, `main` verified at `daa5cc1` before this milestone. |
| Durable execution planning | PASS | Build plan, backlog, architecture decisions, deployment status and this readiness matrix are now maintained in-repo. |
| Ten-engine architecture | PASS | Repository preserves exactly B1–B5 and F1–F5 plus existing invariant coverage. |
| Deterministic decision/UNKNOWN policy | PASS | Existing domain and verification docs/tests preserve explicit UNKNOWN and evidence-first outcomes. |
| Supabase project health | PASS | Project is `ACTIVE_HEALTHY` in `ap-south-1`. |
| Supabase schema/runtime controls | PASS | 53 product tables + 2 runtime-control tables; runtime-control migration present. |
| Supabase browser-role exposure review | PASS | Security advisor has no findings; direct check found no explicit `anon`/`authenticated` table grants. Re-check if grants/Data API exposure changes. |
| Frontend free preview | PASS | Public site reachable on Cloudflare Workers. |
| Honest free-tier API boundary | PASS | `/health` reports degraded and application routes are designed to return 503 rather than fake FastAPI behavior. |
| Global degraded-service UX | PASS | Root-level health check and accessible degraded/unverifiable disclosure implemented; Playwright coverage passed in CI run #21. |
| Current milestone CI | PASS | CI run #21 passed API, web/Playwright, invariants/secret scan and PostgreSQL migration/runtime-control jobs. |
| Live deployment of current milestone | BLOCKED | Source is CI-green but this change has not yet been verified on the Cloudflare Worker; no deployment action is claimed. |
| Live FastAPI runtime | BLOCKED | Cloudflare Containers requires Workers Paid; no paid activation authorized. |
| Production custom domain/TLS | BLOCKED | No domain owned/configured for Rivexis. |
| Production auth secret installation | BLOCKED | Requires action-time production credential setup. |
| Least-privilege production API DB credential | BLOCKED | Role model exists; final runtime credential must be configured into the live API environment. |
| Isolated production migration run | BLOCKED | Requires the real production deployment path/credential at launch. |
| Real browser auth/onboarding E2E | BLOCKED | No live FastAPI runtime on the current free preview. |
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
