# Staging and Release Certification — P37

P37 preserves P36's source-bound nine-runner certification campaign, deterministic dependency-runner correction, and PostgreSQL standalone service-identity contract. P37 fixes a proven P36 orchestration defect that could classify an overall provider **SKIP** as **PASS** when provider-specific diagnostics appeared before the final SKIP line. No external gate is promoted without real runner evidence.

## P37 provider-outcome classification correction

`certify_staging_suite.py` now classifies child-process results fail-closed: any nonzero exit is FAIL; a leading or final non-empty overall `SKIP ...` marker is SKIP; otherwise a zero exit is PASS. This preserves legitimate mixed-provider runs where one optional provider skips but another succeeds and the provider certifier emits a final overall PASS.

## Execution manifest

Create/verify the canonical root manifest with:

```bash
PYTHONPATH=apps/api python scripts/create_certification_execution_manifest.py
PYTHONPATH=apps/api python scripts/verify_certification_execution_manifest.py certification-execution-manifest.json
```

The sealed manifest binds release `P37`, the exact source-tree fingerprint, canonical report paths, all required gates and these specialized production profiles: `local`, `postgres-rls`, `postgres-dr`, `redis`, `registry`, `providers`, `protocol`, `history`, `dependencies`. The diagnostic `full` profile is not sufficient for production coverage.


## P37 dependency-runner correction

P37 fixes a proven P35 release-certification deadlock. P35 required a root `package-lock.json` for frontend dependency gates but did not ship one, while its execution manifest fingerprint treated any newly generated lockfile as source drift. P37 classifies only the repository-root `package-lock.json` as a runner-generated certification artifact, keeps the source `package.json` manifests fingerprint-bound, exact-pins the previously floating `@types/node`, `@types/react` and `@types/react-dom` direct dev dependencies, and requires the generated lockfile to match the exact root/workspace package manifests and records its SHA-256/version in dependency evidence.

On the dedicated dependency runner, verify the clean P37 manifest first, then resolve the dependency tree with `npm install --package-lock-only --ignore-scripts`, install with `npm ci`, install the approved Playwright Chromium runtime, and install the Python dev extras. The generated lockfile may exist before the `dependencies` profile is run without invalidating the P37 application-source fingerprint; a malformed lockfile is a hard dependency-gate FAIL.

## Gate matrix

| Profile | Gate | Required prerequisite names |
|---|---|---|
| local | `otlp-local` | none |
| postgres-rls | `postgres-rls` | `RIVEXIS_RLS_ADMIN_DATABASE_URL`, `RIVEXIS_RLS_APP_DATABASE_URL`, `RIVEXIS_RLS_WORKER_DATABASE_URL` |
| postgres-dr | `postgres-dr` | `RIVEXIS_BACKUP_SOURCE_DATABASE_URL`, `RIVEXIS_BACKUP_RESTORE_DATABASE_URL`, `RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY` |
| redis | `redis-distributed` | `REDIS_URL` |
| registry | `registry-upstream` | `RIVEXIS_CERTIFY_REGISTRY_UPSTREAM` plus network access |
| providers | `live-providers` | `RIVEXIS_CERTIFY_LIVE_PROVIDERS` plus configured licensed credentials/target |
| protocol | `protocol-adapters` | at least one concrete target: `RIVEXIS_CERT_AAVE_ASSET`, `RIVEXIS_CERT_COMPOUND_ASSET`, or `RIVEXIS_CERT_MORPHO_MARKET_ID` |
| history | `archive-history` | `RIVEXIS_CERT_HISTORY_ADAPTER` plus archive-capable RPC/range |
| dependencies | `dependency-gates` | resolved Python and frontend/browser dependency toolchain |

Each report contains the complete ordered nine-gate matrix. Missing prerequisites remain `SKIP`; they never become synthetic `PASS`. Any authorized `FAIL` remains `FAIL`. Non-SKIP evidence is accepted only from an authorized runner profile bound to the same source tree and execution campaign.

## Runner execution

Use the canonical command emitted by `python scripts/certification_plan.py`. Example:

```bash
RIVEXIS_CERT_RUNNER_PROFILE=redis \
RIVEXIS_STAGING_CERT_REPORT=certification-reports/redis.json \
RIVEXIS_CERT_EXECUTION_MANIFEST=certification-execution-manifest.json \
PYTHONPATH=apps/api python scripts/certify_staging_suite.py
```

Verify a report:

```bash
PYTHONPATH=apps/api python scripts/verify_staging_evidence.py certification-reports/redis.json \
  --manifest certification-execution-manifest.json --profile redis
```

## Aggregate and require completion

```bash
PYTHONPATH=apps/api python scripts/certify_release_bundle.py \
  --manifest certification-execution-manifest.json \
  --report certification-reports/local.json \
  --report certification-reports/postgres-rls.json \
  --report certification-reports/postgres-dr.json \
  --report certification-reports/redis.json \
  --report certification-reports/registry.json \
  --report certification-reports/providers.json \
  --report certification-reports/protocol.json \
  --report certification-reports/history.json \
  --report certification-reports/dependencies.json

PYTHONPATH=apps/api python scripts/verify_release_bundle.py release-certification-bundle.json \
  --manifest certification-execution-manifest.json --require-complete
```

`certified=true` requires every gate to be PASS and all nine specialized runner profiles to have supplied accepted evidence.

## Destructive DR rule

The `postgres-dr` gate is intentionally destructive on its restore target. Source and restore URLs must be distinct, the restore target must be disposable/approved, and `RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY=true` must be explicit. The script verifies the restored 53-table application schema, hashes the dump, measures dump/restore/RTO and can enforce `RIVEXIS_BACKUP_MAX_RTO_SECONDS`.

## Rudra ownership boundary

For Rudra's Rivexis deployment, only Rudra/Rivexis-owned targets may be used as certification evidence. An unavailable Rudra-owned target remains unavailable/SKIP; infrastructure belonging to another account or project is not a substitute.

## Inherited P35 security-gate additions

P35 extends existing production evidence rather than upgrading unavailable infrastructure to PASS. It preserves the P34 PostgreSQL organization-revocation scenario and adds a Redis cross-client global authentication-budget scenario so rotating identifiers cannot bypass all shared pre-scrypt protection. The PostgreSQL RLS profile now verifies that removing an organization member revokes access to an organization workspace even when that user originally created it, including downstream tenant data. The Redis profile now exercises the distributed login-attempt budget across independent clients in addition to distributed provider budgets/circuit state. Protocol-gate activation is driven by the concrete Aave/Compound/Morpho target variables consumed by the certifier.

The dependency/browser profile remains SKIP unless Ruff, pip-audit, a resolved npm dependency tree, Next.js build dependencies and Playwright browser runtime are actually present.

## Inherited P35 OTLP privacy certification

The local OTLP gate now verifies that Rivexis exports exception class/type without raw exception messages or stack traces and that sentinel secret-bearing exception text is absent from the emitted protobuf. Production collector transport policy is validated separately at runtime.
