# Rivexis Current Build State

Last updated: 2026-09-24

This file is the compact resume point for the dedicated normal-ChatGPT production-build program. It supplements the historical execution plan and overrides stale point-in-time blocker wording where this file records newer verified evidence.

## Repository and CI

- Repository: private `rudras777/rivexis`, branch `main`.
- Current fully certified implementation head before this state commit: `c9baf68a045b194b9c8adb1557ac77091ae20b00`.
- CI #328 (`35928391144`) passed the complete matrix on that head: API ruff/pytest/pip-audit, web typechecks/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and real PostgreSQL migration/runtime-control certification.
- The earlier B5/F4/F5 campaign remains preserved; this continuation added F1, B1 and B4 deterministic trust-boundary hardening without changing external provider scope.

## Milestone F integrity campaign — latest continuation

### F1 — Portfolio & Exposure

- Canonical engine contract remains `1.2.0`; direct portfolio evidence calculation generation is now `f1-live-1.3.0`.
- F1 now captures one `eth_blockNumber` and uses that exact hex block tag for every requested native balance and ERC-20 `balanceOf` read in the portfolio snapshot.
- Evidence records include the block tag and block number; no `latest` balance read can be stamped as though it came from the earlier captured block.
- Explicit wallet/token all-or-nothing semantics, positive finite pricing and complete CoinGecko timestamp coverage remain preserved.
- CI #322 (`35927503622`) passed the complete matrix for the F1 snapshot slice; the same changes are included in final CI #328.

### B1 — Transaction Simulation / ABI decoding

- Canonical B1 engine contract remains `1.3.0`.
- ABI-free standard calldata decoding now requires canonical 32-byte address encoding: the high 12 bytes of an address word must be zero.
- ABI booleans must be encoded as exactly `0` or `1`; other values remain malformed instead of becoming truthy.
- Malformed standard transfer/approval-shaped calldata is returned as `MALFORMED_STANDARD_CALLDATA` and is not promoted into call-trace approval candidates.
- Verified-ABI static decoding now enforces narrow integer widths/sign extension and fixed-bytes right-zero padding. Out-of-range `uintN`, incorrectly sign-extended `intN`, and non-zero `bytesN` padding return `MALFORMED_VERIFIED_ABI_CALLDATA` rather than plausible values.
- Focused regression tests cover canonical and malformed address/bool/integer/fixed-bytes behavior. Final CI #328 passed with these changes.

### B4 — Entity & Fund Flow

- Canonical engine contract remains `1.0.0`.
- B4 now validates the captured RPC block number before its direct wallet balance read and queries `eth_getBalance` at that exact block tag instead of `latest`.
- Direct-state evidence records the block tag it actually queried, and an explicit assumption documents that the balance snapshot was pinned before evidence was stamped with a block reference.
- Existing malformed-history, token-identity, metadata-conflict, attribution and descriptive-concentration semantics remain unchanged.
- Final CI #328 passed the B4 single-block snapshot regression together with the F1/B1 changes.

## Prior bulk Milestone F hardening retained

- **B5:** canonical engine `1.2.0`; calculation generation `b5-live-1.3.0`; route request, gas/fee economics, duration and included-step contradictions fail closed as `CONFLICTING_DATA`/UNKNOWN with zero score.
- **F4:** engine `1.2.0`; invalid/non-finite/negative reward APY or sigma and reward APY above headline APY fail closed as contradictory evidence.
- **F5:** engine `1.2.0`; booleans cannot become numeric treasury values and CoinGecko freshness requires valid timestamp coverage for every requested asset.
- **F2:** provider audit metadata remains bounded/descriptive only; malformed, insecure, contradictory or declaration-only audit claims cannot suppress missing-audit risk.

## Transactional email status

Brevo owner-side phone/account verification remains recorded as complete. SMTP relay and an active sender were verified; the observed sender is Gmail and is not evidence of an authenticated Rivexis-owned domain. Template `1` (`Rivexis — Account verification code`) and template `2` (`Rivexis — Password reset`) exist but remain intentionally inactive.

The repository contains the fail-closed transactional transport, targeted tests, disabled-by-default environment contract and `docs/TRANSACTIONAL_EMAIL.md`. Brevo API success is treated only as `accepted`/`sandbox_accepted`, never as delivered. No production verification/reset endpoint has been exposed and no real authentication email was sent. Activation remains gated on owned-domain sender authentication, runtime secret installation, sandbox certification, controlled real delivery and transactional lifecycle-event evidence.

## Cloudflare / live frontend

The P1 deployment drift remains unresolved. Earlier live verification showed an older generic/demo-safe workspace shell at unauthenticated `/workspace`, while current source withholds authenticated workspace content until `/api/v1/workspaces` authorizes access.

A Cloudflare dashboard check during the preceding bulk pass again redirected to sign-in. A plugin-directory recheck during this continuation also exposed no callable Cloudflare plugin in this chat runtime. Therefore the existing `rivexis-web` project, Git/main integration and deployed commit remain unverified. No deployment, DNS, billing, environment-variable, secret, route, project or API Worker setting was changed.

## Other production gates retained

- FastAPI production runtime remains blocked on an explicitly approved FastAPI-capable production path; the free-tier API Worker remains the intentional degraded boundary.
- Custom domain remains unselected/unverified.
- Owned-domain Brevo sender authentication and real delivery certification remain incomplete.
- External provider credentials, commercial licenses and customer-specific contracts remain explicit gates where applicable.
- Arkham remains license/terms-gated; Hypernative-native screening remains customer-schema/contract-gated where an exact approved contract is absent.

## Active product milestone

Milestone F — Ten-engine completion remains active. Repository-level integrity coverage is materially deeper, but capability depth is not declared complete.

Remaining depth includes deeper B1 internal/state/security semantics beyond canonical standard/verified-ABI normalization; B2/B3 independent threat/security evidence and continuous monitoring; B4 cross-chain/protocol-semantic attribution beyond the now-consistent direct-state snapshot; B5 independent bridge-security/liquidity/incident evidence; F1 automatic/indexed token discovery plus NFT/DeFi positions; and deeper independent F2/F4/F5 dependency, liquidity, governance/counterparty and strategy evidence.

## Next execution order

1. If authenticated Cloudflare access becomes available, inspect the established `rivexis-web` configuration, deploy current `main` only through that existing safe project, then re-certify unauthenticated `/workspace`, login/signup and API-boundary behavior.
2. Keep Brevo authentication mail inactive until owned-domain/sender and delivery-lifecycle gates are certified.
3. Otherwise continue the highest-value deterministic Milestone F capability-depth slice, with full CI gating and no fabricated provider capability.
