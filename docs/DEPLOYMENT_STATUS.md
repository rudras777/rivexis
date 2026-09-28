# Rivexis Deployment Status

Last updated: 2026-09-29

| Environment | Status | Evidence / meaning |
|---|---|---|
| GitHub product source | CERTIFIED | Product source `859073b02c43df7b4ea373e277b450e213af8041` passed exact-head CI `36477406619`. |
| GitHub Pages | FALLBACK ONLY | Exact-head Pages run `36477405771` passed, but Pages is not the authoritative application runtime. |
| Cloudflare web | LIVE / EXACT SOURCE | `rivexis-web.rudrasingh0718.workers.dev` serves exact source `859073b02c43df7b4ea373e277b450e213af8041` as Worker version `d4d4ed6e-bdcb-4c77-9701-1ecbd8407da5`; the public build marker, official assets, auth/workspace surfaces and proxied health endpoint were verified after deployment with clean browser consoles. |
| Supabase Edge API | LIVE / V8 | `rivexis-api` version 8 ACTIVE with HttpOnly-cookie + CSRF auth and the certified compatibility workflows. |
| Supabase PostgreSQL | LIVE / HARDENED | Project `ivszvufdonfgwjpfgwii`, PostgreSQL 17.6.1; core schema through `0013_auth_email_lifecycle`; hardened runtime bridges retained. |
| Full FastAPI runtime | SOURCE READY / BILLING GATED | Deep provider-capable container deployment remains gated on explicit Workers Paid authorization. |
| Brevo / Supabase email | LIVE / READY | Recovery delivery previously verified Sent + Delivered. Scheduled alert delivery now reports `SCHEDULED_READY` / `BREVO_READY` with encrypted Supabase Edge secrets; controlled alert acceptance/inbox proof and an owned authenticated sender domain remain outstanding. |

## Latest certified source capabilities

The certified GitHub source now includes:

- official production wordmark, lockup, X mark, favicon and social metadata assets derived from the supplied authoritative package;
- a brand-derived navy, cobalt, ice-blue, pearl and institutional-canvas token system shared across public, auth and authenticated surfaces;
- the official `Risk · Value · Execution · Analysis` identity, restrained X-mark topology treatments and tested desktop/mobile asset rendering;
- operational History search/type/mode filters, provenance inspection and real Saved-reference creation;
- authoritative saved-state detection that marks active or archived references as Saved and blocks duplicate persistence requests;
- grouped Command, Operations, Evidence and Infrastructure navigation with independently scrollable short-viewport access;
- Saved Analyses search/inspect/archive/restore/delete;
- structured F1 portfolio-position builder preserving canonical `manual_positions`;
- guided F3 liquidation/oracle evidence inputs aligned to the real FastAPI contract;
- structured F5 treasury allocation ledger preserving exact weights and canonical `allocations`;
- existing institutional UI/UX, provider/monitor, protocol-review/investigation and ten-engine source functionality.

These capabilities are source/CI certified and live on the authoritative Cloudflare Worker at the exact build SHA above.

## Production Saved Analyses backend

Production contains `public.rivexis_edge_saved_analysis(text,text,jsonb)` and Edge v7 Saved Analyses endpoints.

Verified security posture remains:

- function owner `rivexis_migrator`;
- SECURITY DEFINER with pinned search path;
- execute restricted to service-role runtime path rather than anon/authenticated/PUBLIC;
- actor and workspace authorization rechecked server-side;
- migrator remains NOLOGIN and temporary installation SET capability was removed.

Post-deploy verification previously established direct Edge health HTTP 200/ready, unauthenticated Saved Analyses HTTP 401, authoritative Worker health HTTP 200, and version-7 Edge logs without a surfaced runtime exception in those checks.

## Frontend deployment automation blocker

Manual Cloudflare deployment through the authenticated local Wrangler OAuth session is working and exact-source production parity is verified. Automatic GitHub deployment still stops before contacting Cloudflare because repository secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` are not configured.

Until those narrowly scoped deployment credentials are configured:

- preserve manual exact-SHA verification for every production promotion;
- do not expose OAuth state or account credentials in source, logs or chat;
- do not make billing changes without explicit authorization;
- do not claim the GitHub deployment workflow is operational.

## Existing production integrity

- browser authentication uses HttpOnly/Secure/SameSite=Lax cookies + CSRF;
- recovery bearer tokens are not persisted in browser storage;
- workspace/organization access remains tenant-aware and fail-closed;
- demonstration engines remain explicitly synthetic;
- live compatibility execution remains UNKNOWN without verified provider evidence;
- protocol artifacts do not certify safety;
- provider absence/licensing gates remain explicit.

## Next production target

Certify one controlled queued-alert provider acceptance and inbox receipt through the now-ready Brevo sink without overstating delivery semantics. Preserve `UNKNOWN` for unconfigured continuous threat providers.
