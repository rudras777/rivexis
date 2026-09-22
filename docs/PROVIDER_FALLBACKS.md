# Provider Fallbacks

Rivexis does not silently substitute DEMO data for failed live evidence.

Current P5 fallback policy:

- RPC: Alchemy → QuickNode → configured direct RPC. Selection probes `eth_chainId` and rejects chain mismatches.
- B1 simulation: Tenderly when configured → standards-based RPC dry-run (`eth_call` + `eth_estimateGas`) as a deliberately partial fallback. Optional Etherscan ABI and debug trace/state-diff evidence deepen the result when available.
- B2 security: Blockaid when configured contributes attributed external security evidence; direct RPC + deterministic Rivexis approval/calldata/contract-state rules remain independently calculated; Etherscan can add verification/proxy evidence. Hypernative customer-specific request contracts are not guessed.
- B3 threat monitoring: direct RPC snapshot/change detection → optional Chainlink-compatible feed state → optional Blockaid point-in-time screening. Customer-configured Hypernative push events may enter through the Rivexis-owned shared-secret webhook boundary; provider-native signature verification remains a staging/customer-contract requirement.
- B4 entity/fund flow: direct RPC + optional Etherscan history → Nansen labels when configured → Arkham only when credentials **and** explicit license approval are configured. Conflicting identities are exposed as `CONFLICTING EXTERNAL LABELS`; no identity is selected silently.
- B5 routing: LI.FI quote evidence. Missing independent bridge/security evidence keeps the engine partial.
- F1 portfolio: CoinGecko references plus supplied/manual positions and optional direct wallet state.
- F2 protocol: DeFiLlama fundamentals plus optional caller-declared protocol-native contract/oracle/governance/admin/dependency evidence. Caller declarations never prove role authority by themselves.
- F3 position/liquidation: supplied position terms + direct AggregatorV3-compatible feed state + optional CoinGecko reference + optional declared protocol-native evidence.
- F4 yield: DeFiLlama Yields plus optional declared protocol-native evidence; APY never becomes a safety conclusion.
- F5 treasury: CoinGecko references + Rivexis concentration/stress rules + optional multiple declared protocol-native dependency checks.

When required live evidence is unavailable Rivexis returns `PROVIDER_UNAVAILABLE`, `INSUFFICIENT_DATA`, `PARTIAL`, `STALE_DATA`, `CONFLICTING_DATA`, or ultimately `UNKNOWN` as appropriate. DEMO fallback requires explicit caller opt-in.
