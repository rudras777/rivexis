# Rivexis Build Execution Plan

Last updated: 2026-09-24  
Authoritative project mandate: `Rivexis_Production_Master_Prompt_Normal_Chat.txt`

## Current verified baseline

- Repository: public `rudras777/rivexis`; default branch `main`.
- Public GitHub Pages fallback files are preserved; they provide a public navigation fallback and do not replace or certify the Cloudflare application deployment.
- Latest fully certified application head before this documentation-only state sync: `7a5f6aa284b35f8388915788ce1f444410f5ae4d`.
- CI #358 (`35977258512`) passed API ruff/pytest/pip-audit, frontend type/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and PostgreSQL migration/runtime-control certification on that head.
- GitHub Pages deployment #29 (`35977258067`) also passed on that head.
- Frontend: Next.js 16 / React 19 / TypeScript on Cloudflare Workers using vinext.
- API: FastAPI is the authoritative application backend. The free Cloudflare Worker API is an explicit degraded placeholder, not a replacement runtime.
- Supabase project `ivszvufdonfgwjpfgwii` was previously verified `ACTIVE_HEALTHY` in `ap-south-1` with least-privilege application access and no security-advisor findings.
- Brevo fail-closed transactional transport and disabled-by-default environment contract are implemented; verification/reset templates remain intentionally inactive until production sender/domain and delivery-lifecycle certification.

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

Milestone F remains **in progress**. Repository-level input/provider/freshness/parser/runtime integrity is deeply regression-tested across all ten specialist engines. This does not claim that all evidence-depth capabilities are complete; remaining work is deeper evidence collection/normalization through approved deterministic sources.

The Cloudflare frontend discrepancy was closed on 2026-09-24. Current application head `e6e8fea6162ae6b00e3915a165423096ab404aba` was rebuilt with the intended HTTPS API origin and deployed to `rivexis-web` as version `258a0507-177e-43ae-84da-ebc037d29d03` at 100% traffic. Live unauthenticated `/workspace` now fails closed and withholds navigation/content while the API is unavailable. Per-version preview URLs are explicitly disabled and verified disabled.

### Milestone F acceptance targets

- audit B1–B5 and F1–F5 against intended live-provider/direct-state contracts;
- distinguish deterministic repository defects from credential/license/customer-contract gates;
- maintain explicit versioned outputs, provenance, freshness and reproducible UNKNOWN-compatible failure states;
- prohibit synthetic provider facts and unsupported safe conclusions;
- fail closed on contradictory, malformed or non-canonical provider/request evidence rather than normalizing it into plausible scores or parameters;
- keep point-in-time state internally block-consistent where an EVM block reference is claimed;
- separate direct-state provenance/freshness from external indexer/intelligence provenance rather than spreading one source's block/time across another;
- verify contract-derived scaling metadata before turning raw token balances into economic quantities;
- preserve workspace authorization, canonical persistence and workspace-switch isolation;
- require full CI before advancing from integrity hardening to a deeper capability claim;
- do not advance to Milestone G until remaining engine-depth acceptance work is explicitly closed.

## Milestone F completed evidence so far

