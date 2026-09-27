# Rivexis Deployment Status

Last updated: 2026-09-28

| Environment | Status | Evidence / meaning |
|---|---|---|
| GitHub `main` | RELEASE CURRENT | Production repair implementation `c7b52aac8b227246e29efd8ff942e73aa64d15c2` passed CI #409 and Pages #80 on the exact SHA. |
| GitHub Pages | FALLBACK ONLY | Pages follows the same source lineage; it is not the authoritative application runtime. |
| Cloudflare web | LIVE / CURRENT | `rivexis-web.rudrasingh0718.workers.dev`; Worker version `9165c9b6-e8e7-4b78-b82d-4ef73becc6f9`. |
| Supabase Edge API | LIVE / COMPATIBILITY RUNTIME | `rivexis-api` version 4; health ready; auth, workspace, persistence, all ten demonstration engine paths, manual monitors, protocol workflow and reports operational. Missing live providers remain UNKNOWN. |
| Authoritative FastAPI | SOURCE READY / BILLING GATED | Existing Docker + Cloudflare Container `lite` design requires Workers Paid; scrypt will not be weakened for Free. |
| Supabase PostgreSQL | ACTIVE_HEALTHY / CURRENT | Project `ivszvufdonfgwjpfgwii`, PostgreSQL 17.6.1, production Alembic head `0013_auth_email_lifecycle`; 0012 and 0013 postflight verified. |
| Brevo | LIVE / AUTH TRANSPORT | Supabase Auth custom SMTP is enabled through the Brevo free relay. A production recovery request was accepted by Supabase and Brevo recorded both `Sent` and `Delivered`; the credential remains encrypted in Supabase and absent from source. |
| Production | FUNCTIONAL FREE RUNTIME | Public site, auth, recovery delivery, workspaces, organizations, tenant persistence, all ten honest demonstration engines, history, monitors, protocol reviews/investigations and PDF reports are working. Full provider-backed FastAPI parity remains plan/credential gated. |

## Live frontend verification

Live browser E2E on 2026-09-28 verified signup mail, login, onboarding, authenticated refresh/session persistence, workspace switching, organization creation, logout, protected-route denial, password-reset request and Gmail receipt. All B1-B5/F1-F5 demonstration runs persisted with explicit UNKNOWN/no-evidence output; F1 retained framework `f1-live-1.4.0` and engine contract `1.2.0`. Manual B3 monitor checks, protocol history/configuration review approval, investigation lifecycle and PDF response were also verified.

## Production database postflight

Production reports migration `0013_auth_email_lifecycle`, 56 application tables, complete FK covering-index posture, no intended redundant indexes, the certified RLS lookup rewrite, and the `user_auth_state` FORCE-RLS/service-policy contract. No inspected application table changed ownership away from `rivexis_migrator`, and both migration/runtime roles remain `NOLOGIN`.

## Activation gates

- **FastAPI runtime:** explicit authorization for the minimum Workers Paid plan change.
- **Owned email identity:** an authenticated Rivexis-owned sending domain is still absent.
- **Provider contracts:** missing credentials/licensing remain explicit UNKNOWN/unavailable states.
