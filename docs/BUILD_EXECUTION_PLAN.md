# Rivexis Build Execution Plan

Last updated: 2026-09-25
Authoritative project mandate: `Rivexis_Production_Master_Prompt_Normal_Chat.txt`

## Current verified baseline

- Repository: public `rudras777/rivexis`; default branch `main`.
- Public GitHub Pages fallback files are preserved; they provide a public navigation fallback and do not replace or certify the Cloudflare application deployment.
- Latest fully certified application head before this documentation-only state sync: `b2198bc508096e458560e077b41cb60f11fdcd5d`.
- CI #403 (`36168119939`) passed API ruff/pytest/pip-audit, frontend type/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and PostgreSQL migration/runtime-control certification on that head.
- GitHub Pages deployment #74 (`36168118741`) also passed on that head.
- Frontend: Next.js 16 / React 19 / TypeScript on Cloudflare Workers using vinext.
- API: FastAPI is the authoritative application backend. The free Cloudflare Worker API is an explicit degraded placeholder, not a replacement runtime.
- Supabase project `ivszvufdonfgwjpfgwii` is verified `ACTIVE_HEALTHY` in `ap-south-1` at migration `0013_auth_email_lifecycle`, with least-privilege application access. Its remaining Auth-platform leaked-password warning does not govern the FastAPI-owned password path.
- Brevo fail-closed transactional transport and disabled-by-default environment contract are implemented; verification/reset templates are active and controlled template delivery reached Gmail, while application-triggered substitution remains backend-deployment-gated.

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

The Cloudflare frontend discrepancy was closed on 2026-09-24. The frontend uses the intended HTTPS API origin and is deployed to `rivexis-web` as version `0d86a100-a115-4bca-a8ef-69d73be7a72d` at 100% traffic. Live unauthenticated `/workspace` fails closed and withholds navigation/content while the API is unavailable. Per-version preview URLs remain disabled.

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
- **B1:** engine `1.3.0`, calculation `b1-live-1.8.0`. Standard event effects, supported ABI decoding, internal traces and prestate diffs remain canonical and bounded. A non-verdicting structural security section now aggregates validated delegate/callcode context, creation/self-destruct paths, nested failures, broad permission candidates, account lifecycle and runtime-code changes. It exposes source coverage and explicitly does not claim maliciousness or safety. Tuple arrays, nested tuples and dynamic tuple members remain explicit unsupported layouts.
- **B2:** engine `1.1.0`, calculation `b2-live-1.3.0`. Target/sender/hash and RPC transaction bodies validate. RPC quantities are canonical and uint256-bounded; runtime bytecode is size-bounded, block-pinned and hashed; push-aware structural opcode observations and exact EIP-1167 extraction are explicitly non-verdicting. Explorer proxy metadata validates shape/address and retains independent UNKNOWN freshness. Direct/explorer implementation disagreement becomes an unresolved first-class conflict and `CONFLICTING_DATA`.
- **B3:** engine `1.1.0`, calculation `b3-live-1.3.0`. Native balance, bounded runtime code, optional total supply and supplied Chainlink reads share one captured block tag. RPC quantities and scalar ABI returns are canonical; change detection requires a dependency-identified snapshot from a strictly earlier block. Malformed Blockaid responses are unavailable, while timestamp-less valid screening remains UNKNOWN-fresh with no inherited RPC block. Direct state remains separately LIVE. Future/stale oracle behavior remains fail-closed.
- **B4:** engine `1.0.0`, calculation `b4-live-1.1.0`. Direct native balance remains pinned/LIVE at the captured RPC block with canonical uint256 quantities. Non-object indexer rows are explicitly counted as malformed. Native/ERC-20 self-transfers remain normalized activity but contribute zero directional flow and no self-counterparty concentration. Etherscan history and Nansen/Arkham label evidence retain independent UNKNOWN freshness without inheriting the RPC block.
- **B5:** engine `1.2.0`, calculation `b5-live-1.4.0`. Route/tool identity, uint256-bounded amounts, required minimum output, canonical approvals, bounded uniquely identified steps and bounded costs fail closed. Boolean slippage is rejected, contradictions become `CONFLICTING_DATA`/UNKNOWN with zero route score, and timestamp-less LI.FI quotes remain UNKNOWN-fresh rather than treating retrieval time as provider observation time. Certified in CI #401.
- **F1:** engine `1.2.0`, calculation `f1-live-1.4.0`. One captured block pins requested native state and every declared ERC-20 `decimals()`/`balanceOf` read. Token `eth_call` quantities must be canonical single-word ABI uint256 returns, caller decimals must match on-chain decimals before scaling, and direct RPC quantities are uint256-bounded. Metadata contradictions/malformed values fail closed before market valuation. Provider-facing errors remain redacted. Certified in CI #358.
- **F2:** engine `1.2.0`, calculation `f2-live-1.4.0`, shared collector `protocol-native-1.2.0`. Identity/TVL/freshness/provider health and audit metadata fail closed. Direct RPC state uses one captured canonical uint256 block; runtime code, EIP-1967 storage and oracle ABI responses are bounded/canonical. Malformed explorer identity data is unavailable, explorer evidence never inherits direct block/freshness, future oracle timestamps stay UNKNOWN, and aggregate freshness includes all retained evidence. Certified in CI #403.
- **F3:** engine `1.3.0`, calculation `f3-live-1.3.0`. Modeled quantities/debt price validate as finite non-boolean economics; Chainlink reads are block-pinned with exact ABI shape and truthful timestamp freshness; CoinGecko comparison evidence has independent price/timestamp integrity.
- **F4:** engine `1.2.0`; unique pool selection and core/optional yield evidence integrity are preserved; impossible reward APY/sigma semantics fail closed.
- **F5:** engine `1.2.0`; treasury numerics reject booleans and market freshness requires credible complete timestamp coverage.

