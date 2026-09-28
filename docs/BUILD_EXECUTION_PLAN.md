# Rivexis Build Execution Plan

Last updated: 2026-09-28
Authoritative mandate: complete Rivexis as institutional blockchain intelligence / crypto-finance risk decision infrastructure with truthful evidence semantics and production-backed actions.

## Verified baseline

- Repository: `rudras777/rivexis`, branch `main`.
- Latest fully certified product source: `6bf117154a958688697cc998530a65c9726e820f`.
- Exact-head CI: `36429614693` — SUCCESS.
- Exact-head Pages: `36429614899` — SUCCESS.
- Frontend: Next.js 16 / React 19 / TypeScript + vinext.
- Production compatibility backend: Supabase Edge `rivexis-api` v7 ACTIVE.
- Production database: Supabase project `ivszvufdonfgwjpfgwii`, PostgreSQL 17.6.1, hardened owner/RLS posture retained.
- Full provider-capable FastAPI source remains authoritative for deep provider functionality; Cloudflare Container deployment is Workers Paid gated.
- Authoritative Cloudflare web Worker remains the older manual deployment `e8922aac-cb84-435b-bd0c-38fbb886be57`; later source must not be described as live there.

## Completed functional slices

- browser auth, recovery, onboarding, workspace switching and organization creation;
- ten B1-B5/F1-F5 deterministic demonstration engines;
- UNKNOWN-safe live compatibility behavior;
- provider registry/runtime truth separation;
- monitor create/check workflow;
- protocol timeline/config compare/review/approval/PDF;
- investigation creation/link/update/disposition/PDF;
- Saved Analyses create/list/search/inspect/archive/restore/delete backed by production Edge v7 and hardened Postgres RPC;
- History search/type/mode filtering, provenance inspection and real Save-reference action;
- structured F1 `manual_positions` builder;
- structured F5 `allocations` ledger with explicit weight total and no silent normalization;
- guided F3 live liquidation inputs aligned to actual oracle/position backend requirements;
- institutional navy/blue/white visual system with contextual evidence graphics and reduced generic-card UI.

## Active milestone — organization membership parity

Full FastAPI already exposes:

- `GET /api/v1/organizations/{organization_id}/members`;
- `POST /api/v1/organizations/{organization_id}/members`;
- `POST /api/v1/organizations/{organization_id}/members/claim`;
- `DELETE /api/v1/organizations/{organization_id}/members/{user_id}`;
- `POST /api/v1/organizations/{organization_id}/membership-claim`.

The current free Supabase Edge compatibility runtime exposes organization list/create but not member administration. The Settings UI truthfully says member administration is not exposed.

### Acceptance targets

1. Inspect FastAPI/store authorization semantics and production schema before adding any compatibility action.
2. Preserve organization OWNER/ADMIN manager boundaries server-side; never trust a frontend role claim.
3. Direct member addition may only mirror the existing safe behavior for already-provisioned users unless an explicit secure invitation/claim path is implemented.
4. A non-manager must not list privileged administration data or mutate membership beyond the permissions intentionally supported.
5. Prevent removal of the last owner and other organization integrity violations already enforced by FastAPI/store semantics.
6. Edge state-changing routes must retain cookie authentication + CSRF.
7. Any privileged database function must have a pinned search path and minimum execute ACL; no `anon`, `authenticated` or PUBLIC execution.
8. Add focused database/API/browser tests for owner/admin/member/non-member boundaries.
9. Deploy database/Edge changes only after exact-head CI passes, then verify production health/protected-route behavior and logs.
10. Only after backend parity exists should Settings expose real member administration controls.

## Subsequent milestones

1. General analysis/report parity: extend only when FastAPI + Edge persistence/render contracts are real; no fake download/report controls.
2. Remaining organization/workspace role management with genuine backend support.
3. Monitor alert/event history and real delivery controls where delivery infrastructure exists.
4. Systematic route/button/form audit for dead actions, placeholder values and unsupported claims.
5. Provider-backed evidence depth only with approved credentials/contracts/licenses.
6. Promote exact certified web source to the existing Cloudflare Worker when legitimate authenticated access becomes available, then live-certify public/auth/workspace/Saved/History/engine workflows and browser console state.

## Non-negotiable integrity rules

- UNKNOWN for unsupported/unverified evidence.
- Never fabricate provider connectivity, provenance, data freshness or decisions.
- Preserve canonical RPC/ABI quantity validation and same-block consistency where claimed.
- Preserve tenant/workspace authorization and secure browser sessions.
- Do not weaken RLS/role posture to make a feature easier to deploy.
- Do not bypass Cloudflare human verification or use an alternate deployment provider.
- Do not make billing changes without explicit user authorization.

## Autonomous continuation loop

For every `continue`:

1. inspect newest `main` and preserve legitimate newer work;
2. confirm the real product/production gap;
3. implement the narrowest complete frontend/backend/database slice;
4. add action-level and authorization tests;
5. push without force/reset;
6. inspect/fix exact-head CI;
7. production-promote compatible backend/database changes only after certification;
8. live-verify reachable behavior and logs;
9. update durable state;
10. continue to the next highest-value unblocked slice.
