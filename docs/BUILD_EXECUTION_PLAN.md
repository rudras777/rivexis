# Rivexis Build Execution Plan

Last updated: 2026-09-24  
Authoritative project mandate: `Rivexis_Production_Master_Prompt_Normal_Chat.txt`

## Current verified baseline

- Repository: private `rudras777/rivexis`; default branch `main`.
- Latest fully certified implementation head before documentation synchronization: `e01fa907b58a8adbecfe604d5545f677d2e4a6d8`.
- Frontend: Next.js 16 / React 19 / TypeScript on Cloudflare Workers using vinext.
- API: FastAPI is the authoritative application backend. The free Cloudflare Worker API is an explicit degraded placeholder, not a replacement runtime.
- Supabase project `ivszvufdonfgwjpfgwii` was previously verified `ACTIVE_HEALTHY` in `ap-south-1` with least-privilege application access and no security-advisor findings.
- Brevo fail-closed transactional transport and disabled-by-default environment contract are implemented; verification/reset templates exist but remain intentionally inactive until production sender/domain and delivery-lifecycle certification.
- CI #316 (`35923236659`) on `e01fa907b58a8adbecfe604d5545f677d2e4a6d8` passed API lint/tests/pip-audit, frontend type/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and real PostgreSQL migration/runtime-control certification.

## Milestone sequence

1. **A — Baseline and product audit**
2. **B — Design system and application shell**
3. **C — Authentication and onboarding**
4. **D — Workspace foundations**
5. **E — Analysis framework**
6. **F — Ten-engine completion**
7. **G — Monitoring, investigations and reports**
8. **H — Institutional controls**
9. **I — Production deployment**
10. **J — Production certification and launch**

## Current active milestone

**Milestone F — Ten-engine completion**

Milestone E remains complete at repository-test level. The shared analysis/decision framework preserves canonical evidence, uncertainty, versions and provenance from persisted engine output through decisions, explanations, reports and workspace history.

Milestone F is **in progress**. Repository-level input/provider/freshness/parser/runtime integrity is deeply regression-tested across all ten specialist engines. This is not a declaration that all evidence-depth capabilities are complete; remaining work is deeper evidence collection/normalization through approved deterministic sources.

A live-production discrepancy remains open: earlier verification showed an older generic/demo-safe workspace shell on unauthenticated Cloudflare `/workspace`, while current `main` fails closed and withholds workspace content until access is authorized. A fresh 2026-09-24 Cloudflare dashboard attempt again reached sign-in without an authenticated session, so the existing `rivexis-web` deployment identity/Git integration could not be inspected or changed. No Cloudflare deployment, DNS, billing, secret, route, environment or project setting was modified.

### Milestone F acceptance targets

- audit B1–B5 and F1–F5 against intended live-provider/direct-state contracts;
- distinguish deterministic repository defects from credential/license/customer-contract gates;
- maintain explicit versioned outputs, provenance, freshness and reproducible UNKNOWN-compatible failure states;
- prohibit synthetic provider facts and unsupported safe conclusions;
- fail closed on contradictory provider/request evidence rather than normalizing it into plausible scores;
- preserve workspace authorization, canonical persistence and workspace-switch isolation;
- require full CI before advancing from integrity hardening to a deeper capability claim;
- do not advance to Milestone G until remaining engine-depth acceptance work is explicitly closed.

## Milestone F completed evidence so far

