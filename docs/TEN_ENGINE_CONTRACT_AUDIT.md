# Rivexis Ten-Engine Contract Audit

Last updated: 2026-09-23

This audit distinguishes repository implementation gaps from external provider, credential, licensing and customer-contract gates. A missing commercial credential is not treated as a code defect; the engine must instead remain explicit about unavailable or partial evidence.

| Engine | Current live version | Grounding currently implemented | Safe live state / known gap |
|---|---:|---|---|
| B1 — Transaction Simulation | 1.2.0 | EVM RPC state/dry-run; Tenderly when configured; optional verified ABI lookup | `PARTIAL` while decoded internal calls, asset/approval effects and richer state diffs remain incomplete. Revert is a material blocker. |
| B2 — Transaction & Contract Security | 1.1.0 | EVM RPC bytecode/calldata rules; optional Etherscan; Blockaid when resolved | `PARTIAL`; absence of external threat intelligence is never treated as benign. Hypernative customer-only request schema stays explicitly gated rather than invented. |
| B3 — Threat & Monitoring | 1.1.0 | EVM RPC snapshots, balance/code change detection, optional Chainlink state and configured threat provider | Snapshot-based monitoring remains explicit; commercial/provider-native continuous threat coverage is not fabricated. |
| B4 — Entity & Fund Flow | 1.0.0 | Direct wallet state; optional Etherscan indexed history; optional Nansen; Arkham only when license-approved | `UNKNOWN ADDRESS` is preserved when attribution is absent. Unresolved external-label disagreement is now promoted to `CONFLICTING_DATA` with `provider_consensus=CONFLICTING` rather than being presented as an ordinary partial result. |
| B5 — Cross-Chain Route | 1.1.0 | LI.FI route quote normalization | `PARTIAL`; route-aggregator evidence is not an independent bridge-security assessment. Independent bridge/liquidity/incident evidence remains missing. |
| F1 — Portfolio & Exposure | 1.1.0 | CoinGecko market references; optional native-wallet EVM balances; user-declared manual positions | `PARTIAL`; ERC-20/NFT/DeFi position ingestion and deeper dependency evidence remain incomplete. |
| F2 — Protocol Risk | 1.2.0 | DefiLlama fundamentals plus optional direct protocol-native/adapter evidence | `PARTIAL`; independent exploit, governance, liquidity and security coverage remains explicit. Current-dispatch normalization fixes prior result/evidence version drift. |
| F3 — Position & Liquidation Risk | 1.3.0 | Protocol-specific adapter path where available; otherwise caller-modeled position with direct oracle evidence and optional CoinGecko/protocol-native checks | `PARTIAL`, `STALE_DATA` or `CONFLICTING_DATA` as applicable. Explicit `protocol_adapter + user/wallet` requests fail closed to `INSUFFICIENT_DATA`/`PROVIDER_UNAVAILABLE` unless an authoritative adapter position is actually returned; generic modeled fallback conclusions are discarded for that explicit request. |
| F4 — Yield & Strategy Risk | 1.2.0 | Attributed DefiLlama yield-pool evidence plus optional protocol-native evidence | `PARTIAL`; APY is never called safe and principal/security/oracle/withdrawal risks remain explicit. Current-dispatch normalization fixes prior default evidence version drift. |
| F5 — Treasury Allocation & Scenario | 1.2.0 | User allocation model; CoinGecko market references where requested; optional protocol-native checks | `PARTIAL`; dependency/correlation/liquidity/counterparty evidence remains explicit. Current-dispatch normalization corrects multi-provider consensus and evidence-version drift. |

## Cross-engine contract rules

For newly executed live runs, the dispatcher enforces a canonical current engine version for each engine. Evidence records inside the run inherit that parent engine version while preserving a more specific shared/provider calculation version when one exists. This avoids a result claiming one methodology generation while its evidence claims an obsolete/default parent engine generation.

Provider consensus is derived from evidence actually present in the result: zero provider evidence cannot claim `SINGLE_SOURCE`; one provider is `SINGLE_SOURCE`; multiple providers are `MULTI_SOURCE`; unresolved provider conflicts are `CONFLICTING`. `USER_INPUT_ONLY` is preserved only for intentionally modeled results with no provider evidence.

Unresolved provider conflicts are also first-class analysis state. A fresh live result carrying `SourceConflict` records is promoted from ordinary `COMPLETED`/`PARTIAL` to `CONFLICTING_DATA`; `STALE_DATA` and terminal unavailable/failure states are preserved when they are the stronger primary gate.

The normalization is intentionally limited to **new live dispatches**. Historical persisted analyses are not rewritten because their stored versions are part of the audit record.

For F3, an explicit protocol-adapter request is a trust-boundary instruction. If that adapter path does not return an authoritative position, Rivexis does not silently substitute the generic modeled-oracle conclusion. It returns an explicit unavailable/insufficient state with zero confidence and UNKNOWN severity. The generic modeled path remains available only when the caller does not require an authoritative adapter result.

## External gates that remain non-code blockers

- Arkham remains license/terms-gated.
- Hypernative native screening remains customer-schema/contract gated where the exact authenticated request contract is not public/approved.
- Tenderly, Blockaid, Nansen, explorer and RPC behavior depends on deployment configuration and valid credentials/entitlements.
- Absence of those integrations must remain explicit provider-unavailable/partial/UNKNOWN-compatible evidence, not synthetic success.

## Remaining Milestone F work

The repository-level cross-engine provenance/version/consensus/conflict-status contract and the explicit F3 adapter trust boundary are now covered. Remaining work is engine-depth completion and certification: close only those evidence/normalization gaps that can be implemented with approved sources, keep credential/licensing/customer-contract gaps explicit, and add per-engine regression evidence before advancing to monitoring/investigation/report completion.
