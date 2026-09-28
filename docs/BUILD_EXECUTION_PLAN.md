# Rivexis Build Execution Plan

Last updated: 2026-09-28
Authoritative project mandate: Rivexis “Complete Website, Full Functionality & World-Class Institutional UI/UX Master Prompt”.

## Current verified baseline

- Repository: `rudras777/rivexis`; default branch `main`.
- Latest product/backend release source before documentation-only state recording: `59dadde0edb1c58ea2b22f421c26d4509bbab7f2`.
- Exact release CI: `36421346582` — SUCCESS.
- Exact release Pages run: `36421345772` — SUCCESS.
- Frontend: Next.js 16 / React 19 / TypeScript using vinext for Cloudflare Workers.
- Full provider-capable backend: FastAPI source remains authoritative for complete provider depth, but its Cloudflare Container path is Workers Paid gated.
- Free production compatibility backend: Supabase Edge `rivexis-api` **version 7 ACTIVE**.
- Production database: Supabase project `ivszvufdonfgwjpfgwii`, PostgreSQL 17.6.1, hardened owner/RLS posture retained.
- Browser auth: HttpOnly/Secure/SameSite=Lax cookie + CSRF; recovery tokens remain memory-only.
- Demonstration engines B1-B5/F1-F5 remain deterministic and explicitly synthetic; live execution remains UNKNOWN without verified provider evidence.
- Authoritative Cloudflare web Worker remains on manual version `e8922aac-cb84-435b-bd0c-38fbb886be57`; GitHub source is newer and must not be claimed live until authenticated Cloudflare deployment succeeds.

## Completed production capabilities

### Authentication / tenancy

- signup, verification, login, session refresh, logout and protected-route denial;
- password reset request/confirm;
- workspace onboarding and switching;
- organization creation and membership-aware access;
- same-origin frontend API proxy to Supabase Edge.

### Analysis and evidence

- all ten B1-B5/F1-F5 engine routes;
- normalized provenance/evidence metadata;
- explicit provider conflicts, missing data and UNKNOWN-safe behavior;
- canonical persisted analysis detail and history provenance inspection;
- provider registry/runtime truth separation;
- manual B3 monitor creation/check workflow;
- protocol timeline/configuration comparison truth states;
- persisted protocol reviews, approval and PDF rendering;
- investigation creation, review linking, lifecycle/disposition and PDF rendering.

### Saved Analyses

Completed source and production backend contract:

- search;
- active/all archived visibility;
- inspect persisted analysis/evidence;
- create/save reference;
- archive/restore;
- delete saved reference without deleting the underlying analysis;
- CSRF-protected Edge POST/PATCH/DELETE routes;
- hardened `rivexis_edge_saved_analysis` service-role persistence bridge.

Production checks confirm Edge v7 health and unauthenticated 401 protection. Authenticated live archive/restore/delete certification remains a follow-up; CI/browser action coverage is green.

### Institutional UI system

Source contains the current navy/blue/white institutional visual language:

- subtle off-white and translucent surfaces;
- technical topology/evidence SVG environments for public/auth/workspace contexts;
- refined action geometry and reduced generic card repetition;
- editorial/ruled data surfaces and tables;
- institutional engine terminal/list patterns;
- responsive public/authenticated layouts.

This current UI source is not yet claimed on the authoritative Cloudflare Worker because of the authentication/human-verification deployment gate.

## Active product milestone

**History, general reports and remaining operational actions**

The priority is no longer simply “ten engines exist.” The master mandate is full website functionality. The next work therefore closes user-visible operational gaps around persisted analysis history, reporting and reusable institutional workflows while preserving evidence truth.

### Acceptance targets for the active milestone

- History must support useful search/filtering rather than a passive table only.
- Users must be able to open the canonical persisted analysis record from History.
- Save/reference actions must use the real Saved Analyses persistence API.
- Any general report action exposed in UI must have a real FastAPI and Supabase Edge persistence/rendering contract; no frontend-only fake download button.
- Report payloads must preserve canonical analysis identity, engine/version/provenance and explicit uncertainty.
- Deleting a saved reference must never silently delete canonical history.
- All write actions must retain CSRF and tenant/workspace authorization.
- Workspace switching must discard stale detail/report responses.
- Browser tests must validate action behavior, not only visual presence.
- Production Edge changes must be deployed and postflight verified before being described as live.
- Cloudflare web deployment truth must remain separate from backend deployment truth until the new source is genuinely promoted.

## Subsequent product work

After History/reports:

1. structured multi-row F1 portfolio builder;
2. richer F3 position inputs where they remain bounded/canonical;
3. structured F5 treasury allocation/scenario builder;
4. remaining organization/member/role controls that have real backend support;
5. monitor alert/event history and alert delivery only where a genuine delivery backend exists;
6. systematic audit of every route/button/form for dead actions, placeholder data and unsupported claims;
7. deeper provider evidence only with approved credentials/licenses.

## Engine integrity retained

Current engine contract / calculation versions:

- B1 `1.3.0` / `b1-live-1.8.0`;
- B2 `1.1.0` / `b2-live-1.3.0`;
- B3 `1.1.0` / `b3-live-1.3.0`;
- B4 `1.0.0` / `b4-live-1.1.0`;
- B5 `1.2.0` / `b5-live-1.4.0`;
- F1 `1.2.0` / `f1-live-1.4.0`;
- F2 `1.2.0` / `f2-live-1.4.0`;
- F3 `1.3.0` / `f3-live-1.3.0`;
- F4 `1.2.0` / `f4-live-1.3.0`;
- F5 `1.2.0` / `f5-live-1.3.0`.

Do not weaken:

- canonical RPC/ABI quantity validation;
- same-block direct-state consistency where a block is claimed;
- provider-specific provenance/freshness boundaries;
- conflict-first semantics;
- bounded payload/input validation;
- UNKNOWN for unsupported/unverified evidence;
- tenant/workspace authorization;
- secure browser session handling.

## Current external gates

- **Cloudflare web source deployment:** blocked until legitimate authenticated Wrangler/dashboard access is available. Human verification must not be bypassed.
- **Full provider-capable FastAPI deployment:** blocked on explicit Workers Paid authorization.
- **Custom/owned domain:** not configured/owned for release purposes in this execution state.
- **Owned email sender domain:** not authenticated; current Supabase/Brevo transport works but sender-domain hardening remains.
- **External providers:** credentials, licensing and customer-specific contracts remain explicit gates. Arkham and similar intelligence providers must not be simulated.

## Autonomous continuation loop

For every `continue` request:

1. inspect newest GitHub `main` and preserve legitimate newer work;
2. inspect the real implementation and production state relevant to the next gap;
3. reproduce/confirm the functional deficit;
4. implement frontend + backend/database work together where required;
5. add focused action-level tests;
6. push to `main` without force/reset;
7. inspect/fix exact-head CI;
8. deploy production-compatible backend/database changes when certified;
9. live-verify reachable production behavior and logs;
10. update durable state;
11. immediately start the next highest-value unblocked functionality slice.

## Immediate next action

Audit `workspace/history` and the general report APIs across FastAPI + Supabase Edge. Implement the highest-value missing History/report workflow end-to-end, including real persistence/rendering support before exposing any new action. Then full-CI gate and production-promote compatible backend changes. Keep the current Cloudflare frontend drift explicit until authenticated deployment is possible.
