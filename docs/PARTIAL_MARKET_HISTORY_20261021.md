# Partial oracle history and recovery — 21 October 2026

Initial candidate record retained below. **Final result:** PR101 is merged and deployed as `5123c22bbb4c28a5e79708e88ecba0c9f69b2865`, with all release gates and actual-public30 cases per engine passing. See [final closeout, retained failures and remaining owner gates](MARKET_HISTORY_CLOSEOUT_20261021.md). Earlier pending statements below describe the candidate stage.

## Reproduced defects and correction

The actual PublicNode collector returned fresh ETH/BTC quotes and fees but only two historical observations per asset. The existing recent-round fallback ran only when both archive arrays were empty. Partially available archives therefore suppressed useful, independently validated recent oracle rounds. The collector now supplements each incomplete asset independently with up to six actual previous rounds, preserving sampled observations, oracle update timestamps, canonical observation-block provenance and explicit archive gaps. Complete archives incur no supplemental calls. Same-round conflicting evidence is excluded with an error; this guard was tested with controlled responses, not observed in the real provider reads.

A separate browser regression reproduced a missing feed never recovering its history after other market data succeeded. The existing visible-tab quote poll now retries insufficient history at most every five minutes. Ordinary quote polling, hidden-tab suspension, cancellation, request deadlines and bounded backoff remain. No interpolation or guaranteed 24-hour coverage is introduced. The provenance wording now correctly distinguishes oracle update times from observation-block timestamps.

No financial arithmetic, authentication contract, schema, infrastructure, logo, color, public layout or animated background is changed. The bottom-right Pause button remains absent; accessible motion settings remain available. The subsequent exact-head security gate required the Vite patch described below.

## Evidence before release

- Collector regression before correction: 32 cases, nine failures. After correction and an additional conflict guard: all 33 pass, including twelve new cases covering partial/asymmetric archives, provider errors, phase boundaries, invalid/future rounds, deduplication, ordinary polling quotas and contradictory evidence.
- Browser missing-feed regression before correction: failed because archive calls remained at 24 after the feed recovered and the retry interval elapsed. After correction: all 21 market browser cases pass, zero skipped/flaky/unexpected cases and zero test retries.
- Next production build, TypeScript and frontend AST checks pass. Full exact-head CI, Worker dry runs and Firefox/WebKit gates remain required before merge.
- Final actual provider check: block 26236161 to 26236163; fresh ETH/BTC quotes, validated fee observations. Initial request: 55 RPC calls / 21 HTTP requests / 4494 ms. Six historical rounds per asset plus the current quote yield seven chart observations; ten archive errors remain explicit. The ordinary follow-up: 13 RPC calls / five HTTP requests / 1040 ms, with no archive request. No actual evidence conflicts occurred. These are bounded observations, not continuous availability or performance certification.
- Actual collector SHA256: `5b6bcebb66e87a0621faed1caa125323ae3c42daff6bf3943ab1f6ecc79abf4b`.

Raw task-output artifacts: `partial-history-before-20261021.log`, `partial-history-after-20261021.log`, `partial-history-recovery-before-20261021.json`, `partial-history-final-market-browser-20261021.json`, `partial-history-final-next-build-20261021.log`, `partial-history-final-types-20261021.log`, `partial-history-final-ast-20261021.log`, `market-provider-partial-before-20261021.json` and `market-provider-partial-verified-20261021.json`. Preserve failed evidence. These are outside Git; protected recovery material is excluded.

## Security gate follow-up

Initial source `a8db4119ae0e2982efeeb501082ab68465fd5a54` was rejected by the unchanged npm audit gate for Vite8.3.0: GHSA-587h-7wmj-h5pm (High) plus GHSA-698v-4r3x-3vcv and GHSA-r825-w8mm-5pxw (Moderate), relating to development editor launching. The [reviewed advisory](https://github.com/advisories/GHSA-587h-7wmj-h5pm) identifies Vite8.3.3 as patched; the official [Vite8.3.5 release](https://github.com/vitejs/vite/releases/tag/v8.3.5) is pinned, with its required Rolldown/OXC dependency updates recorded in the lockfile. The local audit now passes the existing narrow braces-only exception. No new advisory exception or audit-rule change was made. Existing unpatched GHSA-vfj7-8cjw-p6xm remains disclosed.

The initial source PostgreSQL job separately failed during pip installation with ConnectionResetError104; the same-head PR PostgreSQL job passed. Neither failure is concealed or represented as a successful initial gate. Latest patched-head gates must pass before merge.

## Readiness limits retained

Fresh genuine authenticated production workflow checks require the pending normal owner website sign-in. Do not reset passwords, import sessions or manufacture an identity to bypass it. This frontend-only release does not require a backend redeployment, migration, account change or new service. Existing API36/reports4/alerts5, PostgreSQL17.11.0.003 and the protected rollback/recovery references remain unchanged. Independent native-wallet permission UX, owned-domain inbox placement, recovery custody/full-service restore and institutional operating/security/load assurance remain open; see [readiness](PRODUCTION_READINESS.md) and the [prior verified release](AUTH_RECOVERY_CLOSEOUT_20261021.md).
