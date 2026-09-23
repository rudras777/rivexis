# Rivexis Current Build State

Last updated: 2026-09-24

This file is the compact resume point for the dedicated normal-ChatGPT production-build program. It supplements the historical execution plan and overrides stale point-in-time blocker wording where this file records newer verified evidence.

## Repository and CI

- Repository: public `rudras777/rivexis`, branch `main`.
- Public GitHub Pages fallback work remains preserved and operational. It is a public fallback/navigation surface, not proof of Cloudflare deployment parity or FastAPI production readiness.
- Latest fully certified application/state head before this documentation-only sync: `149f37d6243d435eb6d42f106e3d1b14b899e2e7`.
- CI #349 (`35933475754`) completed successfully on that head across API ruff/pytest/pip-audit, web typechecks/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and PostgreSQL migration/runtime-control certification.
- GitHub Pages deployment #20 (`35933475211`) also completed successfully on `149f37d6243d435eb6d42f106e3d1b14b899e2e7`.
- This certified lineage includes the B1 dynamic-ABI implementation `bab6bf2b56fbdef7bfc059f9e6e5c169da567838` and focused regression commit `e285b83af7d3a70f4052d9c8e41d298456869bf6`.
- Prior B2/B3/F3/F2, F1/B1/B4 and B5/F4/F5 campaigns remain preserved.

## Latest Milestone F continuation — B1 verified ABI dynamic decoding

- Canonical B1 engine contract remains `1.3.0`.
- Verified-ABI `bytes` and `string` parameters now require canonical 32-byte-aligned offsets, offsets outside the static head, complete length words, bounded tails and zero right-padding.
- Dynamic arrays of supported one-word static elementary types (`address`, `bool`, bounded `uintN`/`intN`, and `bytesN`) are decoded with the same canonical element validation used by static ABI parameters.
- Dynamic arrays are bounded to 4096 elements so malformed or adversarial calldata cannot request unbounded decoder work.
- Invalid offsets, truncated tails, impossible lengths, non-zero dynamic padding and malformed array elements now return `MALFORMED_VERIFIED_ABI_CALLDATA` with an explicit reason instead of plausible partial values.
- Tuple, fixed-array and nested/composite dynamic types that the bounded decoder does not yet support return `UNSUPPORTED_VERIFIED_ABI_TYPE` with confidence 0 rather than fabricated decoding.
- Focused regression coverage includes canonical dynamic bytes/string/address arrays plus malformed offset, bounds, padding and bool-array cases, and explicit tuple/fixed-array unsupported behavior.

## Previously certified Milestone F hardening retained

- **B2:** engine `1.1.0`, calculation `b2-live-1.2.0`; bytecode is validated and block-pinned, transaction identities validate, and approval decoding reuses canonical ABI rules.
- **B3:** engine `1.1.0`, calculation `b3-live-1.2.0`; balance/code/supply/Chainlink reads share one captured block and timestamp semantics remain fail-closed.
- **B4:** engine `1.0.0`; direct native balance is pinned to its captured block and indexed-history/attribution integrity remains fail-closed.
- **B5:** engine `1.2.0`, calculation `b5-live-1.3.0`; route request/economics/structure contradictions become `CONFLICTING_DATA`/UNKNOWN with zero route score.
- **F1:** engine `1.2.0`, calculation `f1-live-1.3.0`; one captured block pins all requested native/ERC-20 holdings reads and incomplete explicit holdings never receive subset scoring.
- **F2:** engine `1.2.0`, calculation `f2-live-1.3.0`; boolean provider TVL/timestamps cannot become numeric facts and audit metadata remains bounded/descriptive only.
- **F3:** engine `1.3.0`, calculation `f3-live-1.3.0`; modeled quantities reject bool/non-finite values, oracle reads are block-pinned, and Chainlink/CoinGecko freshness is explicit.
- **F4:** engine `1.2.0`; invalid/contradictory optional APY/sigma evidence fails closed.
- **F5:** engine `1.2.0`; booleans cannot become numeric treasury values and market freshness requires complete credible timestamp coverage.

## Transactional email status

Brevo owner-side phone/account verification remains recorded as complete. SMTP relay and an active sender were verified; the observed sender is Gmail and is not evidence of an authenticated Rivexis-owned domain. Template `1` (`Rivexis — Account verification code`) and template `2` (`Rivexis — Password reset`) remain intentionally inactive.

The repository contains the fail-closed transactional transport, targeted tests, disabled-by-default environment contract and `docs/TRANSACTIONAL_EMAIL.md`. Brevo API success is treated only as `accepted`/`sandbox_accepted`, never as delivered. Activation remains gated on owned-domain sender authentication, runtime secret installation, sandbox certification, controlled real delivery and transactional lifecycle-event evidence.

## Cloudflare / live frontend

The P1 Cloudflare deployment drift remains unresolved. Earlier live verification showed an older generic/demo-safe workspace shell at unauthenticated `/workspace`, while current source withholds authenticated workspace content until `/api/v1/workspaces` authorizes access.

A fresh Cloudflare dashboard automation on 2026-09-24 used the available saved browser profile/vault and terminated with the explicit blocker that no Cloudflare credentials were configured for the available browser account/profile. Therefore the existing `rivexis-web` project, its GitHub/main integration and deployed commit/version could not be inspected or redeployed. No Cloudflare deployment, DNS, billing, environment-variable, secret, route, project or API Worker setting was changed.

The plugin directory also exposed no callable native Cloudflare connector in this chat runtime. GitHub Pages success does not resolve Cloudflare deployment parity.

## Other production gates retained

- FastAPI production runtime remains blocked on an explicitly approved FastAPI-capable production path; the free-tier API Worker remains the intentional degraded boundary.
- Custom domain remains unselected/unverified.
- Owned-domain Brevo sender authentication and real delivery certification remain incomplete.
- External provider credentials, commercial licenses and customer-specific contracts remain explicit gates where applicable.
- Arkham remains license/terms-gated; Hypernative-native screening remains customer-schema/contract-gated where an exact approved contract is absent.

## Active product milestone

Milestone F — Ten-engine completion remains active. Deterministic repository integrity is materially deeper across all ten engines, but evidence/capability depth is not declared complete.

Remaining depth includes deeper B1 internal-call/state/security semantics and tuple/fixed/nested ABI support only where justified; approved independent B2/B3 threat/security evidence and continuous monitoring; B4 cross-chain/protocol-semantic attribution plus stricter external-evidence provenance/freshness; B5 independent bridge-security/liquidity/incident evidence; F1 automatic/indexed discovery plus NFT/DeFi positions; and deeper independent F2/F4/F5 dependency, liquidity, governance/counterparty and strategy evidence.

## Next execution order

1. If authenticated Cloudflare access becomes available, inspect the established `rivexis-web` configuration, deploy current `main` only through the existing safe project, then re-certify unauthenticated `/workspace`, login/signup and API-boundary behavior.
2. Keep Brevo authentication mail inactive until owned-domain/sender and delivery-lifecycle gates are certified.
3. Otherwise continue Milestone F capability depth through the highest-value deterministic slice; the next audited target is B4 external indexed/entity evidence provenance and aggregate freshness, while preserving explicit UNKNOWN/unavailable states where provider contracts or credentials are absent.
