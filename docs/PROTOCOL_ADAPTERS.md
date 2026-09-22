# Rivexis Protocol-Native Adapters — P10

P10 retains and extends the P9 read-only protocol adapters beneath F2/F3/F4/F5 with official deployment identity, richer protocol configuration discovery and historical-block replay. These adapters do not create a new Rivexis engine and never sign or send transactions.

## Common rules

- Direct state is read with EVM `eth_call` through Rivexis's existing RPC fallback/runtime controls.
- `GET /api/v1/protocol-adapters` returns the machine-readable adapter contract.
- `GET /api/v1/protocol-deployments` returns the versioned official deployment registry snapshot.
- Registered core addresses can be auto-filled; an explicit caller address is never overwritten.
- Every result exposes `deployment_identity.status = VERIFIED | MISMATCH | UNVERIFIED`.
- Optional `at_block` performs historical reads through an archive-capable RPC.
- Unsupported/reverting getters remain `missing_data`; Rivexis does not synthesize values.
- Direct protocol state supplements security/liquidity/governance/dependency evidence. It is not a safety guarantee.

## Aave V3

Minimum registered-chain input:

```json
{
  "protocol_adapter": "aave_v3",
  "chain": "ethereum",
  "asset_address": "0x...",
  "user_address": "0x... optional",
  "at_block": "0x... optional"
}
```

For registered Ethereum/Base deployments Rivexis can auto-fill the Pool Data Provider, Pool, Aave Oracle and Pool Addresses Provider. On unregistered chains the caller must provide the relevant addresses.

Reads include:

- `getReserveConfigurationData(address)`
- `getReserveCaps(address)`
- `getDebtCeiling(address)`
- `getPaused(address)`
- `getSiloedBorrowing(address)`
- `getLiquidationProtocolFee(address)`
- `getReserveEModeCategory(address)`
- `getInterestRateStrategyAddress(address)` on the current Aave Protocol Data Provider surface
- Aave Oracle `getSourceOfAsset(address)`
- legacy-compatible `getEModeCategoryData(uint8)` when an eMode category is active; the deprecated `priceSource` field is never treated as current authoritative oracle evidence
- `getUserAccountData(address)` when a user is supplied

The current Aave V3.4 architecture uses a Pool-level shared `RESERVE_INTEREST_RATE_STRATEGY`; Rivexis records the returned strategy as protocol state instead of assuming a per-reserve strategy.

## Compound III / Comet

Minimum registered-market input:

```json
{
  "protocol_adapter": "compound_v3",
  "chain": "ethereum",
  "compound_market": "usdc",
  "collateral_asset": "0x...",
  "user_address": "0x... optional"
}
```

P10 currently bundles official USDC Comet identity records for Ethereum and Base. Explicit `comet_address` remains supported.

Reads include:

- `getAssetInfoByAddress(address)`
- protocol `getPrice(address)` for the returned collateral feed
- `governor()` and `pauseGuardian()`
- `baseToken()` and `baseTokenPriceFeed()`
- `extensionDelegate()`
- `numAssets()`, `getUtilization()`, `targetReserves()`
- supply/transfer/withdraw/absorb/buy pause state
- `isLiquidatable(address)`, `isBorrowCollateralized(address)`, `borrowBalanceOf(address)` and `collateralBalanceOf(address,address)` for a supplied user

Registry governor/pause-guardian values are comparison evidence only. If current on-chain state differs, Rivexis surfaces a governance/history review warning rather than silently forcing the snapshot value.

## Morpho Blue

Input:

```json
{
  "protocol_adapter": "morpho_blue",
  "chain": "ethereum",
  "morpho_market_id": "0x...bytes32",
  "user_address": "0x... optional"
}
```

P10 can auto-fill the official Morpho core on Ethereum, Base, Arbitrum and Optimism. It also carries the official Adaptive Curve IRM and ChainlinkOracleV2 factory references for classification.

Reads include:

- `idToMarketParams(bytes32)` immutable loan/collateral/oracle/IRM/LLTV parameters
- `market(bytes32)` supply/borrow/utilization/fee state
- oracle `price()`
- best-effort Morpho ChainlinkOracleV2 composition getters: base/quote vaults, base/quote feed 1/2, conversion samples and scale factor
- `position(bytes32,address)` and derived health factor when a user is supplied
- `Morpho.isIrmEnabled(address)` IRM enablement provenance
- `MorphoChainlinkOracleV2Factory.isMorphoChainlinkOracleV2(address)` official-factory provenance when a factory is registered
- `AdaptiveCurveIrm.rateAtTarget(bytes32)` for a market using the official registered Adaptive Curve IRM

`irm_classification` distinguishes the official chain Adaptive Curve IRM reference from a custom/other IRM. P10 also records whether Morpho core reports that IRM enabled, whether the registered oracle factory recognizes the market oracle, and the Adaptive Curve `rateAtTarget` state when applicable. A custom IRM is not automatically classified malicious; it remains implementation/dependency evidence requiring review.

## Historical replay

Set `at_block` to an integer or hex block number. Rivexis applies that block tag consistently to protocol-adapter calls and generic protocol-native contract/oracle reads. Outputs include `read_block_number` and `block_tag`.

Historical replay is useful for configuration-change investigations and before/after risk comparisons. It requires an RPC capable of serving the requested historical state.

## Staging certification

Run:

```bash
PYTHONPATH=apps/api python scripts/certify_protocol_adapters.py
```

The certification script can now rely on the official registry for core addresses. Typical target variables are:

- Aave: `RIVEXIS_CERT_AAVE_CHAIN`, `RIVEXIS_CERT_AAVE_ASSET`; optional explicit data provider/pool/user.
- Compound: `RIVEXIS_CERT_COMPOUND_CHAIN`, `RIVEXIS_CERT_COMPOUND_MARKET`, `RIVEXIS_CERT_COMPOUND_ASSET`; optional explicit Comet/user.
- Morpho: `RIVEXIS_CERT_MORPHO_CHAIN`, `RIVEXIS_CERT_MORPHO_MARKET_ID`; optional explicit core/user.
- Any adapter: `RIVEXIS_CERT_AT_BLOCK` for archive-block certification.

Set `RIVEXIS_REQUIRE_PROTOCOL_ADAPTER_CERTIFICATION=true` to fail a certification environment when no configured target succeeds.

## P10 history and review

Use `POST /api/v1/protocol-history/timeline` and `POST /api/v1/protocol-config/compare` for reviewed historical event normalization and two-block state comparison. See `docs/PROTOCOL_HISTORY.md` for event catalogs, block-range limits and materiality semantics.