- Cross-engine dispatch enforces canonical current engine/evidence versions, evidence-derived provider consensus and first-class unresolved conflict semantics.
- **B1:** standard ERC-20/ERC-721/ERC-1155 effects are normalized only from validated event logs; receipt vs simulation evidence is distinguished; ERC-1155 layout and log bounds are enforced.
- **B2:** malformed addresses/hashes are rejected before provider use; RPC-resolved transaction addresses are revalidated.
- **B3:** current/prior state and monitoring thresholds are validated; stale/future oracle semantics fail closed without fabricated deltas.
- **B4:** malformed indexed state is excluded, token identity is contract-based, conflicting decimals are skipped, and concentration is descriptive only.
- **B5:** canonical engine contract remains `1.2.0`, while hardened route calculation evidence is `b5-live-1.3.0`. In addition to chain/token/amount/address/slippage/output checks, gas/fee rows must be valid finite non-negative USD values; execution duration and step structure are validated. Any contradiction becomes `CONFLICTING_DATA`/UNKNOWN with zero route score. CI #312 (`35922406982`) passed.
- **F1:** explicitly requested reads cannot be silently subset-scored; positive exposures require complete positive finite pricing before weights/HHI/concentration.
- **F2:** unusable fundamentals, degraded freshness and malformed audit metadata fail closed; provider audit links remain descriptive screening metadata only.
- **F3:** explicit authoritative adapter requests cannot silently fall back to generic modeled positions.
- **F4:** unique pool selection and core APY/TVL integrity are preserved. Optional reward APY and sigma now fail closed when non-finite, boolean, negative or internally contradictory; reward APY above headline APY is not clamped into a plausible score. CI #314 (`35922900454`) passed.
- **F5:** treasury numeric fields reject booleans as economic values; stablecoin remains strict boolean. Market freshness is asserted only with usable timestamp coverage for every requested CoinGecko asset; missing/malformed/future timestamps remain `UNKNOWN`. Combined CI #316 (`35923236659`) passed the complete matrix on `e01fa907`.

## Remaining Milestone F work

These are capability-depth items, not currently known hidden build/test errors:

- B1 deeper internal-call/state/security semantics beyond standard transfer/approval normalization.
- B2/B3 deeper independent external threat/security evidence where an approved provider contract exists; B3 remains point-in-time rather than continuous provider-native monitoring.
- B4 cross-chain activity and richer protocol-semantic/counterparty attribution.
- B5 independent bridge-security, liquidity and incident evidence beyond route-aggregator evidence.
- F1 automatic/indexed token discovery plus NFT/DeFi position ingestion from approved sources.
- F2/F4/F5 deeper independent dependency, liquidity, governance/counterparty and strategy evidence.
- Complete engine-depth certification before advancing to Milestone G.

## Existing platform integrity retained

- Browser auth uses HttpOnly cookies plus CSRF; browser bearer-token storage is not introduced.
- Workspace reads/writes fail closed and remain permission-aware in current source.
- Old-workspace delayed responses are discarded after workspace switching.
- Global provider registry configuration remains separate from workspace runtime telemetry.
- External/provider absence stays explicit UNKNOWN/unavailable rather than fabricated evidence.

## Dependencies and blockers

- **Cloudflare production deployment drift:** BLOCKED on authenticated Cloudflare dashboard access. The latest browser check again redirected to sign-in; `rivexis-web` Git/main integration and deployed commit remain unverified. No Cloudflare changes were made.
- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval or another explicitly approved FastAPI-capable production path. The current API Worker remains a degraded health/503 boundary.
- **Custom domain:** BLOCKED on domain choice/ownership/configuration.
- **Production email:** Brevo phone/account verification is complete; fail-closed transport, environment contract and inactive templates are implemented. Owned-domain sender authentication, production runtime secret installation, sandbox certification, real delivery verification and transactional lifecycle-event evidence remain outstanding.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths stay UNKNOWN/unavailable.
- **Arkham:** license/terms-gated.
- **Hypernative native screening:** customer-schema/contract-gated where no approved exact request/signing contract exists.
- **Live authenticated analysis certification:** BLOCKED until current frontend source and a live FastAPI application runtime can be independently certified.
- **Production certification:** incomplete until real Rivexis-owned targets satisfy deployment/browser/provider/email gates.

## Next action

If authenticated Cloudflare access becomes available, inspect the established `rivexis-web` project/Git integration and deploy current `main` only through that existing safe configuration, then re-certify unauthenticated `/workspace`, login/signup and API-boundary behavior. Otherwise continue Milestone F capability depth through deterministic repository work, prioritizing B1/B4/F1 or another unblocked integrity/depth slice without inventing provider evidence. Keep Brevo authentication templates inactive until sender/domain and delivery-lifecycle gates are certified. Full-CI gate every implementation slice.
