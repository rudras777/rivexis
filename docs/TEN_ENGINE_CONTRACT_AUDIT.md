# Rivexis Ten-Engine Contract Audit

Last updated: 2026-09-24

This audit distinguishes repository implementation gaps from external provider, credential, licensing and customer-contract gates. A missing commercial credential is not treated as a code defect; the engine must instead remain explicit about unavailable or partial evidence.

| Engine | Current live version | Grounding currently implemented | Safe live state / known gap |
|---|---:|---|---|
| B1 — Transaction Simulation | 1.3.0 | EVM RPC state/dry-run; mined receipts; optional `debug_traceCall`; Tenderly when configured; optional verified ABI lookup | Standard ERC event effects remain validated/log-grounded. Static ABI decoding enforces canonical address/bool/integer/fixed-bytes encodings. Verified-ABI dynamic `bytes`/`string` and dynamic arrays of supported one-word static elementary types validate offsets, head/tail bounds, zero padding and canonical elements under a bounded decoder. Unsupported tuple/fixed-array/nested composite layouts remain explicit `UNSUPPORTED_VERIFIED_ABI_TYPE`. Deeper internal/state/security semantics remain incomplete. |
| B2 — Transaction & Contract Security | 1.1.0 | EVM RPC bytecode/calldata rules; optional Etherscan; Blockaid when resolved | Calculation generation `b2-live-1.2.0`. Target/sender/hash validation is retained; bytecode is validated and read at the captured RPC block; approval analysis reuses canonical calldata decoding. External threat depth remains partial when approved providers are unavailable. |
| B3 — Threat & Monitoring | 1.1.0 | Validated RPC snapshots; balance/code/supply deltas; optional Chainlink state and configured threat provider | Calculation generation `b3-live-1.2.0`. Native balance, runtime code, optional total supply and supplied Chainlink reads share one captured block tag. Future oracle timestamps stay UNKNOWN; stale/policy-aged evidence becomes `STALE_DATA`. Continuous provider-native monitoring remains a capability gap. |
| B4 — Entity & Fund Flow | 1.0.0 | Direct wallet state; optional Etherscan history; optional Nansen; Arkham only when license-approved | Direct native balance remains pinned to the captured RPC block and LIVE. Timestamp-less Etherscan/Nansen/Arkham evidence no longer inherits that block; its freshness remains UNKNOWN and aggregate freshness is UNKNOWN whenever such external evidence is consumed. Malformed indexed state is excluded, ERC-20 identity is contract-based, conflicting decimals are skipped, and concentration remains descriptive only. Cross-chain and richer protocol/counterparty attribution remain incomplete. |
| B5 — Cross-Chain Route | 1.2.0 | LI.FI quote normalization plus request/response/economic/structure integrity validation | Calculation `b5-live-1.3.0`. Chain/token/amount/address/slippage/output integrity is enforced; gas/fee rows require finite non-negative USD values; duration/steps are validated. Contradictions become `CONFLICTING_DATA`/UNKNOWN with zero score. Independent bridge-security/liquidity/incident evidence remains incomplete. |
| F1 — Portfolio & Exposure | 1.2.0 | CoinGecko references; block-pinned direct native/ERC-20 reads for explicitly declared assets; manual positions | Calculation `f1-live-1.4.0`. One captured block pins all requested direct holdings and each declared ERC-20 `decimals()`/`balanceOf` read. `eth_call` uint256 returns must be canonical 32-byte ABI words, caller decimals must match on-chain decimals, and direct JSON-RPC quantities are uint256-bounded. Contradictory/malformed explicit holdings fail closed before valuation. Contract/symbol/CoinGecko identity remains caller-supplied and automatic discovery, NFTs and DeFi positions remain gaps. |
| F2 — Protocol Risk | 1.2.0 | DefiLlama fundamentals plus optional protocol-native/adapter evidence | Calculation `f2-live-1.3.0`. Core TVL/identity/freshness/provider-health and audit-metadata trust boundaries are enforced. Boolean TVL/timestamp values cannot become numeric facts. Audit metadata stays bounded, HTTPS/credential-free and descriptive only. Independent exploit/governance/liquidity/security depth remains partial. |
| F3 — Position & Liquidation Risk | 1.3.0 | Protocol-specific adapter where available; otherwise modeled position with direct oracle evidence and optional market/native checks | Calculation `f3-live-1.3.0`. Modeled quantities reject bool/non-finite values; user debt price must be positive finite; Chainlink ABI shape/prices validate; oracle reads share one captured block; missing/invalid/future timestamps remain UNKNOWN. CoinGecko comparison price/timestamp evidence is independently validated. |
| F4 — Yield & Strategy Risk | 1.2.0 | Attributed DefiLlama yield-pool evidence plus optional protocol-native evidence | Broad selectors resolve uniquely and core APY/TVL must be finite. Optional reward APY/sigma are trust-boundary inputs; invalid/non-finite/bool/negative or internally contradictory values become `CONFLICTING_DATA`. Stale/expired observations become `STALE_DATA`; future observations remain UNKNOWN. |
| F5 — Treasury Allocation & Scenario | 1.2.0 | User allocation model; CoinGecko market references; optional protocol-native checks | Numeric treasury fields reject booleans and economically invalid/non-finite values. Derived weights require complete positive valuation. CoinGecko freshness requires usable timestamp coverage for every requested asset; malformed/missing/future timestamps remain UNKNOWN. |

