# Report failure recovery — resumable record

Active request: continue institutional readiness without redesign or financial-model changes. Audit found the report route conflated RPC/evidence outages with invalid inputs (422) and every persistence error with a full 20-report allowance (409).

The route now separates quota confirmation, fresh evidence validation, financial input calculation and persistence confirmation. Unsupported coverage and invalid model constraints return422; fresh evidence/provider failures return503; only the database's explicit report-limit error returns409. Unconfirmed saves return503 with instructions to check saved reports before retrying; there is no automatic retry of potentially committed writes. No success ID or receipt is returned on failure. Existing auth/CSRF, owner binding, quotas and financial calculations are retained.

Local validation:35 report/account routing tests,180 financial/account tests and30 retained Edge tests passed; TypeScript passed. New outage/recovery cases use explicit external-service fixtures with the actual handler/model and are not claims that production providers were forced offline. Deployment pending. The API29 bundle was fetched and preserved outside the checkout at ../../outputs/report-recovery-api29-rollback.json before any API mutation.

Production database backup/upgrade remains blocked by the unavailable existing PostgreSQL connection. This improvement requires no schema changes, billing changes, new service or credential reset.
