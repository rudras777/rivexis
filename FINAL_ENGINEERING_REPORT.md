# Rivexis Final Engineering Report — P37

Build: **P37 certification-outcome-integrity correction over P36**
API/package version: **3.4.3**

## Why P37 exists

P36 fixed the dependency-certification deadlock inherited from P35, but adversarial release-runner testing exposed a separate orchestration defect: a multi-line provider certification could return exit code `0`, print a provider-specific SKIP diagnostic first, print the overall `SKIP live provider certification...` result last, and still be recorded by `certify_staging_suite.py` as **PASS** because the orchestrator only recognized SKIP when the entire output began with `SKIP `.

P37 corrects only that certification-result-classification defect. It does not change the Rivexis product definition, exactly-10-engine architecture, API behavior, 53-table logical schema, RLS policy semantics, provider-client behavior, protocol logic, alerting logic, signing schemas or anti-rollback lineage design.

## P37 corrections

- Child certification process results are now classified by exit code plus both the leading and final non-empty overall status marker.
- A final `SKIP ...` can no longer be promoted to PASS merely because provider-specific diagnostics preceded it.
- A partial provider skip followed by a real overall provider PASS remains PASS, avoiding an over-broad downgrade.
- Regression tests cover the exact P36 false-PASS reproduction, the partial-provider PASS case, dependency SKIP handling and nonzero FAIL handling.
- P37 preserves the P36 deterministic dependency-runner correction, exact frontend dependency pins and lockfile evidence binding unchanged.


## Verification status

- Backend regression: **261/261 PASS**.
- Exactly 10 engines: **PASS**.
- Alembic/schema parity: **53/53 tables PASS**.
- Schema contract: **511 columns / 102 FK edges / 20 unique constraints / 11 named indexes PASS**.
- Registry governance and pinned attestation contract: **PASS**.
- OTLP/W3C protobuf and exception-payload redaction: **PASS**.
- Retention, SQLite backup/restore procedure, secret scan and frontend AST/browser harness: **PASS**.
- Exact P36 false-PASS provider reproduction under P37: **SKIP as designed**, not PASS.
- Nine-profile release campaign: **1 PASS / 0 FAIL / 8 SKIP**, `certified=false`; integrity verification passes and strict completeness fails as designed.

External PostgreSQL RLS/DR, Redis, live-provider, protocol/archive-RPC, registry-network and resolved dependency/browser evidence still require genuine Rudra-controlled release infrastructure.
