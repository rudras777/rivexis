# Data Architecture

External provider schemas terminate at adapter boundaries. Rivexis validates and normalizes provider payloads into canonical models before engines consume them.

Canonical model families include chains, assets/tokens, blocks, transactions/traces/transfers, contracts, wallets/entities/labels, protocols/pools/vaults/markets, bridges/routes, prices/oracles, portfolios/positions, yield opportunities, security/threat/liquidity/protocol/market/risk signals and EvidenceRecord.

Important values should preserve provider, provider request/method, observed and retrieved timestamps, block reference where applicable, normalized value, calculation/engine version, confidence, freshness and license classification. Material provider disagreement is represented explicitly as SourceConflict.
