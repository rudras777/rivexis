# Rivexis Current Build State

Last updated: 2026-09-28

This is the compact authoritative continuation point. The newest verified GitHub `main`, production Supabase state, and authoritative Cloudflare Worker state override older notes.

## Repository and certification

- Repository: `rudras777/rivexis`; branch `main`.
- Current certified source head: `59dadde0edb1c58ea2b22f421c26d4509bbab7f2` (`Preserve migrator role posture during edge migration`).
- Exact-head CI: run `36421346582` — **SUCCESS**.
- Exact-head GitHub Pages: run `36421345772` — **SUCCESS**.
- Pages remains a fallback/navigation deployment; it is not the authoritative application runtime.
- The current source includes all previously certified auth, workspace, provider/monitor, protocol-review/investigation, ten-engine demonstration, evidence-truth, visual-system and workspace-switch isolation work.

## Latest completed production slice — Saved Analyses

Saved Analyses is no longer a read-only source surface.

Repository source now supports:

- active/all visibility filtering, including archived references;
- search by saved-analysis metadata;
- inspection of the persisted canonical analysis/evidence record;
- archive and restore;
- deletion of the saved reference while retaining the underlying analysis in workspace history;
- POST save support in the compatibility API;
- CSRF-protected PATCH/DELETE actions;
- action-level Playwright coverage for inspect/archive/restore/search/delete.

The initial action test exposed only a Playwright strict-selector ambiguity; the application build, API suite, PostgreSQL lane and the other 58 browser tests were green. The selector was corrected and the final release head passed the full CI matrix.

### Production persistence bridge

Production Supabase now contains `public.rivexis_edge_saved_analysis(text,text,jsonb)`.

Verified post-deployment security posture:

- owner: `rivexis_migrator`;
- `SECURITY DEFINER` enabled;
- fixed `search_path=pg_catalog, public`;
- execute ACL restricted to the owner and `service_role` only;
- no execute grant for `anon`, `authenticated` or `PUBLIC`;
- every saved-analysis action rechecks the authenticated actor and workspace membership;
- `rivexis_migrator` remains `NOLOGIN`;
- the temporary PostgreSQL `SET ROLE rivexis_migrator` capability used during installation was revoked after the migration.

The production migration path records `add_saved_analysis_actions` after the earlier compatibility-runtime migrations. A prior ownership-transfer attempt failed safely because production PostgreSQL could not SET the hardened migrator role; that failed transaction left no partial function. The corrected migration temporarily grants SET, creates the function under `rivexis_migrator`, resets role, and removes SET again.

### Production Edge API

Supabase Edge function `rivexis-api` is now **version 7 ACTIVE**. `verify_jwt=false` remains deliberate because this function performs its own Supabase-authenticated HttpOnly session-cookie validation plus CSRF protection for state-changing browser requests.

Version 7 includes:

- `GET /api/v1/saved-analyses?workspace_id=...&include_archived=...`;
- `POST /api/v1/saved-analyses`;
- `PATCH /api/v1/saved-analyses/{saved_id}?archived=true|false`;
- `DELETE /api/v1/saved-analyses/{saved_id}`.

Post-deployment live checks verified:

- direct Edge `/health` returns HTTP 200 and `ready`, `supabase-edge`, API `v1`, `production`;
- unauthenticated Saved Analyses access returns HTTP 401 `Authentication required`;
- the Cloudflare Worker `/health` still returns HTTP 200 with the same Supabase Edge production runtime;
- Supabase function logs identify deployment version 7 serving the successful health request and the expected protected-route 401, with no runtime exception surfaced in the post-deploy checks.

A real authenticated production archive/restore/delete mutation has not yet been claimed in this continuation. Browser action behavior is CI-certified and the production persistence/API contract is deployed; live authenticated mutation certification remains a valid follow-up when an authenticated test session is available.

## Production PostgreSQL

Supabase project: `ivszvufdonfgwjpfgwii`.

