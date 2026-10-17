# Bounded monitoring context integrity

18 October 2026. Branch `fix/bounded-monitor-context-20261018`; preserve the existing product, visual design and infrastructure.

## Verified defect and implementation

The previous monitor checked wallet/coverage only before its request. An in-flight reply could therefore overwrite a different inspected context. Tab hiding was observed only at the next two-minute interval; an absent current snapshot could also disable the Stop control while the old session remained active. Three browser cases reproduced the wallet/coverage/hidden failures against the previous production build; failing JSON/logs are preserved outside the repository.

The monitor now aborts immediately on wallet/coverage/sample changes, wallet provider context changes, active-workspace switches, hidden tabs and unmount. It checks identity and visibility again before applying results. Returned evidence must match the monitored wallet/coverage, be supported and observed rather than hypothetical/historical, have a recent valid observation time and numeric block, and not replace a newer inspection with an older block. A Stop action always remains available while active. Failures stop; retry/restart is explicit. Five-check/two-minute limits and existing quotas remain. Local abort does not promise that an already-started server read or quota claim was undone.

No financial formula, API/database/account setting, endpoint, paid dependency, CSS, layout, logo or brand change. No wallet signature, transaction submission, deletion or migration.

## Validation and honest intermediate failures

- Initial three regression cases failed on the old build, reproducing the actual defect rather than merely mirroring implementation.
- Initial20 monitoring cases and nine existing product cases passed (29 total, no retries/skips/flakes).
- Added active-workspace cancellation brought new coverage to21. The first45-case combined run passed44; the new case could not locate its selector using exact label matching. It now uses the visible combobox role/name already used by existing workspace tests. The behavior assertion remains intact; original failure is preserved separately.
- Final **45 cases passed**, zero failures/skips/flaky cases/retries, including all21 monitoring cases, product accessibility/responsiveness and prior late financial-response cases. Monitoring cases cover cancellation, context changes, navigation, visibility/resume, explicit stop/restart, five-check cap, timeout,429/503, mismatched/unsupported/sample/stale/future/missing-time/invalid-block/older-block responses.
- The existing five-check fixture now uses the same browser clock it advances; no expired mock snapshot is represented as fresh. No production data or clock is injected.
- Both production builds passed. One local JSX syntax error was corrected before a successful build. Vinext-generated route declarations and the local TypeScript incremental cache subsequently conflicted with Next's generated validator; official `next typegen`, clearing only the generated local compiler cache, and a fresh normal typecheck resolved it. Nonincremental and normal typechecks and frontend AST passed. Generated declarations/cache are excluded from the commit; no type assertion or gate was weakened.

## Release gates and continuation

Full source/PR/main CI now contains221 browser cases plus existing financial/API/security/PostgreSQL suites. Require successful CI/Worker validation, merge, native same-Worker deployment, exact public/authenticated build marker, real bounded monitoring/start-stop/context behavior and existing public browser gates. The current production remains PR87 until that successor is independently verified. Retain PR87 closeout and previous financial/recovery evidence with their dated scope. Update the root checkpoint and implementation PR with actual release identities/results after verification.

Owned sending-domain/DNS, native wallet protected steps, independent key/full-service recovery and institutional assurance remain separate resource gates. They do not justify stopping independent implementation work. Existing security findings and bounded provider/financial limitations remain explicit; added recurring service cost is $0.
