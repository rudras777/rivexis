# Rivexis Current Build State

Last updated: 2026-09-28

This is the compact production resume point. Live provider state and current `main` override older historical notes.

## Repository and certification

- Repository: `rudras777/rivexis`; branch `main`.
- Production-repair work started from clean `main` head `21fe63f3b1b19aa607cd56779e9fc88290673dbc`; origin matched before changes. CI #408 and Pages #79 passed on that baseline.
- Production repair implementation `c7b52aac8b227246e29efd8ff942e73aa64d15c2` adds the free runtime bridge and verified frontend integration. CI #409 and Pages #80 passed on that exact SHA.
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

On 2026-09-28, a least-privilege `SECURITY DEFINER` function, `public.rivexis_edge_bridge(text,text,jsonb)`, was deployed for the Supabase Edge compatibility runtime. Execute remains restricted to `service_role`; the function owner is `rivexis_migrator`; direct application table grants were not restored. The bridge enforces explicit actor/workspace membership checks for analysis detail, monitor, report, review, and investigation paths. A narrowly scoped RLS bootstrap policy permits organization creation only when the function's verified user/organization/OWNER context matches.

Supabase security advisor reports one Auth-platform warning: leaked-password protection is disabled. The free production compatibility runtime uses Supabase Auth, so this warning applies to that path and remains an explicit hardening item unless the current plan supports enabling it without a billing change. Performance advisor reports newly created/other indexes as unused; the database has not yet received enough authoritative API workload for those observations to justify removing the certified FK indexes.

## Production frontend

Authoritative public frontend:

`https://rivexis-web.rudrasingh0718.workers.dev/`

Cloudflare Worker version `9165c9b6-e8e7-4b78-b82d-4ef73becc6f9` is the current manual production deployment. Live browser verification covered public auth pages, same-origin `/health`, authenticated workspace navigation, refresh/session persistence, logout/protected-route denial, workspace and organization creation, providers, monitors, history, saved analyses, protocol history, investigation workflow, and PDF rendering.

The web application now uses a same-origin `/api/v1/*` proxy to the Supabase Edge function `rivexis-api` (function version 4). Browser cookies remain HttpOnly/Secure/SameSite=Lax and state-changing requests retain CSRF validation. Recovery bearer tokens are kept in memory only and removed from the browser URL before password entry.

## Authentication lifecycle

Backend source implements signup/login/cookie session/CSRF/logout/revocation plus email verification and password-reset request/confirm flows. Production schema support is applied at 0013.

Head `3e6285f...` completes the corresponding frontend lifecycle:

- verification-required signup no longer assumes an authenticated session;
- `/verify-email` supports one-time code confirmation and enumeration-safe resend;
- `/forgot-password` returns enumeration-safe acknowledgement;
- `/reset-password` supports trusted-link token prefill, password confirmation, safe invalid/expired-token messaging, and documents session revocation;
- public auth lifecycle endpoints no longer perform an unnecessary authenticated CSRF bootstrap;
- focused browser tests pass 7/7 and the full CI web lane passes.

Production authentication is now available through the free Supabase Edge compatibility runtime. Real signup verification mail, login, automatic application-user provisioning, workspace onboarding, session refresh/persistence, logout, protected-route denial, password-recovery request and Gmail delivery were verified. Supabase Auth Site URL and redirect allowlist now point to the production Worker origin.

## Cloudflare backend gate

The repository's full provider-capable runtime remains the existing FastAPI Docker image behind the Cloudflare Container `lite` wrapper. Workers Free remains incompatible with that runtime's deliberate CPU/security controls. The Supabase Edge compatibility runtime now supplies production auth, tenant/workspace control, persistence, honest UNKNOWN engine demonstrations, manual monitors, protocol-history/investigation artifacts, and reports without claiming FastAPI provider parity.

## Brevo

Live inspection found:

