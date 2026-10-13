# Backup command credential safeguards — 13 October 2026 IST

PR69 merged as `ad683c8d2623b34b2410741d7120ac466430d203`. Both legacy PostgreSQL drills now keep connection URLs out of subprocess arguments. They use libpq child environment variables, remove inherited backup URLs, suppress interactive password prompts, bound each command to 900 seconds and redact tool failures. Credentials still exist in the child environment; this is not encrypted credential storage. Existing disposable-target guards remain enforced. No production database, credential, user, financial model, UI or billing change was made.

Eight regression tests cover 32 scenarios, including source/target aliases, routing overrides, credential decoding and preservation, failures/timeouts and both actual entry points with mocked archives. CI additionally dumps/restores the actual ephemeral PostgreSQL fixture using PostgreSQL 17 clients and compares source/restored application table counts. The obsolete fixed 55-table comparison is removed. This is a procedural test, not production backup certification or full data reconciliation.

## Verified evidence

- PR CI runs `38389919557` and `38389926334`: all jobs succeeded; each passed 133 browser tests, eight guard tests and a real 56-table PostgreSQL fixture restore.
- Final main CI `38390446962` and Worker bundle `38390447081` succeeded on the merged release commit.
- Real drill in run38389919557: client17.11, dump0.10s, restore0.32s, total0.46s, 56 source/restored tables. Run38389926334 repeated it successfully in1.18s. Logs retained outside the checkout at `../../outputs/backup-secret-handling-real-ci-drill.log`.
- Initial fixture failures were retained and corrected: preinstalled PostgreSQL16 client versus17 server, then absence of client17 in Ubuntu's default repository. Final CI uses the official signed PostgreSQL package repository on disposable runners only. Reference: https://www.postgresql.org/download/linux/ubuntu/ .
- Existing Worker native build `a6fafc4c-9a61-4bc2-84be-1222a83231a6`: version prefix `4b6d499c`, 100% Ready, 42seconds. Its source commit and actual public HTML build metadata independently matched `ad683c8`. Same production URL and account retained; no overlapping manual deployment.
- Final actual production suite: 13/13 passed in1.5minutes, no retries. Covers exact deployed build, public auth/API gates, recovery/confirmation credential scrubbing, mobile accessibility, navigation and background motion. It does not freshly certify signed-in financial or native wallet permission flows.
- Evidence: `../../outputs/backup-secret-handling-final-production-results.json`, `../../outputs/backup-secret-handling-cloudflare.txt`, `../../outputs/backup-secret-handling-live.png`.

## Remaining prerequisite

Complete production backup, verified restore and authorized PostgreSQL upgrade are still blocked by missing usable PostgreSQL connection access. The existing connection's local file, environment variable or secure-store location was requested; no secret was requested in chat and no credential reset was attempted. Do not substitute the passing CI fixture for this prerequisite. Existing pg_net and free-plan password-protection advisories and native wallet/signup certification limits remain as documented in the launch records. Unrestricted public launch is not certified.
