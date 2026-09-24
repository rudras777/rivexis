# Rivexis Current Build State

Last updated: 2026-09-24

This file is the compact resume point for the dedicated normal-ChatGPT production-build program. It supplements the historical execution plan and overrides stale point-in-time blocker wording where this file records newer verified evidence.

## Repository and CI

- Repository: public `rudras777/rivexis`, branch `main`.
- Public GitHub Pages fallback remains operational. It is a public navigation/fallback surface, not proof of Cloudflare application parity or FastAPI production readiness.
- Latest fully certified application head before this documentation-only state sync: `7a5f6aa284b35f8388915788ce1f444410f5ae4d`.
- CI #358 (`35977258512`) passed the complete matrix on that head: API ruff/pytest/pip-audit, web typechecks/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and PostgreSQL migration/runtime-control certification.
- GitHub Pages deployment #29 (`35977258067`) also passed on `7a5f6aa284b35f8388915788ce1f444410f5ae4d`.
- This lineage includes the previously certified B1 dynamic-ABI and B4 provenance/freshness continuations plus the new F1 ERC-20 on-chain metadata/ABI integrity hardening.

## Latest Milestone F continuation

### F1 — explicit ERC-20 on-chain metadata and ABI integrity

- Canonical F1 engine contract remains `1.2.0`; calculation generation is now `f1-live-1.4.0`.
- Every explicitly requested ERC-20 contract is queried for `decimals()` at the same captured RPC block used for its `balanceOf(address)` reads.
- `decimals()` and `balanceOf(address)` must return canonical single-word ABI `uint256` data: exactly one 32-byte word. Short, oversized, non-hex or otherwise malformed `eth_call` return data fails closed rather than becoming a plausible quantity.
- Caller-supplied token decimals are treated as claimed metadata only. A caller/on-chain decimals disagreement returns `TOKEN_METADATA_MISMATCH` and prevents portfolio scoring; malformed or unsupported on-chain decimals return `INVALID_TOKEN_DECIMALS`.
- Direct JSON-RPC quantities used for block/native state are bounded to uint256; over-range values cannot enter valuation or block provenance.
- Successful on-chain decimal verification is recorded as `direct_token_metadata` evidence at the captured block before balance scaling.
- Contract address, symbol and CoinGecko ID remain caller-supplied identity/mapping metadata; Rivexis does not claim those identities were independently discovered merely because decimals matched on-chain.
- Provider errors continue to honor the existing redaction contract: internal mismatch details are not leaked through ordinary user-facing warning strings.
- Regression coverage includes metadata mismatch, malformed/oversized ABI words, unsupported decimals, over-uint256 direct quantities, exact same-block reads and preservation of market/completeness gates.
- F1 source/test head `7a5f6aa284b35f8388915788ce1f444410f5ae4d` passed CI #358 and Pages #29.

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
- B4 source/test head `61b728edf259ccafda256f2ab6f221e918e1f0ef` passed CI #353 and Pages #24.

## Previously certified Milestone F hardening retained

- **B2:** engine `1.1.0`, calculation `b2-live-1.2.0`; bytecode is validated/block-pinned, transaction identities validate, and approval decoding reuses canonical ABI rules.
- **B3:** engine `1.1.0`, calculation `b3-live-1.2.0`; balance/code/supply/Chainlink reads share one captured block and timestamp semantics remain fail-closed.
- **B5:** engine `1.2.0`, calculation `b5-live-1.3.0`; route request/economics/structure contradictions become `CONFLICTING_DATA`/UNKNOWN with zero route score.
- **F1:** engine `1.2.0`, calculation `f1-live-1.4.0`; one captured block pins requested native/ERC-20 state, on-chain decimals are verified before balance scaling, ABI words are canonical/bounded, and incomplete or contradictory explicit holdings never receive subset scoring.
- **F2:** engine `1.2.0`, calculation `f2-live-1.3.0`; boolean provider TVL/timestamps cannot become numeric facts and audit metadata remains bounded/descriptive only.
- **F3:** engine `1.3.0`, calculation `f3-live-1.3.0`; modeled quantities reject bool/non-finite values, oracle reads are block-pinned, and Chainlink/CoinGecko freshness is explicit.
- **F4:** engine `1.2.0`; invalid/contradictory optional APY/sigma evidence fails closed.
- **F5:** engine `1.2.0`; booleans cannot become numeric treasury values and market freshness requires complete credible timestamp coverage.

## Transactional email status

Brevo owner-side phone/account verification remains recorded as complete. SMTP relay and an active sender were verified; the observed sender is Gmail and is not evidence of an authenticated Rivexis-owned domain. Template `1` (`Rivexis — Account verification code`) and template `2` (`Rivexis — Password reset`) remain intentionally inactive.

The repository contains fail-closed transactional transport, targeted tests, a disabled-by-default environment contract and `docs/TRANSACTIONAL_EMAIL.md`. Brevo API acceptance is not treated as proof of delivery. Activation remains gated on owned-domain sender authentication, runtime secret installation, sandbox certification, controlled real delivery and delivered/bounced/failed lifecycle evidence.

## Cloudflare / live frontend

The P1 Cloudflare frontend drift was repaired on 2026-09-24. The `rivexis-web` Worker was rebuilt from current application head `e6e8fea6162ae6b00e3915a165423096ab404aba` with `NEXT_PUBLIC_RIVEXIS_API_URL=https://rivexis-api.rudrasingh0718.workers.dev` and deployed as Worker version `258a0507-177e-43ae-84da-ebc037d29d03` at 100% traffic.

Live browser verification confirmed that unauthenticated `/workspace` now withholds navigation and workspace content while the FastAPI runtime is unavailable. Homepage, login, signup and key public routes return successfully; a safe invalid-login probe reports temporary authentication-service unavailability without browser console errors. Per-version Worker preview URLs are explicitly disabled in `wrangler.jsonc` and verified disabled through the Cloudflare API. No DNS, custom domain, billing plan, secret, API Worker or database setting was changed.

## Other production gates retained

- FastAPI production runtime remains blocked on an explicitly approved FastAPI-capable production path; the free-tier API Worker remains the intentional degraded boundary.
- Custom domain remains unselected/unverified.
- Owned-domain Brevo sender authentication and real delivery certification remain incomplete.
- External provider credentials, commercial licenses and customer-specific contracts remain explicit gates where applicable.
- Arkham remains license/terms-gated; Hypernative-native screening remains customer-schema/contract-gated where an exact approved contract is absent.

## Active product milestone

Milestone F — Ten-engine completion remains active. Deterministic repository integrity is materially deeper across all ten engines, but evidence/capability depth is not declared complete.

Remaining depth includes deeper B1 internal-call/state/security semantics and bounded tuple/fixed/nested ABI support only where justified; approved independent B2/B3 threat/security evidence and continuous monitoring; B4 cross-chain/protocol-semantic attribution; B5 independent bridge-security/liquidity/incident evidence; F1 automatic/indexed token discovery plus NFT/DeFi positions and independent token-identity mapping; and deeper independent F2/F4/F5 dependency, liquidity, governance/counterparty and strategy evidence.

## Next execution order

1. Deploy the authoritative FastAPI application runtime on an explicitly approved paid Workers or other FastAPI-capable production target; the current free API Worker remains an honest degraded health/503 boundary.
2. Keep Brevo authentication mail inactive until owned-domain/sender, runtime secret and delivery-lifecycle gates are certified.
3. Continue Milestone F with the highest-value deterministic capability-depth slice, preserving explicit UNKNOWN/unavailable states when provider contracts or credentials are absent.
