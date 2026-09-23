# Rivexis Current Build State

Last updated: 2026-09-24

This file is the compact resume point for the dedicated normal-ChatGPT production-build program. It supplements the historical execution plan and overrides stale point-in-time blocker wording where this file records newer verified evidence.

## Repository and CI

- Repository: private `rudras777/rivexis`, branch `main`.
- Current fully certified implementation head before this state update: `e01fa907b58a8adbecfe604d5545f677d2e4a6d8`.
- CI #316 (`35923236659`) passed the complete matrix on that head: API ruff/pytest/pip-audit, web typechecks/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and real PostgreSQL migration/runtime-control certification.
- The API suite completed 100% and pip-audit reported no known vulnerabilities for installed non-editable dependencies.
- Documentation commits may be ahead of `e01fa907`; they do not supersede that implementation certification unless a later implementation head is separately CI-certified.

## Bulk Milestone F integrity campaign — 2026-09-24

### B5 — Cross-Chain Route

- Canonical engine contract remains `1.2.0`; hardened calculation evidence is versioned `b5-live-1.3.0`.
- LI.FI gas/fee rows must now be a valid list of rows with finite, non-negative USD amounts; malformed, boolean, negative, NaN or infinite economics cannot disappear from the route.
- Execution duration must be finite and non-negative; included route steps must be a list of non-empty objects.
- Requested/quoted slippage must be finite and request-consistent.
- Route request/economic/structural contradictions fail closed as `CONFLICTING_DATA`, UNKNOWN severity and zero route score.
- CI #312 (`35922406982`) passed the full matrix after aligning the calculation hardening with the canonical `1.2.0` engine contract.

### F4 — Yield & Strategy Risk

- Engine contract remains `1.2.0`.
- Optional `apyReward` and `sigma` provider values are now trust-boundary inputs rather than permissive hints.
- Present-but-non-finite values, negative reward APY, negative sigma, boolean numeric values, or reward APY above headline APY fail closed as `CONFLICTING_DATA` instead of being clamped or allowed to distort scoring.
- A valid reward component is used as its exact ratio; no artificial normalization hides contradictory provider evidence.
- CI #314 (`35922900454`) passed API, web/E2E, invariants and PostgreSQL certification.

### F5 — Treasury Allocation & Scenario

- Engine contract remains `1.2.0`.
- Python/JSON booleans can no longer masquerade as numeric quantity, weight, capital, concentration or scenario-shock values.
- `stablecoin` remains a strict JSON boolean.
- CoinGecko freshness is asserted only when every requested market-reference asset has a usable timestamp.
- Missing, malformed, boolean, non-finite or materially future timestamps keep market freshness `UNKNOWN`; they are not clamped into LIVE/CURRENT evidence.
- The oldest usable timestamp across the requested asset set is the freshness boundary when complete coverage exists.
- Combined CI #316 (`35923236659`) passed the complete matrix on `e01fa907b58a8adbecfe604d5545f677d2e4a6d8`.

## Transactional email status

Brevo owner-side phone/account verification remains recorded as complete.

Verified Brevo state:

- SMTP relay is enabled;
- an active sender exists, currently a Gmail address; this is not evidence of owned Rivexis domain authentication;
- template `1`: `Rivexis — Account verification code`, tag `rivexis-auth-verification`, intentionally inactive;
- template `2`: `Rivexis — Password reset`, tag `rivexis-auth-password-reset`, intentionally inactive.

Repository implementation includes `apps/api/rivexis_api/services/transactional_email.py`, targeted tests, disabled-by-default `.env.example` configuration and `docs/TRANSACTIONAL_EMAIL.md`.

Important semantics remain unchanged: Brevo API success is `accepted`/`sandbox_accepted`, never proof of delivery; true delivered/bounced/failed lifecycle state requires transactional-event/webhook evidence. No production verification/reset endpoint has been exposed and no real authentication email was sent. Templates remain inactive pending owned-domain sender authentication, runtime secret installation, sandbox certification and controlled real delivery verification.

## Cloudflare / live frontend

The P1 deployment drift remains unresolved. Earlier live verification showed an older generic/demo-safe workspace shell at unauthenticated `/workspace`, while current source withholds workspace navigation/content until `/api/v1/workspaces` authorizes access.

A fresh Cloudflare dashboard check during this bulk pass again redirected to sign-in. No authenticated Cloudflare browser session was available, so the existing `rivexis-web` project, GitHub/main integration and deployed commit could not be inspected or changed. No deployment, DNS, billing, environment-variable, secret, route, project or API Worker change was made.

## Other production gates retained

- FastAPI production runtime remains blocked on an explicitly approved FastAPI-capable production path; the free-tier API Worker remains the intentional degraded boundary.
- Custom domain remains unselected/unverified.
- Owned-domain Brevo sender authentication and real delivery certification remain incomplete.
- External provider credentials, commercial licenses and customer-specific contracts remain explicit gates where applicable.
- Arkham remains license/terms-gated; Hypernative-native screening remains customer-schema/contract-gated where an exact approved contract is absent.

## Active product milestone

Milestone F — Ten-engine completion remains active. Repository-level integrity coverage is materially deeper after the B5/F4/F5 campaign, but capability depth is not declared complete.

Remaining depth includes B1 internal-call/state/security semantics; B2/B3 independent threat/security evidence and continuous monitoring; B4 cross-chain/protocol-semantic attribution; B5 independent bridge-security/liquidity/incident evidence; F1 automatic/indexed discovery plus NFT/DeFi positions; and deeper independent F2/F4/F5 dependency, liquidity, governance/counterparty and strategy evidence.

## Next execution order

1. If authenticated Cloudflare access becomes available, inspect the existing `rivexis-web` configuration, deploy current `main` only through the existing safe project, and re-certify unauthenticated `/workspace`, login/signup and API-boundary behavior.
2. Keep Brevo authentication mail inactive until owned-domain/sender and delivery-lifecycle gates are certified.
3. Otherwise continue the highest-value deterministic Milestone F depth slice, with full CI gating and no fabricated provider capability.
