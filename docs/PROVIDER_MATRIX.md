# Provider / Engine Matrix

| Engine | Implemented non-demo evidence path | Additional institutional evidence still required |
|---|---|---|
| B1 | Tenderly simulation when configured; RPC `eth_call`/`eth_estimateGas`; standard selector decoding; verified ABI lookup/decoding; optional `debug_traceCall`/prestate normalization | broader trace-provider coverage, fork simulation and richer asset/state normalization |
| B2 | direct RPC contract state; deterministic calldata/approval rules; optional Etherscan verification; credentialed Blockaid EVM address/transaction scanning | Hypernative customer-specific security API contract where licensed/configured; broader exploit-intelligence cross-validation |
| B3 | direct RPC snapshot/change detection; optional Chainlink-compatible feed state; Blockaid point-in-time screening; Rivexis-secret-authenticated Hypernative forwarding ingress | provider-native Hypernative signature/contract certification, continuous streaming/WebSocket/SSE orchestration and real staging delivery/SLO certification |
| B4 | direct RPC wallet/contract state; optional Etherscan history; credentialed Nansen labels; license-gated Arkham intelligence with explicit conflicts | enriched clustering/behavioral depth and commercial-license/staging certification |
| B5 | LI.FI quote normalization | independent route/bridge security, liquidity/dependency cross-validation |
| F1 | CoinGecko market references; manual positions; optional direct wallet balance context | protocol positions, liabilities, exchange imports, counterparty/dependency depth |
| F2 | DeFiLlama fundamentals + generic protocol-native evidence + P10 registry-aware Aave V3 / Compound III / Morpho Blue direct-state adapters | deeper governance/implementation dependency proof; external risk providers |
| F3 | P10 registry-aware Aave/Compound/Morpho native position/liquidation state when supplied; otherwise direct Chainlink-compatible feed + deterministic model | broader protocol coverage; deeper liquidity/liquidation execution inputs |
| F4 | DefiLlama Yields + generic native evidence + P10 protocol adapters where applicable | strategy/vault-specific execution/dependency adapters and sustainability calibration |
| F5 | CoinGecko references + Rivexis concentration/stress calculations + optional multiple P10 registry-aware protocol-native adapter checks | institutional counterparty/dependency enrichment and calibrated scenario libraries |

The matrix is evidence-oriented. External provider conclusions remain attributed evidence and never become the Rivexis final decision automatically. Caller-declared protocol roles are explicitly marked as assumptions until independently proven by a protocol-specific adapter.
