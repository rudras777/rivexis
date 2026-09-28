# Rivexis Deployment Status

Last updated: 2026-09-28

| Environment | Status | Evidence / meaning |
|---|---|---|
| GitHub `main` | RELEASE CURRENT | Deterministic demonstration runtime `6f2ee469d4c8eb6b4e2945bfc525517adaeb4eea` passed CI run `36394468961` and Pages run `36394469225` on the exact SHA. |
| GitHub Pages | FALLBACK ONLY | Pages follows the same source lineage; it is not the authoritative application runtime. |
| Cloudflare web | LIVE / CURRENT | `rivexis-web.rudrasingh0718.workers.dev`; Worker version `b2e9f7f5-8b55-4523-b8f7-d5504c0ab13a`. |
| Supabase Edge API | LIVE / COMPATIBILITY RUNTIME | `rivexis-api` version 6; health ready; auth, workspace, persistence, all ten deterministic demonstration engine paths, manual monitors, protocol workflow and reports operational. The provider registry explicitly declares deep probes unavailable and missing live providers remain UNKNOWN. |
| Authoritative FastAPI | SOURCE READY / BILLING GATED | Existing Docker + Cloudflare Container `lite` design requires Workers Paid; scrypt will not be weakened for Free. |
| Supabase PostgreSQL | ACTIVE_HEALTHY / CURRENT | Project `ivszvufdonfgwjpfgwii`, PostgreSQL 17.6.1, production Alembic head `0013_auth_email_lifecycle`; 0012 and 0013 postflight verified. |
| Brevo | LIVE / AUTH TRANSPORT | Supabase Auth custom SMTP is enabled through the Brevo free relay. A production recovery request was accepted by Supabase and Brevo recorded both `Sent` and `Delivered`; the credential remains encrypted in Supabase and absent from source. |
| Production | FUNCTIONAL FREE RUNTIME | Public site, auth, recovery delivery, workspaces, organizations, tenant persistence, all ten honest demonstration engines, history, monitors, protocol reviews/investigations and PDF reports are working. Full provider-backed FastAPI parity remains plan/credential gated. |

## Live frontend verification

Live browser E2E on 2026-09-28 verified signup mail, login, onboarding, authenticated refresh/session persistence, workspace switching, organization creation, logout, protected-route denial, password-reset request and Gmail receipt. All B1-B5/F1-F5 engine routes passed the 51-test browser matrix. Edge unit coverage passed 13/13 across all ten deterministic demonstrations plus malformed-input and live fail-closed cases. Production browser verification confirmed B1's synthetic 45/100 evidence-backed demonstration, B4's `CONFLICTING_DATA` result with one unresolved conflict, and B1 live mode returning `UNKNOWN`, zero evidence and `NO_VERIFIED_PROVIDER_EVIDENCE`. F1 retained framework `f1-live-1.4.0` and engine contract `1.2.0`. Manual B3 monitor checks, protocol history/configuration review approval, investigation lifecycle and PDF response were also verified.

The provider-health surface now consumes the runtime's explicit `deep_probe_available=false` capability. It offers a verified refresh action and no longer presents a deep-probe action that the free compatibility runtime cannot execute. The production browser reload and refresh both completed while retaining the authenticated workspace.

## Production database postflight

Production reports migration `0013_auth_email_lifecycle`, 56 application tables, complete FK covering-index posture, no intended redundant indexes, the certified RLS lookup rewrite, and the `user_auth_state` FORCE-RLS/service-policy contract. No inspected application table changed ownership away from `rivexis_migrator`, and both migration/runtime roles remain `NOLOGIN`.

## Activation gates

- **FastAPI runtime:** explicit authorization for the minimum Workers Paid plan change.
- **Owned email identity:** an authenticated Rivexis-owned sending domain is still absent.
- **Provider contracts:** missing credentials/licensing remain explicit UNKNOWN/unavailable states.