## Cross-engine contract rules

For newly executed live runs, the dispatcher enforces a canonical current engine version for each engine. Evidence inherits the parent engine contract version while preserving a more specific calculation version when needed. Historical persisted analyses are not rewritten.

Provider consensus is derived from evidence actually present. Zero provider evidence cannot claim `SINGLE_SOURCE`; one provider is `SINGLE_SOURCE`; multiple providers are `MULTI_SOURCE`; unresolved conflicts are `CONFLICTING`. `USER_INPUT_ONLY` is preserved only for intentionally modeled results without provider evidence.

Unresolved provider conflicts are first-class analysis state. Fresh live results carrying unresolved source conflicts are promoted from ordinary completed/partial states to `CONFLICTING_DATA`; stale and terminal unavailable states remain stronger gates where applicable.

## Engine-specific trust-boundary notes

**B1.** Standard ERC-20/ERC-721/ERC-1155 effects come only from raw logs whose standard topic signature and ABI layout validate. Receipt logs for mined transactions are observed evidence; Tenderly simulation logs are predicted. Non-canonical static calldata remains malformed rather than coerced. Verified-ABI dynamic `bytes`/`string` offsets must be 32-byte aligned, point outside the static head, contain complete bounded tail data, and use zero ABI padding. Supported static-element dynamic arrays inherit canonical element validation and a bounded item limit. Tuple, fixed-array and nested/composite dynamic layouts are not guessed.

**B2.** Input and RPC-resolved addresses/hashes validate before downstream use. Contract code must be valid hex and is observed at the same captured block referenced by its evidence. Approval-shaped calldata follows the same canonical address/bool boundary as B1.

**B3.** Current and prior snapshots are trust boundaries. All direct state forming a current snapshot—balance, code, optional supply and supplied Chainlink state—shares the captured block tag. Numeric state, thresholds and oracle timestamps must validate; malformed prior fields suppress only their affected comparison rather than manufacturing signals.

**B4.** Direct-chain and external-provider provenance is explicitly separated. The captured RPC block applies only to the direct native-balance snapshot. Etherscan history pages and Nansen/Arkham label responses without a provider-normalized observation timestamp or block are stored with `block_number=None` and `FreshnessStatus.UNKNOWN`; retrieval time is not converted into provider observation time. B4 aggregate freshness remains UNKNOWN whenever any such external evidence is consumed, while `direct_state=LIVE` and `direct_state_block_number` preserve the current chain snapshot. If no external evidence is consumed, direct-only aggregate freshness remains LIVE and unavailable external dimensions are explicit. Counterparty concentration remains descriptive interaction concentration—not ownership, maliciousness or economic exposure.

**B5.** Caller request plus LI.FI response form one trust boundary. Gas/fee collections must be explicit lists of valid non-negative finite USD rows; duration and included-step structure must validate. Contradictions retain evidence but discard route scoring.

**F1.** Explicit wallet/token reads are all-or-nothing. All direct holdings reads in one live snapshot share the captured block tag. For every declared ERC-20 contract, Rivexis first reads `decimals()` at that block and requires one canonical 32-byte ABI uint256 word; `balanceOf(address)` is held to the same ABI-width rule. Caller-supplied decimals must equal the observed on-chain decimals before any raw balance is scaled. Malformed, over-range or contradictory direct state prevents scoring instead of becoming zero or a plausible quantity. Direct JSON-RPC block/native quantities are bounded to uint256. Positive exposures still require complete positive finite prices before weights/concentration scoring, and market freshness requires credible timestamp coverage. Contract address, symbol and CoinGecko ID remain caller-supplied mapping metadata until independent discovery/identity evidence exists. Ordinary provider errors preserve the global redaction boundary rather than exposing raw internal mismatch details.

