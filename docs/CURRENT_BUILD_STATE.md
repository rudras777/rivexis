# Rivexis Current Build State

Last updated: 2026-09-24

This file is the compact resume point for the dedicated normal-ChatGPT production-build program. It supplements the historical execution plan and overrides stale point-in-time blocker wording where this file records newer verified evidence.

## Repository and CI

- Repository: public `rudras777/rivexis`, branch `main`.
- Public GitHub Pages fallback remains operational. It is a public navigation/fallback surface, not proof of Cloudflare application parity or FastAPI production readiness.
- Latest fully certified application head before this documentation-only state sync: `61b728edf259ccafda256f2ab6f221e918e1f0ef`.
- CI #353 (`35934430946`) passed the complete matrix on that head: API ruff/pytest/pip-audit, web typechecks/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and PostgreSQL migration/runtime-control certification.
- GitHub Pages deployment #24 (`35934430378`) also passed on `61b728edf259ccafda256f2ab6f221e918e1f0ef`.
- This lineage includes the previously certified B1 dynamic-ABI continuation and the new B4 external-evidence provenance/freshness hardening.

## Latest Milestone F continuation

### B1 — verified ABI dynamic decoding

- Canonical B1 engine contract remains `1.3.0`.
- Verified-ABI `bytes` and `string` parameters require canonical aligned offsets, offsets outside the static head, complete bounded tails and zero ABI right-padding.
- Dynamic arrays of supported one-word static elementary types (`address`, `bool`, bounded `uintN`/`intN`, and `bytesN`) reuse canonical static decoding and are bounded to 4096 items.
- Invalid offsets, truncated tails, impossible lengths, non-zero padding and malformed array elements return `MALFORMED_VERIFIED_ABI_CALLDATA` rather than plausible partial values.
- Tuple, fixed-array and nested/composite dynamic types not supported by the bounded decoder return `UNSUPPORTED_VERIFIED_ABI_TYPE` with confidence 0 instead of fabricated decoding.
- The full B1 source/test/state lineage was already certified by CI #350 (`35933971343`) on resume head `2d0e2338e75114089e94c8623bb76fe7c8d79bf5`.

### B4 — external indexed/entity evidence provenance and freshness

- Canonical B4 engine contract remains `1.0.0`.
- Direct native-balance state remains pinned to the captured RPC block and is explicitly reported as LIVE direct-state evidence.
- Etherscan indexed-history evidence no longer inherits the current direct RPC block when the provider response does not establish one block-specific observation.
- Nansen/Arkham entity-label evidence no longer inherits the current direct RPC block when the provider does not provide block-specific provenance.
- Timestamp-less external indexed/entity evidence remains `UNKNOWN` freshness; retrieval time is retained only as the schema-required datetime fallback and is not treated as provider observation time.
- Aggregate B4 freshness is now `UNKNOWN` whenever such external evidence is consumed, while direct-state freshness remains separately `LIVE` with `direct_state_block_number` preserved.
- When no external evidence is consumed, the aggregate remains LIVE for the direct snapshot and unavailable external dimensions are stated explicitly rather than fabricated.
- Regression coverage verifies direct-state-only LIVE semantics, external-evidence `block_number=None`, UNKNOWN aggregate freshness for Etherscan/Nansen evidence, and preservation of the captured direct-state block.
- B4 source/test head `61b728edf259ccafda256f2ab6f221e918e1f0ef` passed CI #353 and Pages #24.

## Previously certified Milestone F hardening retained

