# Rivexis Current Build State

Last updated: 2026-09-25

This is the compact production resume point. Live provider state and current `main` override older historical notes.

## Repository and certification

- Repository: `rudras777/rivexis`; branch `main`.
- Latest certified application head: `b2198bc508096e458560e077b41cb60f11fdcd5d` (`Harden F2 protocol-native evidence integrity`).
- CI #403 (`36168119939`) passed the complete matrix on that exact head: API ruff/pytest/pip-audit; web edge/web typechecks, Next build, vinext build, npm audit and Playwright; invariants/secret/migration checks; PostgreSQL migration/runtime-control/migrated-schema verification. Pages #74 (`36168118741`) also passed on the exact head.
- Pages is a fallback/navigation deployment for the same source lineage; it is not the authoritative runtime.

## Production PostgreSQL

Supabase project `ivszvufdonfgwjpfgwii` is `ACTIVE_HEALTHY` in `ap-south-1` on PostgreSQL 17.6.1.

Live postflight on 2026-09-25 established production is at Alembic head `0013_auth_email_lifecycle`. The previously documented migration gate is resolved. Verified live state:

- 56 application tables;
- zero foreign keys lacking a valid leading-column covering index;
- `ix_users_email` and `ix_workspaces_owner_user_id` absent as intended;
- zero target tenant policies retaining uncached per-row session-setting lookup form;
- `user_auth_state` has RLS and FORCE RLS enabled;
- its intended `rivexis_app` service policy exists;
- no `anon`, `authenticated`, `PUBLIC`, or `service_role` grant exists on `user_auth_state`;
- every public application table remains owned by `rivexis_migrator`;
- `rivexis_migrator` and `rivexis_app` both remain `NOLOGIN` in the inspected management context.

Supabase security advisor reports one Auth-platform warning: leaked-password protection is disabled. Rivexis authentication is implemented by the FastAPI service rather than Supabase Auth, so this warning does not describe the current application password path. Performance advisor reports newly created/other indexes as unused; the database has not yet received authoritative API workload, so those observations are not evidence that the certified FK indexes should be removed.

## Production frontend

Authoritative public frontend:

`https://rivexis-web.rudrasingh0718.workers.dev/`

Cloudflare Worker version `0d86a100-a115-4bca-a8ef-69d73be7a72d` receives 100% traffic. It was deployed only after CI #383 passed. Live probes verified `/`, `/login?verified=1`, `/forgot-password`, `/reset-password`, `/verify-email`, and `/workspace` return 200, an unknown route returns 404, HTTPS/HSTS/CSP/nosniff headers remain present, and browser inspection found the deployed verification notice and recovery UI without page console errors. Cloudflare observability has query-string redaction enabled so recovery tokens are not retained in request URLs; the durable Wrangler configuration carries the same setting.

The web application is configured to call `https://rivexis-api.rudrasingh0718.workers.dev`.

## Authentication lifecycle

Backend source implements signup/login/cookie session/CSRF/logout/revocation plus email verification and password-reset request/confirm flows. Production schema support is applied at 0013.

Head `3e6285f...` completes the corresponding frontend lifecycle:

- verification-required signup no longer assumes an authenticated session;
- `/verify-email` supports one-time code confirmation and enumeration-safe resend;
- `/forgot-password` returns enumeration-safe acknowledgement;
- `/reset-password` supports trusted-link token prefill, password confirmation, safe invalid/expired-token messaging, and documents session revocation;
- public auth lifecycle endpoints no longer perform an unnecessary authenticated CSRF bootstrap;
- focused browser tests pass 7/7 and the full CI web lane passes.

Production auth remains unavailable because the authoritative FastAPI runtime is not deployed. The free `rivexis-api` Worker remains an explicit degraded boundary and returns 503 for application endpoints instead of faking authentication.

## Cloudflare backend gate

The repository's approved runtime remains the existing FastAPI Docker image behind the Cloudflare Container `lite` wrapper. Workers Free is incompatible with the deliberate scrypt CPU budget; Rivexis will not weaken password hashing or distributed controls. Deploying the authoritative API still requires explicit authorization for the minimum Workers Paid plan change.

## Brevo

Live inspection found:

- SMTP relay enabled;
- free account with 300 daily send credits at inspection time;
- one active `Rivexis` sender using the owner's Gmail address;
- verification template #1 and password-reset template #2 are active, use sender name `Rivexis`, and match the runtime parameter contract;
- no Rivexis-owned authenticated sending domain exists, so Brevo warns it will substitute a `brevosend.com` sender domain;
- controlled template tests were accepted by Brevo and both messages reached the owner Gmail inbox; Brevo logs independently showed the verification message as `Sent` and `Delivered`;
- template-test sends do not inject runtime parameters, so production link/code substitution and the full application-triggered lifecycle remain uncertified until the backend is deployed.

## Engine integrity

All B1-B5/F1-F5 integrity controls remain intact. B1 remains engine contract `1.3.0`, calculation `b1-live-1.8.0`, with bounded, non-verdicting structural security observations. B2 remains engine contract `1.1.0`, calculation `b2-live-1.3.0`, with bounded bytecode/proxy observations and first-class implementation conflicts. B3 remains engine contract `1.1.0`, calculation `b3-live-1.3.0`, with canonical RPC/ABI values, monotonic dependency-identified prior snapshots and provider-specific freshness. B4 remains engine contract `1.0.0`, calculation `b4-live-1.1.0`, with strict quantities/history limits, explicit malformed rows, zero-flow self-transfer accounting and isolated external freshness. B5 remains engine contract `1.2.0`, calculation `b5-live-1.4.0`, with bounded route/economic/step integrity and honest UNKNOWN quote freshness. F1 remains engine contract `1.2.0`, calculation `f1-live-1.4.0`, with same-block direct `decimals()`/`balanceOf`, canonical ABI uint256 validation, bounded quantities, token metadata conflict handling, direct metadata evidence, provider redaction, and fail-closed incomplete holdings semantics. F2 remains engine contract `1.2.0` and advances to calculation `f2-live-1.4.0` with shared collector `protocol-native-1.2.0`: every direct read is pinned to the captured canonical uint256 block; runtime code, EIP-1967 words and oracle ABI returns are bounded/canonical; malformed direct or explorer identity evidence fails closed; future oracle time stays UNKNOWN; external explorer metadata cannot inherit the RPC block or LIVE freshness; and aggregate freshness reflects every retained evidence source.

## Current execution gates

1. Authoritative FastAPI deployment requires explicit Workers Paid authorization.
2. Runtime production secrets must be configured without exposing migration credentials.
3. The Gmail sender is not an owned authenticated domain.
4. Real signup/login/session/logout/recovery/email E2E cannot be certified until the backend is deployed.
5. Provider credentials/licenses remain explicit; unavailable evidence stays UNKNOWN.

## Next execution order

1. Continue free authentication UX and deterministic engine hardening while the runtime is billing-gated.
2. If a zero-cost authoritative runtime becomes technically compatible without weakening controls, certify it before any architecture change.
3. If paid deployment is later authorized, deploy the existing FastAPI Container with restricted runtime credentials and production bindings.
4. Run real auth, session, reset, inbox-delivery, workspace, and safe engine E2E after an authoritative backend exists.