**F2.** Provider numerics reject Python/JSON booleans before float coercion. Boolean TVL in history, top-level TVL or `currentChainTvls` is malformed evidence; boolean timestamps cannot establish observation time. Audit counts/links cannot gain scoring trust through boolean truthiness, insecure references, contradictions or declaration-only claims.

**F3.** Explicit protocol-adapter requests remain authoritative when a position is returned. Generic modeled inputs reject booleans and non-finite values. Chainlink responses require exact five-word layout and positive finite prices, with both feed calls pinned to the captured block. Materially future or unusable timestamps remain UNKNOWN. CoinGecko reference freshness is based on its own usable observation timestamp rather than retrieval-time optimism.

**F4.** Strategy identity must resolve uniquely. Core and optional yield/volatility evidence cannot carry impossible provider semantics into the score; reward APY above headline APY is contradictory rather than clamped.

**F5.** Treasury numbers reject booleans before float coercion. Every requested CoinGecko asset must carry a usable observation timestamp before Rivexis asserts freshness; the oldest valid timestamp bounds aggregate freshness.

## External gates that remain non-code blockers

- Arkham remains license/terms-gated.
- Hypernative native screening remains customer-schema/contract gated where the exact authenticated request contract is not public/approved.
- Tenderly, Blockaid, Nansen, explorer and RPC behavior depends on deployment configuration and valid credentials/entitlements.
- Absence of those integrations must remain explicit provider-unavailable/partial/UNKNOWN-compatible evidence, not synthetic success.

## Latest repository evidence

- PR #26 — B1 canonical standard event effects — CI #271 (`35857083832`) PASS.
- PR #27 — F1 numeric/completeness integrity — CI #277 (`35861080306`) PASS.
- PR #28 — B4 token identity/counterparty-flow integrity — CI #282 (`35895021465`) PASS.
- PR #29 — B1 event parser ABI/input bounds — CI #287 (`35896050913`) PASS.
- PR #30 — B3 monitoring runtime integrity — CI #293 (`35897012617`) PASS.
- `6eecf44c921c6b31dddc265c2e62c60ac664a44e` — F2 audit-metadata trust boundary — CI #302 (`35916994577`) PASS.
- `eccb38a2db4523d9db1e0b14b667b8714f98d544` — B5 hardened route contract — CI #312 (`35922406982`) PASS.
- `f2f45e8ef0ec43230cc886554002878a90c56df8` — F4 optional yield-metric contradictions — CI #314 (`35922900454`) PASS.
- `e01fa907b58a8adbecfe604d5545f677d2e4a6d8` — F5 boolean/freshness hardening — CI #316 (`35923236659`) PASS.
- `c9baf68a045b194b9c8adb1557ac77091ae20b00` — F1 + B1 + B4 integrity campaign — CI #328 (`35928391144`) PASS.
- `c5f9b083229e61297375f0c02ded6cc1ecdbada9` — B2 + B3 + F3 + F2 bulk integrity campaign — CI #340 (`35931269784`) PASS.
- `2d0e2338e75114089e94c8623bb76fe7c8d79bf5` — certified B1 verified-ABI dynamic decoder lineage — CI #350 (`35933971343`) PASS; Pages #21 PASS.
- `61b728edf259ccafda256f2ab6f221e918e1f0ef` — B4 external indexed/entity evidence provenance + aggregate freshness — CI #353 (`35934430946`) PASS; Pages #24 (`35934430378`) PASS.
- `7a5f6aa284b35f8388915788ce1f444410f5ae4d` — F1 on-chain ERC-20 decimals/ABI-word integrity and redaction-compatible regressions — CI #358 (`35977258512`) PASS; Pages #29 (`35977258067`) PASS.

## Remaining Milestone F work

Deterministic integrity defects identified in these campaigns are regression-covered. Remaining work is primarily capability depth: deeper B1 internal/state/security semantics plus tuple/fixed/nested ABI decoding only where justified; approved independent B2/B3 security/threat evidence and continuous monitoring; B4 cross-chain/protocol-semantic attribution; F1 automatic/indexed discovery plus NFT/DeFi positions and independent token-identity mapping; independent B5 bridge-security/liquidity/incident evidence; and deeper F2/F4/F5 dependency/liquidity/governance/counterparty/strategy evidence. Credential/licensing/customer-contract gaps stay explicit and must not be replaced by synthetic success.
