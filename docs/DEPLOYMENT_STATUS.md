# Rivexis Deployment Status

Last updated: 2026-09-28

| Environment | Status | Evidence / meaning |
|---|---|---|
| GitHub `main` | RELEASE CURRENT | Institutional product experience `73d662839651481b3f6f06e06ff509fe37a21e13` passed CI run `36397358106` and Pages run `36397356730` on the exact SHA; the browser matrix passed 52/52. |
| GitHub Pages | FALLBACK ONLY | Pages follows the same source lineage; it is not the authoritative application runtime. |
| Cloudflare web | LIVE / CURRENT | `rivexis-web.rudrasingh0718.workers.dev`; Worker version `e8922aac-cb84-435b-bd0c-38fbb886be57`. |
| Supabase Edge API | LIVE / COMPATIBILITY RUNTIME | `rivexis-api` version 6; health ready; auth, workspace, persistence, all ten deterministic demonstration engine paths, manual monitors, protocol workflow and reports operational. The provider registry explicitly declares deep probes unavailable and missing live providers remain UNKNOWN. |
| Authoritative FastAPI | SOURCE READY / BILLING GATED | Existing Docker + Cloudflare Container `lite` design requires Workers Paid; scrypt will not be weakened for Free. |
| Supabase PostgreSQL | ACTIVE_HEALTHY / CURRENT | Project `ivszvufdonfgwjpfgwii`, PostgreSQL 17.6.1, production Alembic head `0013_auth_email_lifecycle`; 0012 and 0013 postflight verified. |
| Brevo | LIVE / AUTH TRANSPORT | Supabase Auth custom SMTP is enabled through the Brevo free relay. A production recovery request was accepted by Supabase and Brevo recorded both `Sent` and `Delivered`; the credential remains encrypted in Supabase and absent from source. |
| Production | FUNCTIONAL FREE RUNTIME | Public site, auth, recovery delivery, workspaces, organizations, tenant persistence, all ten honest demonstration engines, history, monitors, protocol reviews/investigations and PDF reports are working. Full provider-backed FastAPI parity remains plan/credential gated. |

## Live frontend verification

Live browser E2E on 2026-09-28 verified signup mail, login, onboarding, authenticated refresh/session persistence, workspace switching, organization creation, logout, protected-route denial, password-reset request and Gmail receipt. All B1-B5/F1-F5 engine routes passed the 52-test browser matrix, including guided-control payload normalization. Edge unit coverage passed 13/13 across all ten deterministic demonstrations plus malformed-input and live fail-closed cases. Production browser verification on Worker `e8922aac-cb84-435b-bd0c-38fbb886be57` confirmed the redesigned public/login/workspace surfaces, session restoration, same-origin health `200`, and a guided F5 `40/12` demonstration completing with a normalized 40/100 synthetic result. The public and authenticated console checks returned no warnings or errors. Earlier production verification of B1's synthetic 45/100 output, B4's `CONFLICTING_DATA`, B1 live fail-closed `UNKNOWN`, manual B3 monitor checks, protocol workflow, investigation lifecycle and PDF response remains valid.

The provider-health surface now consumes the runtime's explicit `deep_probe_available=false` capability. It offers a verified refresh action and no longer presents a deep-probe action that the free compatibility runtime cannot execute. The production browser reload and refresh both completed while retaining the authenticated workspace.

## Production database postflight

Production reports migration `0013_auth_email_lifecycle`, 56 application tables, complete FK covering-index posture, no intended redundant indexes, the certified RLS lookup rewrite, and the `user_auth_state` FORCE-RLS/service-policy contract. No inspected application table changed ownership away from `rivexis_migrator`, and both migration/runtime roles remain `NOLOGIN`.

## Activation gates

- **FastAPI runtime:** explicit authorization for the minimum Workers Paid plan change.
- **Owned email identity:** an authenticated Rivexis-owned sending domain is still absent.
- **Provider contracts:** missing credentials/licensing remain explicit UNKNOWN/unavailable states.
