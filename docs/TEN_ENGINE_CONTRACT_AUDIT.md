# Rivexis Ten-Engine Contract Audit

Last updated: 2026-09-24

This audit distinguishes repository implementation gaps from external provider, credential, licensing and customer-contract gates. A missing commercial credential is not treated as a code defect; the engine must instead remain explicit about unavailable or partial evidence.

| Engine | Current live version | Grounding currently implemented | Safe live state / known gap |
|---|---:|---|---|
| B1 — Transaction Simulation | 1.3.0 | EVM RPC state/dry-run; mined transaction receipts for historical hashes; optional `debug_traceCall` call tree/prestate diff; Tenderly simulation/event logs when configured; optional verified ABI lookup | Fresh live outputs include deterministic transaction effects plus canonical standard ERC-20/ERC-721/ERC-1155 transfer/approval effects only from validated raw logs. Receipt logs are observed evidence; Tenderly logs are predicted evidence. ERC-1155 ABI layout and log-processing bounds are enforced. Deeper internal/state/security semantics remain incomplete. |
| B2 — Transaction & Contract Security | 1.1.0 | EVM RPC bytecode/calldata rules; optional Etherscan; Blockaid when resolved | EVM addresses/hashes are validated before provider use and RPC-resolved transaction addresses are revalidated. External threat coverage remains partial when approved providers are unavailable. |
| B3 — Threat & Monitoring | 1.1.0 | Validated RPC snapshots; balance/code/supply deltas; optional Chainlink state and configured threat provider | Snapshot identity/state/thresholds are validated. Future oracle timestamps stay UNKNOWN; stale/expired/policy-aged evidence becomes `STALE_DATA`. Continuous provider-native monitoring remains a capability gap. |
| B4 — Entity & Fund Flow | 1.0.0 | Direct wallet state; optional Etherscan history; optional Nansen; Arkham only when license-approved | Malformed numeric/indexed state is excluded, ERC-20 identity is contract-based, conflicting decimals are skipped, and concentration is descriptive rather than maliciousness/economic ownership evidence. Cross-chain and richer protocol/counterparty attribution remain incomplete. |
| B5 — Cross-Chain Route | 1.2.0 | LI.FI quote normalization plus request/response/economic/structure integrity validation | Calculation evidence is versioned `b5-live-1.3.0` while the canonical engine contract remains `1.2.0`. Chain/token/amount/address/slippage/output integrity is enforced. Gas/fee rows must contain finite non-negative USD values, execution duration must be finite/non-negative, and included steps must be structurally valid. Any request, economic or structural contradiction becomes `CONFLICTING_DATA` with UNKNOWN severity and zero route score. Matching routes stay `PARTIAL` because aggregator evidence is not independent bridge-security/liquidity/incident evidence. |
| F1 — Portfolio & Exposure | 1.2.0 | CoinGecko references; direct native/ERC-20 reads for declared assets; manual positions | Explicit reads fail closed on partial failure; positive exposures require positive finite pricing; duplicate/conflicting token metadata is deterministic. Automatic token discovery, NFTs and DeFi positions remain explicit gaps. |
| F2 — Protocol Risk | 1.2.0 | DefiLlama fundamentals plus optional protocol-native/adapter evidence | Core TVL/identity/freshness/provider-health trust boundaries are enforced. Audit metadata is bounded, HTTPS/credential-free and descriptive only; malformed or declaration-only audit claims cannot suppress missing-audit risk. Independent exploit/governance/liquidity/security depth remains partial. |
| F3 — Position & Liquidation Risk | 1.3.0 | Protocol-specific adapter where available; otherwise modeled position with direct oracle evidence and optional market/native checks | Explicit authoritative-adapter requests fail closed unless an authoritative position is actually returned. `PARTIAL`, `STALE_DATA`, `CONFLICTING_DATA` or unavailable states remain explicit. |
| F4 — Yield & Strategy Risk | 1.2.0 | Attributed DefiLlama yield-pool evidence plus optional protocol-native evidence | Broad selectors must resolve uniquely and core APY/TVL must be finite. Optional `apyReward` and `sigma` are also trust-boundary inputs: present-but-invalid/non-finite/bool values, negative reward APY, negative sigma, or reward APY above headline APY become `CONFLICTING_DATA` instead of being clamped/normalized into a score. Stale/expired observations become `STALE_DATA`; future observations remain UNKNOWN. Principal/security/oracle/withdrawal depth remains incomplete. |
| F5 — Treasury Allocation & Scenario | 1.2.0 | User allocation model; CoinGecko market references; optional protocol-native checks | Numeric treasury fields reject booleans as well as negative/non-finite/economically invalid values; `stablecoin` requires a real JSON boolean. Derived weights require complete positive valuation. CoinGecko freshness is asserted only with usable timestamp coverage for every requested asset; missing/malformed/non-finite/future timestamps remain `UNKNOWN` and cannot be called LIVE. Dependency/correlation/liquidity/counterparty depth remains incomplete. |

## Cross-engine contract rules

For newly executed live runs, the dispatcher enforces a canonical current engine version for each engine. Evidence inherits the parent engine contract version while preserving a more specific calculation version when needed. Historical persisted analyses are not rewritten.

Provider consensus is derived from evidence actually present: zero provider evidence cannot claim `SINGLE_SOURCE`; one provider is `SINGLE_SOURCE`; multiple providers are `MULTI_SOURCE`; unresolved conflicts are `CONFLICTING`. `USER_INPUT_ONLY` is preserved only for intentionally modeled results without provider evidence.