- **B2:** engine `1.1.0`, calculation `b2-live-1.2.0`; bytecode is validated/block-pinned, transaction identities validate, and approval decoding reuses canonical ABI rules.
- **B3:** engine `1.1.0`, calculation `b3-live-1.2.0`; balance/code/supply/Chainlink reads share one captured block and timestamp semantics remain fail-closed.
- **B5:** engine `1.2.0`, calculation `b5-live-1.3.0`; route request/economics/structure contradictions become `CONFLICTING_DATA`/UNKNOWN with zero route score.
- **F1:** engine `1.2.0`, calculation `f1-live-1.3.0`; one captured block pins requested native/ERC-20 holdings reads and incomplete explicit holdings never receive subset scoring.
- **F2:** engine `1.2.0`, calculation `f2-live-1.3.0`; boolean provider TVL/timestamps cannot become numeric facts and audit metadata remains bounded/descriptive only.
- **F3:** engine `1.3.0`, calculation `f3-live-1.3.0`; modeled quantities reject bool/non-finite values, oracle reads are block-pinned, and Chainlink/CoinGecko freshness is explicit.
- **F4:** engine `1.2.0`; invalid/contradictory optional APY/sigma evidence fails closed.
- **F5:** engine `1.2.0`; booleans cannot become numeric treasury values and market freshness requires complete credible timestamp coverage.

## Transactional email status

Brevo owner-side phone/account verification remains recorded as complete. SMTP relay and an active sender were verified; the observed sender is Gmail and is not evidence of an authenticated Rivexis-owned domain. Template `1` (`Rivexis — Account verification code`) and template `2` (`Rivexis — Password reset`) remain intentionally inactive.

The repository contains fail-closed transactional transport, targeted tests, a disabled-by-default environment contract and `docs/TRANSACTIONAL_EMAIL.md`. Brevo API acceptance is not treated as proof of delivery. Activation remains gated on owned-domain sender authentication, runtime secret installation, sandbox certification, controlled real delivery and delivered/bounced/failed lifecycle evidence.

## Cloudflare / live frontend

The P1 Cloudflare deployment drift remains unresolved. Earlier live verification showed an older generic/demo-safe workspace shell at unauthenticated `/workspace`, while current source withholds authenticated workspace content until `/api/v1/workspaces` authorizes access.

A fresh Cloudflare dashboard automation on 2026-09-24 used the available saved browser profile/vault and terminated with the explicit blocker that no Cloudflare credentials were configured for the available browser account/profile. The existing `rivexis-web` project, GitHub/main integration and deployed commit/version therefore could not be inspected or redeployed. No Cloudflare deployment, DNS, billing, environment-variable, secret, route, project or API Worker setting was changed.

The plugin directory also exposed no callable native Cloudflare connector in this chat runtime. GitHub Pages success does not resolve Cloudflare deployment parity.

## Other production gates retained

- FastAPI production runtime remains blocked on an explicitly approved FastAPI-capable production path; the free-tier API Worker remains the intentional degraded boundary.
- Custom domain remains unselected/unverified.
- Owned-domain Brevo sender authentication and real delivery certification remain incomplete.
- External provider credentials, commercial licenses and customer-specific contracts remain explicit gates where applicable.
- Arkham remains license/terms-gated; Hypernative-native screening remains customer-schema/contract-gated where an exact approved contract is absent.

## Active product milestone

Milestone F — Ten-engine completion remains active. Deterministic repository integrity is materially deeper across all ten engines, but evidence/capability depth is not declared complete.

Remaining depth includes deeper B1 internal-call/state/security semantics and bounded tuple/fixed/nested ABI support only where justified; approved independent B2/B3 threat/security evidence and continuous monitoring; B4 cross-chain/protocol-semantic attribution; B5 independent bridge-security/liquidity/incident evidence; F1 automatic/indexed discovery plus NFT/DeFi positions; and deeper independent F2/F4/F5 dependency, liquidity, governance/counterparty and strategy evidence.

## Next execution order

1. If authenticated Cloudflare access becomes available, inspect the established `rivexis-web` configuration, deploy current `main` only through the existing safe project, then re-certify unauthenticated `/workspace`, login/signup and API-boundary behavior.
2. Keep Brevo authentication mail inactive until owned-domain/sender and delivery-lifecycle gates are certified.
3. Otherwise continue Milestone F with the highest-value deterministic capability-depth slice, preferring repository-verifiable evidence improvements over speculative provider integrations and preserving explicit UNKNOWN/unavailable states when provider contracts or credentials are absent.
