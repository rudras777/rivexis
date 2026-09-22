# Provider Architecture

Rivexis terminates provider-specific schemas at adapter/service boundaries and normalizes evidence before an engine consumes it. DEMO data is never selected automatically after a live-provider failure.

## Runtime controls

Implemented outbound HTTP/RPC clients use centralized controls:

- bounded retries with exponential backoff for retryable failures;
- per-workspace provider budgets;
- short-TTL process-local cache for suitable idempotent reads;
- concurrent same-key request coalescing;
- per-workspace circuit breakers;
- optional Redis control plane for cross-worker budget/circuit state;
- persistent workspace-scoped provider request/cost/latency telemetry;
- authenticated runtime/request/usage endpoints.

`GET /api/v1/providers/runtime`, `/runtime/requests`, and `/runtime/usage` expose operational evidence to authorized workspaces. Cross-worker response caching remains deliberately unimplemented until a serialization-safe shared-cache contract is chosen.

## P5 commercial/enriched providers

### Blockaid

The backend implements credentialed EVM address and transaction scanning using the provider's current EVM scan endpoints and `X-API-Key` authentication. Blockaid verdicts/features/simulation summaries are normalized as **external security intelligence**. Rivexis still runs its own direct-state and deterministic rules and does not turn a benign provider verdict into a safety guarantee.

### Nansen

Credentialed address-label evidence is normalized with provider provenance. Labels are analytical/enriched evidence, not direct chain state.

### Arkham

Arkham is additionally gated by `RIVEXIS_ARKHAM_LICENSE_APPROVED=true`. A credential alone does not enable the client. This forces deployment/legal review before Rivexis consumes Arkham intelligence in a potentially competing blockchain-intelligence product. Conflicts with Nansen are preserved and reduce confidence.

### Hypernative

The public/current product supports real-time monitoring, but customer-specific API/webhook schemas/signature contracts are configuration dependent. Rivexis therefore does not invent a provider-native signing algorithm. It supplies a customer-forwarding boundary at `POST /api/v1/integrations/hypernative/events`, protected by `HYPERNATIVE_WEBHOOK_SECRET`, monitor/workspace binding, a 64 KiB payload cap, attribution, and audit persistence. Its response explicitly states `provider_native_signature_verified=false`.

## Protocol-native evidence

F2–F5 can collect direct bytecode, explorer verification/proxy metadata and AggregatorV3-compatible oracle state for caller-declared protocol/admin/governance/dependency/oracle addresses. The declaration is retained as an assumption until a protocol-specific adapter independently proves the relationship.
