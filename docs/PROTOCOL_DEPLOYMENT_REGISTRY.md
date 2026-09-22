# Rivexis Protocol Deployment Registry — P10

Rivexis carries a versioned, read-only snapshot of reviewed official protocol deployment sources. Registry identity evidence is separate from direct on-chain state and never makes a protocol or market safe by itself.

Registry version: **2026-09-11**.

## Identity states

Each protocol-adapter result exposes `deployment_identity.status`:

- `VERIFIED` — the core address matches the selected bundled official-source record.
- `MISMATCH` — the caller explicitly supplied a different core address. Rivexis preserves the caller address and surfaces the conflict.
- `UNVERIFIED` — no unique registry record exists for the adapter/chain/market.

`GET /api/v1/protocol-deployments` returns both `registry_version` and a SHA-256 `registry_fingerprint` over the canonical bundled registry payload.

## Current records

| Adapter | Chain | Deployment / market | Identity source |
|---|---|---|---|
| Aave V3 | Ethereum (1) | Aave V3 Ethereum | Aave DAO generated address book |
| Aave V3 | Base (8453) | Aave V3 Base | Aave DAO generated address book |
| Compound III | Ethereum (1) | USDC Comet | Compound `comet` deployment repository |
| Compound III | Base (8453) | USDC Comet | Compound `comet` deployment repository |
| Morpho Blue | Ethereum (1) | Morpho Blue core | Morpho contract-address documentation |
| Morpho Blue | Base (8453) | Morpho Blue core | Morpho contract-address documentation |
| Morpho Blue | Arbitrum (42161) | Morpho Blue core | Morpho contract-address documentation |
| Morpho Blue | Optimism (10) | Morpho Blue core | Morpho contract-address documentation |

## Registry update governance

P10 retains an explicit plan/approve/verify workflow. A registry content change using the same `registry_version` is rejected.

Export/fingerprint the bundled registry:

```bash
PYTHONPATH=apps/api python scripts/registry_update_governance.py fingerprint
PYTHONPATH=apps/api python scripts/registry_update_governance.py export --out current-registry.json
```

Prepare a proposed update:

```bash
PYTHONPATH=apps/api python scripts/registry_update_governance.py plan \
  --proposed proposed-registry.json \
  --out registry-update-plan.json
```

A changed plan is emitted as `PENDING_APPROVAL`. It cannot pass the release guard until an explicit reviewer and approval ID are attached:

```bash
PYTHONPATH=apps/api python scripts/registry_update_governance.py approve \
  --plan registry-update-plan.json \
  --reviewer "<reviewer>" \
  --approval-id "<change-control-id>" \
  --out registry-update-approved.json

PYTHONPATH=apps/api python scripts/registry_update_governance.py verify \
  --plan registry-update-approved.json
```

Approval re-computes the base and proposed fingerprints. A stale or tampered plan fails verification.

This workflow intentionally does **not** auto-edit the Python registry or auto-approve upstream changes. Source review and release application remain explicit change-control actions.

## Historical distinction

`at_block` applies to chain-state reads. The bundled registry remains a release-time identity snapshot. P10 does not retroactively claim that a current registry record was official at an arbitrary historical block.

## Official source references

Aave:
- `https://github.com/aave-dao/aave-address-book/blob/main/src/AaveV3Ethereum.sol`
- `https://github.com/aave-dao/aave-address-book/blob/main/src/AaveV3Base.sol`

Compound III:
- `https://github.com/compound-finance/comet/tree/main/deployments/mainnet/usdc`
- `https://github.com/compound-finance/comet/tree/main/deployments/base/usdc`

Morpho:
- `https://docs.morpho.org/developers/contracts/addresses/`

The Rivexis release manifest and ZIP SHA-256 identify the exact bundled snapshot. They are not upstream protocol signatures.


## P10 upstream source attestations

Every registry item exposes `source_attestation`. Aave Ethereum/Base and Compound III Ethereum/Base USDC are pinned to exact reviewed official GitHub blob SHAs. The Morpho records are labeled `REVIEWED_CONTENT_SNAPSHOT` because the official documentation source is reviewed content rather than a pinned repository blob.

`check_registry_attestations.py` validates the local release contract. `certify_registry_upstream.py` is opt-in (`RIVEXIS_CERTIFY_REGISTRY_UPSTREAM=1`) and must run in a network-enabled release environment; it fails if a pinned GitHub file no longer has the reviewed blob SHA or documentation no longer contains registered addresses. A failure means "review upstream change", not "silently update Rivexis".