Unresolved provider conflicts are first-class analysis state. Fresh live results carrying unresolved source conflicts are promoted from ordinary completed/partial states to `CONFLICTING_DATA`; stale and terminal unavailable states remain stronger gates where applicable.

### Engine-specific trust-boundary notes

**B1.** Standard ERC-20/ERC-721/ERC-1155 effects come only from raw logs whose standard topic signature and ABI layout validate. Receipt logs for mined transactions are observed evidence; Tenderly simulation logs are predicted. Amounts/token IDs remain raw. ERC-1155 batches require canonical dynamic-array layout and log normalization is bounded with explicit omitted/truncated coverage.

**B2.** Malformed target/sender addresses and transaction hashes are rejected before provider calls; RPC-resolved transaction addresses are revalidated before downstream analysis.

**B3.** Current and prior snapshots are trust boundaries. Numeric EVM state, monitoring thresholds and Chainlink output/timestamps must validate; malformed prior fields suppress only their affected comparison rather than manufacturing change signals.

**B4.** Direct-chain and external-provider evidence stay distinct. Token identity is contract-based, malformed rows are excluded, and counterparty concentration is descriptive interaction concentration—not ownership, maliciousness or economic exposure.

**B5.** The caller route request and the LI.FI economic/structural response form one trust boundary. Besides chain/token/amount/address/slippage and output consistency, all gas/fee collections must be explicit lists of valid non-negative finite USD rows; malformed rows cannot silently disappear into a lower-cost route. Execution duration must be finite/non-negative and included steps must be structurally usable. Any contradiction is retained as evidence but route scoring is discarded. The engine contract remains `1.2.0`; the hardened calculation generation is `b5-live-1.3.0`.

**F1.** Explicit wallet/token reads are all-or-nothing for scoring. Positive exposures require complete positive finite prices before value/HHI/concentration scoring, and freshness requires credible timestamp coverage.

**F2.** Usable provider identity/core TVL/freshness are mandatory. DefiLlama audit counts/links cannot gain scoring trust through boolean truthiness, malformed/insecure references, contradictions or declaration-only claims. Even validated links remain provider-supplied screening metadata rather than proof of current safe code.

**F3.** An explicit protocol-adapter request cannot silently fall back to a generic modeled position when the authoritative adapter does not return a position.

**F4.** Strategy identity must resolve uniquely. Core APY/TVL are validated before scoring, and optional reward/volatility fields cannot carry impossible provider semantics into the score. Reward APY above headline APY is treated as contradictory evidence, not clamped to a plausible share. Negative sigma is invalid because sigma is a dispersion magnitude. Stale/expired timestamps remain a first-class gate and materially future timestamps do not count as current evidence.

**F5.** Treasury numbers reject booleans before float coercion, preventing `true`/`false` from becoming `1`/`0` economic values. When market references are requested, every requested CoinGecko asset must carry a usable observation timestamp before Rivexis asserts freshness. The oldest valid timestamp bounds freshness; missing, malformed or materially future timestamps keep freshness UNKNOWN. Unpriced derived-weight positions cannot silently receive zero exposure.

## External gates that remain non-code blockers

- Arkham remains license/terms-gated.
- Hypernative native screening remains customer-schema/contract gated where the exact authenticated request contract is not public/approved.
- Tenderly, Blockaid, Nansen, explorer and RPC behavior depends on deployment configuration and valid credentials/entitlements.
- Absence of those integrations must remain explicit provider-unavailable/partial/UNKNOWN-compatible evidence, not synthetic success.

## Latest repository evidence

- PR #26 — B1 canonical standard event effects — CI #271 (`35857083832`) PASS.
- PR #27 — F1 numeric/completeness integrity — CI #277 (`35861080306`) PASS.
- PR #28 — B4 token identity/counterparty-flow integrity — CI #282 (`35895021465`) PASS; merge `d8bb045800ee534d182acc88d094589bafa816a2`.
- PR #29 — B1 event parser ABI/input bounds — CI #287 (`35896050913`) PASS; merge `0d56ba9ca80e340b21ea48f6f990aa7d04d77b3e`.
- PR #30 — B3 monitoring runtime integrity — CI #293 (`35897012617`) PASS; merge `042f08376f3b27cbd87dec0df6fb72ed063cdb52`.
- `6eecf44c921c6b31dddc265c2e62c60ac664a44e` — F2 audit-metadata trust boundary — CI #302 (`35916994577`) PASS.
- `eccb38a2db4523d9db1e0b14b667b8714f98d544` — corrected/canonical B5 hardened contract — CI #312 (`35922406982`) PASS.
- `f2f45e8ef0ec43230cc886554002878a90c56df8` — F4 optional yield-metric contradictions — CI #314 (`35922900454`) PASS.
- `e01fa907b58a8adbecfe604d5545f677d2e4a6d8` — combined F5 boolean/freshness hardening with prior B5/F4 changes preserved — CI #316 (`35923236659`) PASS across API, web/E2E, invariants and PostgreSQL migration/runtime-control jobs.

## Remaining Milestone F work

Repository-level integrity defects identified so far are regression-covered. Remaining work is capability depth rather than a known hidden build/test failure: deeper B1 internal/state/security semantics; deeper B2/B3 external threat/security evidence and continuous monitoring where approved; B4 cross-chain/protocol-semantic attribution; F1 automatic/indexed token discovery plus NFT/DeFi positions; independent B5 bridge-security/liquidity/incident evidence; and deeper F2/F4/F5 dependency/liquidity/governance/counterparty/strategy evidence. Keep credential/licensing/customer-contract gaps explicit and add focused regression evidence before advancing to Milestone G.