- PostgreSQL 17.6.1; project remains healthy.
- Core Alembic application schema remains at `0013_auth_email_lifecycle` with the previously certified tenant/RLS/index posture.
- 56 application tables and the existing owner-scoped hardening remain preserved.
- `rivexis_edge_bridge(text,text,jsonb)` remains the narrow service-role bridge for the Supabase Edge compatibility runtime.
- `rivexis_edge_saved_analysis(text,text,jsonb)` now supplies the isolated saved-reference CRUD contract without reopening direct table access.
- `rivexis_migrator` and `rivexis_app` remain non-login roles in the inspected production posture.

Supabase Auth leaked-password protection remains an explicit hardening item unless it can be enabled without an unapproved billing change.

## Production frontend

Authoritative public frontend:

`https://rivexis-web.rudrasingh0718.workers.dev/`

The authoritative Cloudflare web Worker still serves the previously certified manual deployment, Worker version `e8922aac-cb84-435b-bd0c-38fbb886be57`.

**Important source-truth boundary:** GitHub source is substantially ahead of that Worker. The current institutional UI, provider/monitor refinements, protocol evidence operations, Saved Analyses action UI and other later source slices are repository/CI/Pages certified but are not claimed as deployed to the authoritative Worker.

Deployment remains blocked in this execution environment because Wrangler is unauthenticated and the Cloudflare dashboard remained behind human verification after the permitted safe attempt. No alternate host, temporary account, verification bypass or billing change has been used. Production therefore continues to serve the older certified web bundle while proxying to the now-updated Supabase Edge v7 backend.

## Authentication and session security

Production auth remains available through Supabase Auth + the Edge compatibility runtime:

- signup and email verification;
- login;
- HttpOnly/Secure/SameSite=Lax browser session cookie;
- CSRF for state-changing requests;
- session restoration/refresh;
- logout/protected-route denial;
- password-reset request/confirm;
- workspace onboarding and organization creation.

Recovery bearer tokens remain memory-only and are removed from the browser URL before password entry.

Supabase custom SMTP remains connected to the Brevo free relay. Production recovery delivery was previously verified through Supabase Auth and independently recorded by Brevo as Sent and Delivered. The sender still lacks a Rivexis-owned authenticated domain.

## Engine and evidence integrity

All B1-B5/F1-F5 integrity contracts remain intact. Current source continues to preserve deterministic demonstration behavior and fail-closed live behavior:

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

The free runtime does not fabricate provider evidence. Without verified provider connectivity, live engine execution remains `UNKNOWN` with zero invented evidence. Demonstration outputs remain explicitly synthetic and attributed.

## Current execution gates

1. **Cloudflare frontend source drift:** current source cannot be promoted until authenticated Cloudflare access is available; do not bypass human verification.
2. **Full FastAPI/provider runtime:** Cloudflare Container deployment remains gated on explicit Workers Paid authorization.
3. **Provider credentials/contracts:** unavailable/licensing-gated evidence stays UNKNOWN/unavailable.
4. **Owned sender domain:** Brevo/Supabase delivery works, but Rivexis does not yet have an authenticated owned sending domain.

## Next execution order

1. Institutionalize **History and general report workflows** end-to-end: search/filter/open canonical analysis, save/reference actions, and only report actions that are backed by real FastAPI + Supabase Edge persistence/rendering contracts.
2. Add missing compatibility-runtime backend work before exposing any new frontend action; no frontend-only mock controls.
3. Continue structured multi-row builders for portfolio/position/treasury workflows where they materially improve F1/F3/F5 usability without weakening canonical input validation.
4. Deploy the latest certified web source to the existing `rivexis-web` Worker as soon as legitimate Cloudflare authentication is available, then live-certify public/auth/workspace/Saved/History/report flows, responsive UI and browser console state.
5. Add provider-backed evidence depth only with approved credentials/licenses and preserve UNKNOWN otherwise.