- Cross-engine dispatch enforces canonical current engine/evidence versions, evidence-derived provider consensus and first-class unresolved conflict semantics.
- **B1:** standard event effects are validated/log-grounded; canonical address/bool/integer/fixed-bytes ABI rules prevent malformed permission-shaped calls from becoming plausible approvals. Verified-ABI dynamic `bytes`/`string` and dynamic arrays of supported one-word static elementary types validate alignment, static-head boundaries, tail lengths, padding and elements under a bounded decoder. Unsupported tuple/fixed-array/nested dynamic layouts remain explicit. Certified in CI #350.
- **B2:** engine `1.1.0`, calculation `b2-live-1.2.0`. Target/sender/hash and RPC transaction bodies validate; contract bytecode is valid hex read at the captured block; approval rules reuse canonical calldata decoding.
- **B3:** engine `1.1.0`, calculation `b3-live-1.2.0`. Native balance, code, optional total supply and supplied Chainlink reads share one captured block tag. Future/stale oracle behavior and prior-snapshot validation remain fail-closed.
- **B4:** engine `1.0.0`. Direct native balance remains pinned/LIVE at the captured RPC block. Etherscan history and Nansen/Arkham label evidence no longer inherit that block without provider-specific proof; timestamp-less external evidence remains UNKNOWN and drives aggregate freshness to UNKNOWN while direct-state freshness remains separately LIVE. Focused regressions passed CI #353.
- **B5:** engine `1.2.0`, calculation `b5-live-1.3.0`. Request/output/economic/structural contradictions become `CONFLICTING_DATA`/UNKNOWN with zero route score.
- **F1:** engine `1.2.0`, calculation `f1-live-1.4.0`. One captured block pins requested native state and every declared ERC-20 `decimals()`/`balanceOf` read. Token `eth_call` quantities must be canonical single-word ABI uint256 returns, caller decimals must match on-chain decimals before scaling, and direct RPC quantities are uint256-bounded. Metadata contradictions/malformed values fail closed before market valuation. Provider-facing errors remain redacted. Certified in CI #358.
- **F2:** engine `1.2.0`, calculation `f2-live-1.3.0`. Identity/TVL/freshness/provider health and audit metadata fail closed; booleans cannot become numeric TVL/timestamps.
- **F3:** engine `1.3.0`, calculation `f3-live-1.3.0`. Modeled quantities/debt price validate as finite non-boolean economics; Chainlink reads are block-pinned with exact ABI shape and truthful timestamp freshness; CoinGecko comparison evidence has independent price/timestamp integrity.
- **F4:** engine `1.2.0`; unique pool selection and core/optional yield evidence integrity are preserved; impossible reward APY/sigma semantics fail closed.
- **F5:** engine `1.2.0`; treasury numerics reject booleans and market freshness requires credible complete timestamp coverage.

## Remaining Milestone F work

These are primarily capability-depth items rather than known hidden build/test failures:

- B1 deeper internal-call/state/security semantics; tuple/fixed-array/nested ABI decoding only where it materially improves transaction understanding and can remain bounded/canonical.
- B2/B3 deeper independent external threat/security evidence where an approved provider contract exists; B3 remains point-in-time rather than continuous provider-native monitoring.
- B4 cross-chain activity and richer protocol-semantic/counterparty attribution beyond the now-correct direct/external provenance boundary.
- B5 independent bridge-security, liquidity and incident evidence beyond route-aggregator evidence.
- F1 automatic/indexed token discovery plus NFT/DeFi position ingestion and independent token-identity/CoinGecko mapping from approved sources.
- F2/F4/F5 deeper independent dependency, liquidity, governance/counterparty and strategy evidence.
- Complete engine-depth certification before advancing to Milestone G.

## Existing platform integrity retained

- Browser auth uses HttpOnly cookies plus CSRF; browser bearer-token storage is not introduced.
- Workspace reads/writes fail closed and remain permission-aware in current source.
- Old-workspace delayed responses are discarded after workspace switching.
- Global provider registry configuration remains separate from workspace runtime telemetry.
- External/provider absence stays explicit UNKNOWN/unavailable rather than fabricated evidence.

## Dependencies and blockers

- **Cloudflare production deployment drift:** RESOLVED for the frontend. Worker version `258a0507-177e-43ae-84da-ebc037d29d03` serves the current application source, uses the intended API origin, and passes live route/workspace checks. The Worker remains manually deployed rather than Git-integrated CI/CD.
- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval or another explicitly approved FastAPI-capable production path. The current API Worker remains a degraded health/503 boundary.
- **Custom domain:** BLOCKED on domain choice/ownership/configuration.
- **Production email:** Brevo phone/account verification is complete; fail-closed transport, environment contract and inactive templates are implemented. Owned-domain sender authentication, production runtime secret installation, sandbox certification, real delivery verification and transactional lifecycle-event evidence remain outstanding.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths stay UNKNOWN/unavailable.
- **Arkham:** license/terms-gated.
- **Hypernative native screening:** customer-schema/contract-gated where no approved exact request/signing contract exists.
- **Live authenticated analysis certification:** BLOCKED until current frontend source and a live FastAPI application runtime can be independently certified.
- **Production certification:** incomplete until real Rivexis-owned targets satisfy deployment/browser/provider/email gates.

## Next action

Deploy the authoritative FastAPI runtime on an explicitly approved production target, then configure exact HTTPS origins, PostgreSQL application credentials, distributed controls and Brevo secrets there before running authenticated browser and email-delivery certification. Keep Brevo templates inactive until owned-domain/sender and delivery-lifecycle gates are certified. Full-CI gate every implementation slice.
