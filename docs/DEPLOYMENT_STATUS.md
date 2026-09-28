# Rivexis Deployment Status

Last updated: 2026-09-28

| Environment | Status | Evidence / meaning |
|---|---|---|
| GitHub product source | CERTIFIED | Product source `6bf117154a958688697cc998530a65c9726e820f` passed CI `36429614693` and Pages `36429614899`. Later documentation-only commits record that certified state. |
| GitHub Pages | FALLBACK ONLY | Latest certified product source built successfully, but Pages is not the authoritative application runtime. |
| Cloudflare web | LIVE / SOURCE DRIFT | `rivexis-web.rudrasingh0718.workers.dev` remains on manual Worker version `e8922aac-cb84-435b-bd0c-38fbb886be57`; newer UI/workflow source is not claimed live there. |
| Supabase Edge API | LIVE / V7 | `rivexis-api` version 7 ACTIVE with HttpOnly-cookie + CSRF auth and production Saved Analyses compatibility endpoints. |
| Supabase PostgreSQL | LIVE / HARDENED | Project `ivszvufdonfgwjpfgwii`, PostgreSQL 17.6.1; core schema through `0013_auth_email_lifecycle`; hardened runtime bridges retained. |
| Full FastAPI runtime | SOURCE READY / BILLING GATED | Deep provider-capable container deployment remains gated on explicit Workers Paid authorization. |
| Brevo / Supabase SMTP | LIVE / AUTH TRANSPORT | Recovery delivery previously verified Sent + Delivered; owned authenticated Rivexis sender domain remains absent. |

## Latest certified source capabilities

The certified GitHub source now includes:

- operational History search/type/mode filters, provenance inspection and real Saved-reference creation;
- Saved Analyses search/inspect/archive/restore/delete;
- structured F1 portfolio-position builder preserving canonical `manual_positions`;
- guided F3 liquidation/oracle evidence inputs aligned to the real FastAPI contract;
- structured F5 treasury allocation ledger preserving exact weights and canonical `allocations`;
- existing institutional UI/UX, provider/monitor, protocol-review/investigation and ten-engine source functionality.

These are **source/CI/Pages certified**, not authoritative Cloudflare-live UI claims.

## Production Saved Analyses backend

Production contains `public.rivexis_edge_saved_analysis(text,text,jsonb)` and Edge v7 Saved Analyses endpoints.

Verified security posture remains:

- function owner `rivexis_migrator`;
- SECURITY DEFINER with pinned search path;
- execute restricted to service-role runtime path rather than anon/authenticated/PUBLIC;
- actor and workspace authorization rechecked server-side;
- migrator remains NOLOGIN and temporary installation SET capability was removed.

Post-deploy verification previously established direct Edge health HTTP 200/ready, unauthenticated Saved Analyses HTTP 401, authoritative Worker health HTTP 200, and version-7 Edge logs without a surfaced runtime exception in those checks.

## Frontend release blocker

Cloudflare web promotion is still blocked because Wrangler is unauthenticated and the dashboard remained behind human verification after the permitted safe attempt.

Until legitimate Cloudflare authentication is available:

- do not claim current GitHub UI is live on the Worker;
- do not bypass human verification;
- do not create a temporary Cloudflare account or deploy to another host;
- do not make billing changes without explicit authorization;
- continue source/backend work with exact certification and separate production truth.

## Existing production integrity

- browser authentication uses HttpOnly/Secure/SameSite=Lax cookies + CSRF;
- recovery bearer tokens are not persisted in browser storage;
- workspace/organization access remains tenant-aware and fail-closed;
- demonstration engines remain explicitly synthetic;
- live compatibility execution remains UNKNOWN without verified provider evidence;
- protocol artifacts do not certify safety;
- provider absence/licensing gates remain explicit.

## Next production target

Implement organization/member administration parity in the Supabase compatibility runtime before exposing Settings member controls. Full FastAPI already supports member list/add/claim/remove; the free Edge path must gain equivalent authorization and persistence semantics first. Any database bridge must retain the hardened minimum-execute posture recommended for privileged Supabase functions. General report actions remain deferred until real Edge persistence/rendering parity exists.
