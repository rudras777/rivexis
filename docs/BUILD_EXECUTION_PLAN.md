# Rivexis Build Execution Plan

Last updated: 2026-09-24  
Authoritative project mandate: `Rivexis_Production_Master_Prompt_Normal_Chat.txt`

## Current verified baseline

- Repository: public `rudras777/rivexis`; default branch `main`.
- Public GitHub Pages fallback files are preserved; they provide a public navigation fallback and do not replace or certify the Cloudflare application deployment.
- Latest fully certified application/state head before this documentation-only sync: `149f37d6243d435eb6d42f106e3d1b14b899e2e7`.
- CI #349 (`35933475754`) passed API ruff/pytest/pip-audit, frontend type/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and PostgreSQL migration/runtime-control certification on that head.
- GitHub Pages deployment #20 (`35933475211`) also passed on that head.
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

The live-production discrepancy remains open: earlier verification showed an older generic/demo-safe workspace shell on unauthenticated Cloudflare `/workspace`, while current source fails closed and withholds workspace content until access is authorized. The public GitHub Pages fallback does not establish Cloudflare parity. A fresh Cloudflare browser run on 2026-09-24 terminated because the available saved browser account/profile had no configured Cloudflare credentials. The plugin directory also exposed no callable native Cloudflare connector. No Cloudflare deployment or configuration was changed.

### Milestone F acceptance targets

- audit B1–B5 and F1–F5 against intended live-provider/direct-state contracts;
- distinguish deterministic repository defects from credential/license/customer-contract gates;
- maintain explicit versioned outputs, provenance, freshness and reproducible UNKNOWN-compatible failure states;
- prohibit synthetic provider facts and unsupported safe conclusions;
- fail closed on contradictory, malformed or non-canonical provider/request evidence rather than normalizing it into plausible scores or parameters;
- keep point-in-time state internally block-consistent where an EVM block reference is claimed;
- preserve workspace authorization, canonical persistence and workspace-switch isolation;
- require full CI before advancing from integrity hardening to a deeper capability claim;
- do not advance to Milestone G until remaining engine-depth acceptance work is explicitly closed.

## Milestone F completed evidence so far

- Cross-engine dispatch enforces canonical current engine/evidence versions, evidence-derived provider consensus and first-class unresolved conflict semantics.
- **B1:** standard event effects are validated/log-grounded; canonical address/bool/integer/fixed-bytes ABI rules prevent malformed permission-shaped calls from becoming plausible approvals. Verified-ABI dynamic `bytes`/`string` and dynamic arrays of supported one-word static elementary types now validate alignment, static-head boundaries, tail lengths, padding and elements. Arrays are bounded to 4096 items. Unsupported tuple/fixed-array/nested dynamic layouts return explicit unsupported state with zero confidence. This lineage is included in CI #349.
- **B2:** engine `1.1.0`, calculation `b2-live-1.2.0`. Target/sender/hash and RPC transaction bodies validate; contract bytecode is valid hex read at the captured block; approval rules reuse canonical calldata decoding.
- **B3:** engine `1.1.0`, calculation `b3-live-1.2.0`. Native balance, code, optional total supply and supplied Chainlink reads share one captured block tag. Future/stale oracle behavior and prior-snapshot validation remain fail-closed.
- **B4:** malformed indexed state is excluded, token identity is contract-based, concentration is descriptive, and direct native balance is pinned to the captured block. A new audit identified external indexed/entity provenance and aggregate freshness as the next deterministic integrity slice.
- **B5:** engine `1.2.0`, calculation `b5-live-1.3.0`. Request/output/economic/structural contradictions become `CONFLICTING_DATA`/UNKNOWN with zero route score.
- **F1:** engine `1.2.0`, calculation `f1-live-1.3.0`. One captured block pins requested native/ERC-20 holdings and explicit holdings remain all-or-nothing for scoring.
- **F2:** engine `1.2.0`, calculation `f2-live-1.3.0`. Identity/TVL/freshness/provider health and audit metadata fail closed; booleans cannot become numeric TVL/timestamps.
- **F3:** engine `1.3.0`, calculation `f3-live-1.3.0`. Modeled quantities/debt price validate as finite non-boolean economics; Chainlink reads are block-pinned with exact ABI shape and truthful timestamp freshness; CoinGecko comparison evidence has independent price/timestamp integrity.
- **F4:** engine `1.2.0`; unique pool selection and core/optional yield evidence integrity are preserved; impossible reward APY/sigma semantics fail closed.
- **F5:** engine `1.2.0`; treasury numerics reject booleans and market freshness requires credible complete timestamp coverage.

## Remaining Milestone F work

These are primarily capability-depth items rather than known hidden build/test failures:

- B1 deeper internal-call/state/security semantics; tuple/fixed-array/nested ABI decoding only where it materially improves transaction understanding and can remain bounded/canonical.
- B2/B3 deeper independent external threat/security evidence where an approved provider contract exists; B3 remains point-in-time rather than continuous provider-native monitoring.
- B4 external indexed/entity evidence provenance/freshness, cross-chain activity and richer protocol-semantic/counterparty attribution.
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

- **Cloudflare production deployment drift:** BLOCKED on authenticated Cloudflare access. Fresh browser automation confirmed the available saved profile/vault has no configured Cloudflare credentials; `rivexis-web` Git/main integration and deployed commit remain unverified. The GitHub Pages fallback is not a substitute for this certification.
- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval or another explicitly approved FastAPI-capable production path. The current API Worker remains a degraded health/503 boundary.
- **Custom domain:** BLOCKED on domain choice/ownership/configuration.
- **Production email:** Brevo phone/account verification is complete; fail-closed transport, environment contract and inactive templates are implemented. Owned-domain sender authentication, production runtime secret installation, sandbox certification, real delivery verification and transactional lifecycle-event evidence remain outstanding.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths stay UNKNOWN/unavailable.
- **Arkham:** license/terms-gated.
- **Hypernative native screening:** customer-schema/contract-gated where no approved exact request/signing contract exists.
- **Live authenticated analysis certification:** BLOCKED until current frontend source and a live FastAPI application runtime can be independently certified.
- **Production certification:** incomplete until real Rivexis-owned targets satisfy deployment/browser/provider/email gates.

## Next action

If authenticated Cloudflare access becomes available, inspect the established `rivexis-web` project/Git integration and deploy current `main` only through that existing safe configuration, then re-certify unauthenticated `/workspace`, login/signup and API-boundary behavior. Otherwise continue Milestone F with the audited B4 external indexed/entity provenance and aggregate-freshness slice, then proceed to the next highest-value deterministic capability without inventing provider evidence. Keep Brevo authentication templates inactive until sender/domain and delivery-lifecycle gates are certified. Full-CI gate every implementation slice.
