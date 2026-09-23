# Rivexis Current Build State

Last updated: 2026-09-24

This file is the compact resume point for the dedicated normal-ChatGPT production-build program. It supplements the historical execution plan and overrides stale point-in-time blocker wording where this file records newer verified evidence.

## Repository and CI

- Repository: public `rudras777/rivexis`, branch `main`.
- Public GitHub Pages fallback work added after the prior resume point is preserved (`.nojekyll`, root `index.html`, and `404.html` route users toward the live Rivexis surface). It is a public fallback/navigation surface, not proof of Cloudflare deployment parity or FastAPI production readiness.
- Current fully certified implementation head before this state commit: `c5f9b083229e61297375f0c02ded6cc1ecdbada9`.
- CI #340 (`35931269784`) completed successfully on that head across API ruff/pytest/pip-audit, web typechecks/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and PostgreSQL migration/runtime-control certification.
- The prior F1/B1/B4 and B5/F4/F5 campaigns remain preserved; this bulk continuation added B2, B3, F3 and F2 trust-boundary hardening without inventing new external-provider capability.

## Bulk Milestone F integrity campaign — B2 / B3 / F3 / F2

### B2 — Transaction & Contract Security

- Canonical engine contract remains `1.1.0`; hardened calculation evidence is `b2-live-1.2.0`.
- B2 now captures and validates one RPC block and reads target bytecode at that exact block tag rather than `latest` before stamping block-referenced evidence.
- Contract bytecode must be valid even-length hex; malformed RPC bytecode cannot become plausible contract-presence evidence.
- B2 approval analysis now reuses the hardened canonical EVM calldata decoder. Non-zero high address padding and non-0/1 approval booleans remain malformed rather than becoming plausible approval parameters.
- RPC transaction-by-hash bodies and block quantities are validated before downstream use.

### B3 — Threat & Monitoring

- Canonical engine contract remains `1.1.0`; hardened snapshot calculation evidence is `b3-live-1.2.0`.
- One captured block now pins the entity native balance, runtime bytecode, optional token `totalSupply()`, and supplied Chainlink `decimals()` / `latestRoundData()` reads.
- Snapshot/evidence output records the block tag used, so point-in-time deltas cannot mix state from different `latest` blocks while claiming one block reference.
- Existing future-oracle UNKNOWN, stale-data gating, malformed prior-snapshot suppression, and explicit continuous-monitoring limitations remain preserved.

### F3 — Position & Liquidation Risk

- Canonical engine contract remains `1.3.0`; calculation evidence is now `f3-live-1.3.0`.
- Generic modeled quantities, liquidation thresholds, conflict tolerances and user debt price reject booleans and non-finite values; debt price must be positive.
- Chainlink round data must contain exactly five ABI words and normalize to a positive finite price.
- Modeled collateral/debt oracle reads are pinned to the captured RPC block.
- Missing, invalid or materially future oracle timestamps remain `UNKNOWN` rather than being clamped into fresh-looking observations.
- CoinGecko comparison prices must be positive finite; their observation timestamp is normalized independently and missing/invalid/future timestamps remain UNKNOWN rather than automatically CURRENT.
- Protocol-native health factors are validated before risk scoring.

### F2 — Protocol Risk

- Canonical engine contract remains `1.2.0`; calculation evidence is now `f2-live-1.3.0`.
- Boolean provider values can no longer pass through float coercion as TVL or timestamps.
- This applies to timestamped TVL history, top-level TVL and `currentChainTvls`; boolean core TVL is malformed provider evidence and fails closed instead of becoming `$0`/`$1`.
- Boolean TVL observation timestamps remain unusable, so freshness stays UNKNOWN and retrieval time is not promoted into provider observation time.
- Existing audit-metadata protections remain unchanged: audit references are bounded, HTTPS/credential-free, internally consistent and descriptive only.

## Previously certified Milestone F hardening retained

- **B1:** engine `1.3.0`; canonical standard-event normalization plus strict ABI address/bool/integer/fixed-bytes encoding.
- **B4:** engine `1.0.0`; direct native balance is pinned to its captured block and indexed-history/attribution integrity remains fail-closed.
- **B5:** engine `1.2.0`, calculation `b5-live-1.3.0`; route request/economics/structure contradictions become `CONFLICTING_DATA`/UNKNOWN with zero route score.
- **F1:** engine `1.2.0`, calculation `f1-live-1.3.0`; one captured block pins all requested native/ERC-20 holdings reads and incomplete explicit holdings never receive subset scoring.
- **F4:** engine `1.2.0`; invalid/contradictory optional APY/sigma evidence fails closed.
- **F5:** engine `1.2.0`; booleans cannot become numeric treasury values and market freshness requires complete credible timestamp coverage.

## Transactional email status

Brevo owner-side phone/account verification remains recorded as complete. SMTP relay and an active sender were verified; the observed sender is Gmail and is not evidence of an authenticated Rivexis-owned domain. Template `1` (`Rivexis — Account verification code`) and template `2` (`Rivexis — Password reset`) exist but remain intentionally inactive.

The repository contains the fail-closed transactional transport, targeted tests, disabled-by-default environment contract and `docs/TRANSACTIONAL_EMAIL.md`. Brevo API success is treated only as `accepted`/`sandbox_accepted`, never as delivered. No production verification/reset endpoint has been exposed and no real authentication email was sent. Activation remains gated on owned-domain sender authentication, runtime secret installation, sandbox certification, controlled real delivery and transactional lifecycle-event evidence.

## Cloudflare / live frontend

The P1 Cloudflare deployment drift remains unresolved. Earlier live verification showed an older generic/demo-safe workspace shell at unauthenticated `/workspace`, while current source withholds authenticated workspace content until `/api/v1/workspaces` authorizes access.

The repository now has a public GitHub Pages fallback, but that does not establish that `rivexis-web` is deployed from current `main`. The most recent Cloudflare dashboard attempt required account sign-in and the plugin directory exposed no callable Cloudflare connector in this chat runtime. No Cloudflare deployment, DNS, billing, environment-variable, secret, route, project or API Worker setting was changed during this campaign.

## Other production gates retained

- FastAPI production runtime remains blocked on an explicitly approved FastAPI-capable production path; the free-tier API Worker remains the intentional degraded boundary.
- Custom domain remains unselected/unverified.
- Owned-domain Brevo sender authentication and real delivery certification remain incomplete.
- External provider credentials, commercial licenses and customer-specific contracts remain explicit gates where applicable.
- Arkham remains license/terms-gated; Hypernative-native screening remains customer-schema/contract-gated where an exact approved contract is absent.

## Active product milestone

Milestone F — Ten-engine completion remains active. Deterministic repository integrity is materially deeper across all ten engines, but evidence/capability depth is not declared complete.

Remaining depth includes deeper B1 internal/state/security semantics; approved independent B2/B3 threat/security evidence and continuous monitoring; B4 cross-chain/protocol-semantic attribution; B5 independent bridge-security/liquidity/incident evidence; F1 automatic/indexed discovery plus NFT/DeFi positions; and deeper independent F2/F4/F5 dependency, liquidity, governance/counterparty and strategy evidence.

## Next execution order

1. If authenticated Cloudflare access becomes available, inspect the established `rivexis-web` configuration, deploy current `main` only through the existing safe project, then re-certify unauthenticated `/workspace`, login/signup and API-boundary behavior.
2. Keep Brevo authentication mail inactive until owned-domain/sender and delivery-lifecycle gates are certified.
3. Otherwise continue Milestone F capability depth through the highest-value deterministic slice, preserving explicit UNKNOWN/unavailable states where provider contracts or credentials are absent.