- SMTP relay enabled;
- free account with 300 daily send credits at inspection time;
- one active `Rivexis` sender using the owner's Gmail address;
- verification template #1 and password-reset template #2 are active, use sender name `Rivexis`, and match the runtime parameter contract;
- no Rivexis-owned authenticated sending domain exists, so Brevo warns it will substitute a `brevosend.com` sender domain;
- controlled template tests were accepted by Brevo and both messages reached the owner Gmail inbox; Brevo logs independently showed the verification message as `Sent` and `Delivered`;
- template-test sends do not inject runtime parameters; production recovery delivery is now independently certified through the Supabase Auth custom-SMTP path, while verification-template substitution remains covered by the existing Supabase Auth template rather than Brevo template #1.

Supabase Auth custom SMTP is now enabled through the Brevo free relay. The production credential is encrypted by Supabase, was never committed, and remains hidden after save. A real Rivexis password-recovery request completed with HTTP 200; Supabase Auth logged `user_recovery_requested`, and Brevo independently recorded the resulting message as both `Sent` and `Delivered`. Until an owned sender domain is authenticated, Brevo substitutes the configured Gmail sender with its `brevosend.com` domain.

## Engine integrity

All B1-B5/F1-F5 integrity controls remain intact. B1 remains engine contract `1.3.0`, calculation `b1-live-1.8.0`, with bounded, non-verdicting structural security observations. B2 remains engine contract `1.1.0`, calculation `b2-live-1.3.0`, with bounded bytecode/proxy observations and first-class implementation conflicts. B3 remains engine contract `1.1.0`, calculation `b3-live-1.3.0`, with canonical RPC/ABI values, monotonic dependency-identified prior snapshots and provider-specific freshness. B4 remains engine contract `1.0.0`, calculation `b4-live-1.1.0`, with strict quantities/history limits, explicit malformed rows, zero-flow self-transfer accounting and isolated external freshness. B5 remains engine contract `1.2.0`, calculation `b5-live-1.4.0`, with bounded route/economic/step integrity and honest UNKNOWN quote freshness. F1 remains engine contract `1.2.0`, calculation `f1-live-1.4.0`, with same-block direct `decimals()`/`balanceOf`, canonical ABI uint256 validation, bounded quantities, token metadata conflict handling, direct metadata evidence, provider redaction, and fail-closed incomplete holdings semantics. F2 remains engine contract `1.2.0`, calculation `f2-live-1.4.0`, with shared collector `protocol-native-1.2.0`: every direct read is pinned to the captured canonical uint256 block; runtime code, EIP-1967 words and oracle ABI returns are bounded/canonical; malformed direct or explorer identity evidence fails closed; future oracle time stays UNKNOWN; external explorer metadata cannot inherit the RPC block or LIVE freshness; and aggregate freshness reflects every retained evidence source. F4 remains engine contract `1.2.0`, calculation `f4-live-1.3.0`: selectors, provider payloads and selected identity are bounded; strategy matching cannot succeed through arbitrary substrings; present-but-invalid optional metrics fail closed; provider timestamps are normalized without retrieval-time optimism; native confidence requires native evidence; and aggregate freshness conservatively reflects all retained yield, native and explorer evidence. F5 remains engine contract `1.2.0` and advances to calculation `f5-live-1.3.0`: allocation/identity/native-check inputs are bounded; duplicate asset rows aggregate before concentration and HHI scoring; contradictory classifications and non-finite valuations fail closed; malformed market rows cannot claim current confidence; unknown observation time remains null; and aggregate freshness/confidence incorporates protocol-native evidence only when evidence exists.

## Current execution gates

1. Full provider-capable FastAPI deployment still requires explicit Workers Paid authorization.
2. The Gmail sender is not an owned authenticated domain.
3. Provider credentials/licenses remain explicit; unavailable evidence stays UNKNOWN.

## Next execution order

1. Continue deterministic engine hardening and add real providers only with approved credentials/licenses; preserve UNKNOWN otherwise.
2. Authenticate a Rivexis-owned sender domain when one becomes available; do not purchase one implicitly.
3. If paid deployment is later authorized, deploy the existing FastAPI Container with restricted runtime credentials and production bindings, then certify parity against the compatibility runtime.