## Remaining Milestone F work

These are primarily capability-depth items rather than known hidden build/test failures:

- B1 independently grounded asset/protocol identity plus deeper security semantics beyond its non-verdicting structural observations; nested/dynamic tuple and other composite ABI decoding only where it materially improves transaction understanding and can remain bounded/canonical.
- B2 deeper independent threat/security evidence plus implementation-code and upgrade-authority analysis where approved provider contracts exist; B3 independently timestamped threat evidence and continuous provider-native monitoring.
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

- **Cloudflare production deployment drift:** RESOLVED for the frontend. Worker version `0d86a100-a115-4bca-a8ef-69d73be7a72d` receives 100% traffic, uses the intended API origin, and passes live route/workspace checks. The Worker remains manually deployed rather than Git-integrated CI/CD.
- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval or another explicitly approved FastAPI-capable production path. The current API Worker remains a degraded health/503 boundary.
- **Custom domain:** BLOCKED on domain choice/ownership/configuration.
- **Production email:** Brevo phone/account verification is complete; fail-closed transport and the environment contract are implemented; verification/reset templates are active; controlled template sends reached Gmail and Brevo independently recorded delivery. Owned-domain sender authentication, production runtime secret installation, runtime parameter substitution and application-triggered lifecycle evidence remain outstanding.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths stay UNKNOWN/unavailable.
- **Arkham:** license/terms-gated.
- **Hypernative native screening:** customer-schema/contract-gated where no approved exact request/signing contract exists.
- **Live authenticated analysis certification:** BLOCKED until current frontend source and a live FastAPI application runtime can be independently certified.
- **Production certification:** incomplete until real Rivexis-owned targets satisfy deployment/browser/provider/email gates.

## Next action

Deploy the authoritative FastAPI runtime on an explicitly approved production target, then configure exact HTTPS origins, PostgreSQL application credentials, distributed controls and Brevo secrets there before running authenticated browser and application-triggered email-delivery certification. Preserve the active templates and fail-closed transport contract while the owned-domain and runtime lifecycle gates remain open. Full-CI gate every implementation slice.
