# Data Provider Strategy

Rivexis separates blockchain/infrastructure evidence from crypto-finance/DeFi evidence and keeps every provider behind an adapter boundary.

## P5 implemented external surfaces

Blockchain/security/entity: direct RPC, Etherscan, Tenderly, LI.FI, Blockaid, Nansen and license-gated Arkham; Hypernative is represented through a safe customer-forwarding ingress plus an explicit customer-schema/provider-native-signature certification gap.

Finance/DeFi: CoinGecko, DeFiLlama fundamentals, DeFiLlama Yields and direct AggregatorV3-compatible oracle state. F2–F5 can additionally inspect caller-declared protocol/admin/governance/dependency contracts through direct RPC and Etherscan verification/proxy metadata.

## Evidence rules

- Direct chain state has higher authority for direct-state questions than enriched analytics.
- External provider labels/security verdicts remain attributed evidence.
- A benign security-provider verdict is not a Rivexis safety guarantee.
- Nansen/Arkham identity disagreement is preserved as a source conflict.
- Arkham cannot be enabled by credentials alone; deployment licensing approval is required.
- Caller-declared DeFi roles remain assumptions until a protocol-specific adapter proves the mapping.
- Missing commercial evidence produces partial/unknown outcomes rather than DEMO fallback.
