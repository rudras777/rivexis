# Rivexis Deployment Status

Last updated: 2026-09-28

| Environment | Status | Evidence / meaning |
|---|---|---|
| GitHub `main` | RELEASE CURRENT | Saved-analysis production slice is certified through source `59dadde0edb1c58ea2b22f421c26d4509bbab7f2`; CI run `36421346582` and Pages run `36421345772` both passed on that exact SHA. Later documentation commits only record this verified state unless otherwise noted. |
| GitHub Pages | FALLBACK ONLY | Pages follows the source lineage but is not the authoritative application runtime. |
| Cloudflare web | LIVE / SOURCE DRIFT | `rivexis-web.rudrasingh0718.workers.dev` remains on previously certified manual Worker version `e8922aac-cb84-435b-bd0c-38fbb886be57`. The current institutional UI and later operational source are not claimed as live on this Worker. |
| Supabase Edge API | LIVE / V7 | `rivexis-api` version 7 is ACTIVE. It retains custom HttpOnly-cookie + CSRF auth and now includes production Saved Analyses list/save/archive/restore/delete compatibility endpoints. |
| Supabase PostgreSQL | LIVE / HARDENED | Project `ivszvufdonfgwjpfgwii`, PostgreSQL 17.6.1. Core Alembic schema remains through `0013_auth_email_lifecycle`; the Saved Analyses service-role bridge is additionally deployed under `rivexis_migrator`. |
| Authoritative FastAPI | SOURCE READY / BILLING GATED | Existing full provider-capable Docker/Container design remains gated on explicit Workers Paid authorization. Security controls will not be weakened for a free-plan deployment. |
| Brevo / Supabase SMTP | LIVE / AUTH TRANSPORT | Production password recovery previously passed Supabase Auth and Brevo independently recorded Sent + Delivered. An owned authenticated Rivexis sending domain is still absent. |
| Production capability | FUNCTIONAL COMPATIBILITY RUNTIME | Auth, tenancy, persistence, ten deterministic demonstration engines, UNKNOWN-safe live mode, monitors, protocol review/investigation artifacts and the Saved Analyses backend contract are production-backed. Full provider-backed FastAPI parity remains credential/plan gated. |

## Saved Analyses production release

Source behavior now includes search, active/all archived visibility, persisted evidence inspection, archive/restore and saved-reference deletion. The underlying analysis remains in workspace history when a saved reference is deleted.

Production database support is provided by `public.rivexis_edge_saved_analysis(text,text,jsonb)`. Post-deployment inspection verified:

- owner `rivexis_migrator`;
- SECURITY DEFINER with fixed `search_path=pg_catalog, public`;
- execute ACL limited to `rivexis_migrator` and `service_role`;
- no anonymous/authenticated/public execution grant;
- `rivexis_migrator` remains NOLOGIN;
- PostgreSQL's temporary ability to SET `rivexis_migrator` was removed after installation.

Supabase Edge `rivexis-api` version 7 exposes authenticated + CSRF-protected Saved Analyses routes matching the FastAPI contract for list/save/archive/restore/delete.

Post-deploy public verification established:

- direct Edge `/health` → HTTP 200, `ready`, runtime `supabase-edge`, API `v1`, environment `production`;
- unauthenticated Saved Analyses request → HTTP 401 `Authentication required`;
- authoritative Worker `/health` → HTTP 200 with the same production Edge runtime;
- Edge logs identify version 7 for the post-deploy health and protected-route requests and did not surface a runtime exception in those checks.

A real authenticated production archive/restore/delete mutation has not yet been claimed during this continuation. The action UI is browser-test certified and the production database/API contract is live; authenticated mutation certification remains a follow-up.

## Authoritative frontend drift

The web Worker remains the main release blocker. GitHub source contains later institutional UI/UX and operational functionality than the current Worker bundle.

Cloudflare deployment could not be completed from this environment because Wrangler lacks authenticated credentials and the Cloudflare dashboard remained behind human verification after the permitted safe attempt. No temporary account, alternate host, verification bypass or billing change was used.

Until legitimate Cloudflare authentication is available:

- do not claim newer frontend source is live on `rivexis-web`;
- continue implementing/test-certifying unblocked source and backend slices;
- keep production API/backend improvements truthful and separately evidenced;
- deploy the exact newest certified source once authorized access becomes available, then perform full live browser certification.

## Existing production integrity retained

- Browser authentication uses HttpOnly/Secure/SameSite=Lax cookies plus CSRF.
- Password recovery does not persist bearer tokens in browser storage.
- Workspace/organization access remains tenant-aware and fail-closed.
- All ten demonstration engines are explicitly synthetic and deterministic.
- Live requests remain `UNKNOWN` when verified provider evidence is unavailable.
- Protocol review/investigation artifacts do not certify protocol safety.
- Provider absence, licensing gates and unavailable deep probes remain visible rather than simulated.

## Activation gates

- **Latest frontend deployment:** requires authenticated Cloudflare dashboard or Wrangler access.
- **Full FastAPI runtime:** requires explicit Workers Paid authorization.
- **Provider-backed evidence:** requires approved credentials/contracts/licenses.
- **Owned email identity:** requires a Rivexis-owned authenticated sending domain; do not purchase/configure one implicitly.

## Next production target

Complete History and general report actions end-to-end against real persistence/rendering contracts, then certify those source/backend changes before attempting the next Cloudflare web promotion. Structured F1/F3/F5 builders follow where they improve real workflow usability without weakening validation or evidence semantics.
