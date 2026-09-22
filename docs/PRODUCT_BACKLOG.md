# Rivexis Product Backlog

Last updated: 2026-09-23

This backlog is organized around user outcomes, not microtasks. Priority follows the dependency order in `BUILD_EXECUTION_PLAN.md`.

## Epic 1 — Trustworthy public and application shell

**User outcome:** A user can understand what Rivexis is, what is actually available, and whether application services are healthy before taking action.

Acceptance criteria:
- public claims distinguish illustrative, degraded, partial and live behavior;
- global service availability is accessible and non-color-only;
- navigation is responsive and keyboard usable;
- shared loading, empty, error, degraded, stale and partial states are consistent;
- no fake charts, live claims or provider connectivity.

## Epic 2 — Secure account and onboarding journey

**User outcome:** A user can create an account, establish a browser session, configure a workspace, recover from session failure and understand security limitations.

Acceptance criteria:
- signup/login/logout/session restoration/expiration work against the real FastAPI path in a runnable environment;
- HttpOnly cookie + CSRF protections are preserved;
- server-side authorization and no-account-enumeration behavior are tested;
- onboarding persists role/workspace state and supports safe retry/resume;
- recovery/verification is not represented as complete until real email delivery is configured.

## Epic 3 — Workspace foundations

**User outcome:** An authorized user can enter the correct organization/workspace and see relevant recent activity, provider state, history and settings.

Acceptance criteria:
- organization/workspace selection is role-aware;
- unauthorized/revoked users lose downstream access;
- overview, provider status, saved analyses and history have search/filter/pagination where needed;
- failures and partial evidence remain explicit.

## Epic 4 — Common analysis lifecycle

**User outcome:** Every analysis behaves consistently from validated input through evidence, decision, history and report.

Acceptance criteria:
- shared typed lifecycle covers draft/validation/running/result/review/save/report;
- normalized outputs preserve provenance, freshness, conflicts, assumptions and missing data;
- deterministic policy version and engine version are visible;
- canonical decisions remain PROCEED/MODIFY/WAIT/AVOID/UNKNOWN;
- no engine can silently convert unavailable evidence into a confident result.

## Epic 5 — Ten specialist engines

**User outcome:** Users can run B1–B5 and F1–F5 with engine-specific validated inputs and evidence-grounded outputs.

Acceptance criteria:
- each engine has a real input contract, validation and explicit supported-chain/provider state;
- direct/deterministic evidence is preferred where available;
- external assertions stay attributed;
- unavailable commercial/provider paths return partial/UNKNOWN/unavailable;
- each engine integrates with saved analyses, history and reporting.

## Epic 6 — Monitoring, alerts, investigations and reports

**User outcome:** Users can revisit analyses, monitor defined conditions, investigate related evidence and export authorized reports.

Acceptance criteria:
- monitor lifecycle supports create/edit/pause/resume/delete;
- alert retry/dead-letter/requeue/deduplication remains durable and audited;
- investigations group artifacts without erasing provenance;
- JSON/HTML/PDF outputs preserve evidence, limitations and versions;
- downloads are authorized and private.

## Epic 7 — Institutional access controls

**User outcome:** Organization owners/admins can safely manage members, roles, policy and review without tenant leakage.

Acceptance criteria:
- invitation/claim flow is identity-safe and audited;
- OWNER authority constraints remain enforced;
- maker/reviewer workflows exist only where product value justifies them;
- RLS and application authorization are both tested for revocation and cross-tenant isolation.

## Epic 8 — Production operations and launch

**User outcome:** Rivexis can be deployed and operated with truthful availability, rollback and incident response.

Acceptance criteria:
- paid/API hosting is activated only with explicit approval;
- exact HTTPS origin, least-privilege database role and production auth secret are installed;
- custom domain, Brevo domain authentication and real inbox delivery are verified;
- provider certifications use Rivexis-owned targets;
- backup/restore, observability, performance, accessibility and security gates are evidence-backed;
- launch occurs only when `PRODUCTION_READINESS.md` has no unresolved required FAIL/BLOCKED items.
