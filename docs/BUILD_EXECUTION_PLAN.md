# Rivexis Build Execution Plan

Last updated: 2026-09-23  
Authoritative project mandate: `Rivexis_Master_Build_Prompt.txt`

## Current verified baseline

- Repository: private `rudras777/rivexis`; default branch `main`.
- Frontend: Next.js 16 / React 19 / TypeScript on Cloudflare Workers using vinext.
- API: FastAPI is the authoritative application backend. The free Cloudflare Worker API is an explicit degraded placeholder, not a replacement runtime.
- Supabase project `ivszvufdonfgwjpfgwii` is `ACTIVE_HEALTHY` in `ap-south-1`; 53 logical product tables plus 2 runtime-control tables were previously verified.
- CI covers API lint/tests/pip-audit, frontend type/build/vinext/npm-audit/Playwright/Axe, invariants/secret/migration checks, and real PostgreSQL migration/runtime-control checks.
- Milestone E repository framework is complete through PR #12 / CI #164 (`35832725687`).
- Milestone F cross-engine contract slices PR #13–#15 are merged and full-CI certified.
- Milestone F engine-specific integrity/depth slices now extend through PR #30. Latest code gate: PR #30 final head `efbff97df9574bd15c4e1b6c74850fcc59bd2c3f`, CI #293 (`35897012617`), merge `042f08376f3b27cbd87dec0df6fb72ed063cdb52`.
- Recent exact full-CI evidence includes PR #26 CI #271 (`35857083832`), PR #27 CI #277 (`35861080306`), PR #28 CI #282 (`35895021465`), PR #29 CI #287 (`35896050913`) and PR #30 CI #293 (`35897012617`).

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

Milestone E is complete at repository-test level. The shared analysis/decision framework preserves canonical evidence, uncertainty, versioning and provenance from persisted engine output through decisioning, explanations, reports, engine-result UI and workspace History.

Milestone F is **in progress**. Repository-level input/provider/freshness/parser/runtime integrity is now deeply regression-tested across all ten specialist engines. This still does **not** mean all engine-depth capabilities are complete; the remaining backlog is deeper evidence collection/normalization that requires approved sources or additional deterministic implementation.

### Milestone F acceptance targets

- audit all ten specialist engines B1–B5 and F1–F5 against intended live-provider/direct-state contracts, deterministic/demo behavior and current tests;
- identify exact repository-level gaps rather than treating absent commercial credentials as code defects;
- ensure each engine has a versioned output contract, explicit evidence/provider provenance, deterministic missing-data semantics and safe `PARTIAL`, `STALE_DATA`, `CONFLICTING_DATA`, `PROVIDER_UNAVAILABLE` or other UNKNOWN-compatible states where evidence is incomplete;
- prohibit synthetic provider facts, unsupported “safe” conclusions and silent fallback from live mode to demo assumptions or a different evidence model;
- verify engine-specific hard blockers, confidence, evidence freshness and provider consensus are reproducible and covered by focused tests;
- preserve workspace authorization, canonical persistence, decision integrity and in-place switch isolation;
- keep license/customer-contract gated providers such as Arkham or undocumented Hypernative-native contracts explicitly blocked rather than fabricating integration behavior;
- require full CI before declaring the ten-engine implementation complete enough to advance to Milestone G.

## Milestone E completed evidence

- `analysis_framework_version` is persisted on shared engine outputs and `decision_methodology_version` on decisions.
- Decisions rehydrate persisted `analysis_id` records before scoring; caller-supplied risk/confidence/severity/blocker/conflict changes cannot replace canonical stored evidence.
- Duplicate persisted analysis references and duplicate specialist-engine inputs cannot silently distort aggregate weighting.
- Requested partial, stale, conflicting or provider-unavailable evidence remains WAIT/UNKNOWN unless an explicit hard blocker independently requires AVOID.
- Decisions, explanations, HTML/PDF reports, engine-result UI and workspace History expose persisted provenance without inventing provider grounding.
- Workspace History provenance detail is active-workspace keyed and cleared on workspace changes; browser coverage proves old-workspace evidence does not remain visible after switching.

## Milestone F completed evidence so far

