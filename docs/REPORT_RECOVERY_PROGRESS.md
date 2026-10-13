# Report failure recovery — resumable record

Active request: continue institutional readiness without redesign or financial-model changes. Audit found the report route conflated RPC/evidence outages with invalid inputs (422) and every persistence error with a full 20-report allowance (409).

The route now separates quota confirmation, fresh evidence validation, financial input calculation and persistence confirmation. Unsupported coverage and invalid model constraints return422; fresh evidence/provider failures return503; only the database's explicit report-limit error returns409. Unconfirmed saves return503 with instructions to check saved reports before retrying; there is no automatic retry of potentially committed writes. No success ID or receipt is returned on failure. Existing auth/CSRF, owner binding, quotas and financial calculations are retained.

Validation:36 report/account routing tests passed; final CI passed181 financial/account tests,30 retained Edge tests and133 browser tests. TypeScript, Deno checks, builds, secret scan and migration/invariant gates passed. New outage/recovery cases use explicit external-service fixtures with the actual handler/model and are not claims that production providers were forced offline. The API29 bundle was fetched and preserved outside the checkout at ../../outputs/report-recovery-api29-rollback.json before any API mutation.

Production database backup/upgrade remains blocked by the unavailable existing PostgreSQL connection. This improvement requires no schema changes, billing changes, new service or credential reset.

## Verified release — 13 October 2026 IST

PR70 merged as fdc5ce009d67e6f4899d10b0cb60d96116b7ee15. PR CI38392294940 and38392298348 passed; final main CI38392863329 and Worker bundle38392863299 passed. Existing Worker native build7df5fe58-390d-4d5a-9b59-3751bb05a11e deployed version prefix0607c845 at100% Ready (62seconds). Actual public build metadata independently matched the merge commit. No overlapping manual Worker deployment.

Existing Supabase rivexis-api version30 is ACTIVE. All21 runtime files were fetched after deployment and exactly matched the intended bundle. Bundle SHA256:77d2b1b02a5488ec11e664f660ab78d82931484587b694464f061bb1fad409e3. Existing custom cookie/CSRF/getUser authentication and verify_jwt=false configuration were preserved. Only index.ts changed among deployed files; financial kernels and data were preserved.

Final actual production suite passed13/13 in1.4minutes with zero skips/retries. Additional real report GET and two repeated POST requests without authentication each returned401, with no success ID or receipt. New signed-in outage behavior is certified by actual-handler fixtures and exact deployed-source reconciliation, not by forced live provider failures or fresh authenticated report writes in this turn. Earlier signed-in financial evidence remains valid for unchanged kernels but is not fresh certification of this new save route.

Durable evidence outside checkout: ../../outputs/report-recovery-final-production-results.json, ../../outputs/report-recovery-live-report-auth.json, ../../outputs/report-recovery-cloudflare.txt and ../../outputs/report-recovery-live.png. Complete production backup/restore, database maintenance, native wallet approval and remaining signup certification gates remain unresolved; unrestricted institutional launch is not certified.
