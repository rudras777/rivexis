# Rivexis Current Build State

Last updated: 2026-09-24

This file is the compact resume point for the dedicated normal-ChatGPT production-build program. It supplements the historical execution plan and overrides stale point-in-time blocker wording where this file records newer verified evidence.

## Repository and CI

- Repository: private `rudras777/rivexis`, branch `main`.
- Current implementation/config head before this state-only commit: `b1fcda6f7e197ca6b3352c899aa8a60dec2d5d9d`.
- Brevo transport implementation commit: `f4a9393f2c7c8988cfcc41fed3009db586026150` (`Add fail-closed Brevo transactional email boundary`).
- Environment-contract commit: `b1fcda6f7e197ca6b3352c899aa8a60dec2d5d9d` (`Document fail-closed Brevo environment contract`).
- CI #306 (`35920966567`) passed API, web/E2E, invariants and PostgreSQL migration/runtime-control jobs for the transport implementation.
- CI #307 (`35921041970`) passed API, web/E2E, invariants and PostgreSQL migration/runtime-control jobs for the combined implementation plus `.env.example` contract.

## Transactional email status

Brevo owner-side phone/account verification remains recorded as complete.

Live Brevo inspection on 2026-09-24 verified:

- SMTP relay is enabled on the connected Rivexis Brevo account;
- an active Rivexis sender exists;
- the available sender is currently a Gmail address, which is not evidence that an owned Rivexis domain has been authenticated;
- no transactional templates existed before this production-build slice.

Created live Brevo assets, intentionally inactive:

- template `1`: `Rivexis — Account verification code`, tag `rivexis-auth-verification`;
- template `2`: `Rivexis — Password reset`, tag `rivexis-auth-password-reset`.

Repository implementation now includes:

- `apps/api/rivexis_api/services/transactional_email.py` as the fail-closed Brevo send boundary;
- `apps/api/tests/test_transactional_email.py` covering disabled/incomplete config, provider acceptance semantics, sandbox drop, idempotency, sensitive-error suppression and malformed success responses;
- `.env.example` with disabled-by-default Brevo configuration;
- `docs/TRANSACTIONAL_EMAIL.md` with activation and delivery-certification gates.

Important semantics:

- successful Brevo send API responses are recorded only as `accepted` (or `sandbox_accepted`), never `delivered`;
- true delivered/bounced/failed lifecycle state requires later Brevo transactional-event/webhook evidence;
- no production verification/password-reset endpoint has been exposed yet;
- no real auth email was sent in this slice;
- templates remain inactive until production sender/domain authentication, runtime secret installation, sandbox certification and controlled real delivery verification are complete.

## Cloudflare / live frontend

The P1 frontend deployment drift discovered earlier remains unresolved: the live `rivexis-web` deployment does not yet have verified parity with current `main`, and earlier unauthenticated `/workspace` behavior exposed an older generic/demo-safe shell even though current source is fail-closed.

The Cloudflare app tag is visible in ChatGPT, but no callable Cloudflare connector actions were exposed to this chat runtime during this slice. The previous TinyFish browser route also lacked an authenticated Cloudflare dashboard session. No Cloudflare project, DNS, billing, secret or deployment change was made.

## Other production gates retained

- FastAPI production runtime remains blocked on an explicitly approved FastAPI-capable deployment path; the current free-tier API Worker remains the intentional degraded boundary.
- Custom domain remains unselected/unverified.
- Owned-domain Brevo sender authentication and real delivery certification remain incomplete.
- External providers that require credentials, commercial licensing or customer-specific contracts remain explicitly unavailable rather than simulated.
- Arkham remains license/terms-gated; Hypernative-native screening remains customer-schema/contract-gated where an exact approved contract is absent.

## Active product milestone

Milestone F — Ten-engine completion remains active. The F2 audit-metadata trust boundary completed immediately before this email slice and is preserved. Remaining engine-depth work is documented in `docs/BUILD_EXECUTION_PLAN.md` and `docs/TEN_ENGINE_CONTRACT_AUDIT.md`.

## Next execution order

1. If callable/authenticated Cloudflare access becomes available, inspect the existing `rivexis-web` Git/deployment configuration, deploy current `main` only if the existing setup is safe, then retest unauthenticated `/workspace`, login/signup and API-boundary behavior.
2. Do not activate real Brevo auth mail until owned-domain/sender and runtime-secret gates are certified. The next email implementation depth is persistent verification/reset state, enumeration-safe endpoints, rate limits/resend cooldowns and transactional-event lifecycle ingestion.
3. If Cloudflare/email external gates remain blocked, continue the highest-value deterministic Milestone F engine-depth slice and full-CI gate it.