- `docs/TEN_ENGINE_CONTRACT_AUDIT.md` records B1–B5/F1–F5 current live versions, grounding sources, safe states, known depth gaps and external non-code gates.
- Cross-engine live dispatch normalizes current engine/evidence versions, derives source consensus from evidence actually present, preserves intentional user-input-only states, and promotes unresolved provider conflicts from ordinary `COMPLETED`/`PARTIAL` to `CONFLICTING_DATA` while leaving historical persisted analyses unchanged.
- F3 explicit authoritative protocol-adapter requests fail closed if the requested adapter does not actually return an authoritative position; generic modeled fallback is not substituted silently.
- **B1:** canonical transaction-effects output now includes standard ERC-20/ERC-721/ERC-1155 transfer/approval effects only from validated raw event logs. Mined receipt events are observed evidence; Tenderly simulation events are predicted evidence. Parser integrity requires canonical ERC-1155 batch ABI layout, bounds input-log processing and reports omitted/truncated coverage without inferring decimals/symbols/prices/ownership.
- **B2:** malformed EVM addresses/transaction hashes are rejected before provider use; transaction addresses resolved from RPC are revalidated before security analysis.
- **B3:** prior snapshots must match entity/network/dependencies; direct block/balance/bytecode/supply state and monitoring thresholds are validated; future Chainlink timestamps stay UNKNOWN; stale/expired/policy-aged oracle evidence becomes `STALE_DATA`; malformed prior fields suppress only the affected delta instead of fabricating signals.
- **B4:** malformed RPC/indexed state no longer becomes zero; ERC-20 asset identity is contract-based rather than symbol-based; conflicting token decimals are excluded; activity risk uses only valid normalized rows; directional counterparty flow and descriptive concentration are exposed without treating concentration as risk/identity evidence; external label freshness/identity conflicts remain explicit.
- **B5:** LI.FI quote chain/token/amount/address/slippage and minimum-output integrity are checked against the caller's route contract; mismatches fail closed as `CONFLICTING_DATA`/UNKNOWN rather than being scored normally.
- **F1:** caller-declared manual/native/ERC-20 exposures require valid non-negative quantities and complete positive pricing before concentration/HHI; explicitly requested wallet/token read failures prevent subset scoring; duplicate/conflicting token metadata is handled deterministically.
- **F2:** unusable DefiLlama protocol records, malformed provider-health metadata and non-finite/negative TVL fail closed; provider TVL timestamps drive freshness; stale/expired/degraded fundamentals become `STALE_DATA`.
- **F3:** authoritative-adapter trust boundary plus oracle/conflict/staleness semantics remain covered.
- **F4:** broad yield selectors must resolve uniquely, core APY/TVL must be finite, stale/expired pool evidence becomes `STALE_DATA`, and future-dated timestamps are not called current.
- **F5:** treasury model inputs must be finite/economically valid; derived weights require complete positive pricing rather than silently assigning zero exposure; stale market references become `STALE_DATA`.
- PRs #26–#30 each passed the full CI matrix before merge; latest engine-integrity gate is PR #30 CI #293 (`35897012617`).

## Remaining Milestone F work

These are capability-depth items, not currently known hidden build/test errors:

- B1 deeper internal-call/state/security semantics beyond standard transfer/approval event normalization.
- B2/B3 deeper independent external threat/security evidence where an approved provider contract exists; B3 remains point-in-time rather than continuous monitoring.
- B4 cross-chain activity and richer protocol-semantic/counterparty attribution beyond validated single-chain indexed history.
- B5 independent bridge-security, liquidity and incident evidence beyond route-aggregator evidence.
- F1 automatic/indexed token discovery plus NFT/DeFi position ingestion from approved evidence sources.
- F2/F4/F5 deeper independent dependency, liquidity, governance/counterparty and strategy evidence.
- Complete engine-depth certification before advancing to Milestone G.

## Existing platform integrity retained

- Browser auth uses HttpOnly cookies plus CSRF; browser bearer-token storage is not introduced.
- Workspace reads/writes fail closed and remain permission-aware.
- Engine/monitor/investigation/protocol-history delayed responses from an old workspace are discarded after switching.
- Shared/global provider registry configuration is separate from active-workspace runtime telemetry.
- Product constants are labeled as static metadata; workspace activity comes from authorized workspace APIs.
- External/provider absence remains explicit UNKNOWN/unavailable rather than fabricated evidence.

## Dependencies and blockers

- **FastAPI production runtime:** BLOCKED on explicit Workers Paid approval or another explicitly approved FastAPI-capable platform.
- **Custom domain:** BLOCKED on user domain choice/purchase approval.
- **Production email:** BLOCKED on Brevo phone verification, owned domain, domain authentication and action-time credential approval.
- **External providers:** BLOCKED where credentials, commercial licensing or customer-specific contracts are absent; unsupported paths remain UNKNOWN/unavailable.
- **Production secrets:** creation/rotation requires action-time confirmation where specified by the project mandate.
- **Arkham:** remains license/terms-gated; credentials alone do not authorize production use.
- **Hypernative native screening:** remains customer-schema/contract-gated where no approved exact request/signing contract is available.
- **Real deployed browser/auth/analysis certification:** BLOCKED until a live FastAPI runtime is available; repository-level browser/API evidence is not production evidence.
- **Production certification:** incomplete until real Rivexis-owned targets supply external gate evidence.

## Next action

Continue Milestone F with evidence-depth work that can be implemented without fabricating capability. Prioritize approved/deterministic normalization over unsupported provider claims, keep commercial/credential/customer-contract dependencies explicitly partial or blocked, and full-CI gate every slice. Do not advance to Milestone G until remaining engine-depth acceptance work is explicitly closed.
