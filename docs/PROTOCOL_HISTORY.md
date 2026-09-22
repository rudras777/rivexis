# Rivexis Protocol History and Configuration Review — P10

P10 extends the read-only protocol investigation surface beneath F2–F5. It does not create another engine and does not interpret a configuration change as malicious merely because it changed.

## API surfaces

- `POST /api/v1/protocol-history/timeline`
- `POST /api/v1/protocol-config/compare`
- `POST /api/v1/protocol-config/reviews`
- `GET /api/v1/protocol-config/reviews/{report_id}`
- `POST /api/v1/protocol-config/reviews/{report_id}/approve`
- `GET /api/v1/protocol-config/reviews/{report_id}/render?format=json|html|pdf`

All operational POST calls require authenticated workspace access. Approval additionally requires workspace manager authority.

## Historical log retrieval

Rivexis queries only the reviewed protocol-specific event catalog. The requested range is bounded by `RIVEXIS_PROTOCOL_HISTORY_MAX_BLOCKS` (50,000 by default), then split into chunks (`RIVEXIS_PROTOCOL_HISTORY_CHUNK_BLOCKS`, default 5,000). If a retryable provider range/limit failure survives the provider runtime retries, Rivexis reduces the chunk and retries rather than returning an empty timeline.

Chunk-boundary duplicates are de-duplicated by transaction/log identity. Logs marked `removed=true` are counted but excluded by default; `include_removed=true` is reserved for explicit reorg investigation.

Set `hydrate_timestamps=true` to resolve unique event blocks through `eth_getBlockByNumber`. Timestamp hydration is bounded by `RIVEXIS_PROTOCOL_HISTORY_TIMESTAMP_MAX_BLOCKS` (250 by default). If the event set exceeds that bound, Rivexis reports skipped hydration rather than issuing unbounded RPC reads.

## Event catalogs

Aave V3: borrowing, collateral configuration, active/frozen/paused state, reserve factor, borrow/supply caps, liquidation protocol fee/grace period and interest-rate strategy changes.

Compound III: governor/pause guardian/base-feed changes, supply/borrow kinks, target reserves, collateral price-feed/factor/supply-cap changes, plus Comet `PauseAction`.

Morpho Blue: owner/fee/IRM/LLTV/market creation plus official ChainlinkOracleV2 factory creation events when that factory is registered.

Absence of a normalized event is never proof that no governance activity occurred. Unknown/new events remain unsupported until reviewed.

## Configuration comparison and review artifacts

`/protocol-config/compare` executes the same adapter at `from_block` and `to_block`, recursively compares normalized metrics and assigns deterministic review priority: HIGH for liquidation/oracle/governance/pause/implementation-sensitive changes, MEDIUM for LTV/caps/rates/fees/IRM-type changes, and LOW for other normalized differences.

`/protocol-config/reviews` persists the comparison in the existing `reports` domain as a `protocol_configuration_review`. New reviews begin as `draft`. A workspace manager can explicitly approve the artifact; the approval stores actor/time and is audit logged. JSON, HTML and PDF renderers operate from the persisted review payload. Approval means the review artifact was accepted for the workspace record, not that the protocol change was safe.

## Deployment-source attestation

Registry records now include a source-attestation object. Reviewed Aave and Compound records are pinned to exact official GitHub blob SHAs observed in the release review. Morpho records sourced from official documentation are deliberately labeled `REVIEWED_CONTENT_SNAPSHOT` because the documentation surface does not expose the same immutable blob-revision contract.

`scripts/check_registry_attestations.py` validates the local attestation contract. `scripts/certify_registry_upstream.py` is an opt-in network-enabled release gate that re-fetches pinned GitHub files and official documentation; it fails if a pinned upstream blob changed or registered documentation addresses are no longer present.

## Workspace presentation

The Protocol History page renders event and configuration-change tables as the primary presentation, supports timestamp hydration, exposes the raw evidence payload behind a disclosure, and allows a configuration comparison to be saved, approved and rendered as PDF.

## Completeness boundary

Historical state still requires archive-capable RPC service. Provider-specific log retention/limits can still require staged ranges. Event chronology does not prove authorization or proposal legitimacy. Registry membership is release-time identity evidence, not proof that a deployment was official at every historical block.
