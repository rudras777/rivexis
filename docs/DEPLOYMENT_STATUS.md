# Rivexis Deployment Status

Last updated: 2026-09-25

| Environment | Status | Evidence / meaning |
|---|---|---|
| GitHub `main` | GREEN | Application head `37fd1e4097cc5c621d9a847e40ce8a24b3ead9e1`; CI #380 (`36056453140`) passed all lanes. |
| GitHub Pages | FALLBACK ONLY | Pages #51 follows the same source lineage; it is not the authoritative application runtime. |
| Cloudflare web | LIVE / CURRENT | `rivexis-web.rudrasingh0718.workers.dev`; Worker version `b6f5f845-a9fa-4f03-8622-ece8364db633` at 100% traffic. |
| Cloudflare API Free | LIVE / DEGRADED BY DESIGN | `/health` reports degraded; application endpoints return 503. It is not the FastAPI runtime. |
| Authoritative FastAPI | SOURCE READY / BILLING GATED | Existing Docker + Cloudflare Container `lite` design requires Workers Paid; scrypt will not be weakened for Free. |
| Supabase PostgreSQL | ACTIVE_HEALTHY / CURRENT | Project `ivszvufdonfgwjpfgwii`, PostgreSQL 17.6.1, production Alembic head `0013_auth_email_lifecycle`; 0012 and 0013 postflight verified. |
| Brevo | RELAY/SENDER READY / TEMPLATES INACTIVE | Relay enabled; active Gmail sender; templates #1/#2 exist but remain inactive; owned-domain identity and inbox delivery are uncertified. |
| Production | PARTIAL | Frontend and schema are current; authoritative API, real auth, transactional delivery, and workspace runtime remain blocked by the paid backend gate and email activation/identity gates. |

## Live frontend verification

The deployment exposes the new verification and recovery routes and retains the existing degraded-service disclosure. Live HTTP probes on 2026-09-25 returned 200 for `/`, `/login`, `/signup`, `/forgot-password`, `/reset-password`, `/verify-email`, and `/workspace`; an unknown route returned 404. Responses retained HSTS, CSP, `X-Content-Type-Options`, and HTTPS. Browser inspection confirmed the login recovery link and recovery form with no observed page console errors.

## Production database postflight

Production reports migration `0013_auth_email_lifecycle`, 56 application tables, complete FK covering-index posture, no intended redundant indexes, the certified RLS lookup rewrite, and the `user_auth_state` FORCE-RLS/service-policy contract. No inspected application table changed ownership away from `rivexis_migrator`, and both migration/runtime roles remain `NOLOGIN`.

## Activation gates

- **FastAPI runtime:** explicit authorization for the minimum Workers Paid plan change.
- **Runtime configuration:** restricted `DATABASE_URL`, strong auth secret, exact origins, DEMO off, PostgreSQL distributed controls on, Brevo bindings, and trusted public web URL.
- **Brevo:** activate existing templates; an owned-domain sender is still absent; controlled API-to-provider-to-inbox delivery remains unverified.
- **Auth E2E:** frontend and backend source exist, but the authoritative API is not deployed, so real signup/login/session/reset cannot yet be certified.
- **Provider contracts:** missing credentials/licensing remain explicit UNKNOWN/unavailable states.
