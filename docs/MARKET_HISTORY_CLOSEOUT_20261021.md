# Market-history production closeout — 21 October 2026

Subsequent normal owner sign-in and genuine authenticated workflow checks are complete; PR102 supersedes the then-pending login/correction gate. Earlier release evidence below remains dated5123c22. [Authenticated final closeout](AUTHENTICATED_WORKFLOW_REVIEW_20261021.md).

The existing [RIVEXIS website](https://rivexis-web.rudrasingh0718.workers.dev/) serves **5123c22bbb4c28a5e79708e88ecba0c9f69b2865**, merged [PR101](https://github.com/rudras777/rivexis/pull/101). Tested source **635eef96952eda5ccbbb985192ea49a0643376f2** and main have identical tree `371b9aec56f15fe6602ae67c2960f3b4d90629b7`. Existing Worker **f535fd05-2fd8-4e5a-95dc-81235e7e66da** has100% allocation; deployment **c269613d-35dc-47a2-9abb-930d2f69d2c5**, native build **96389e29-240b-4edc-a786-bdc9786317e3**, Ready in1m20s. Independent no-cache HTTP200, real browser DOM and Cloudflare rollout history agree.

## Completed correction

- Partial archives now receive validated recent oracle rounds independently for ETH/BTC. Actual update times and canonical observation-block provenance are retained. Conflicting same-round evidence is excluded explicitly; no missing points are fabricated.
- An initially unavailable feed can recover its history through existing visible-tab polling, at most every five minutes. Ordinary quote polls avoid repeated archive reads. Hidden/offline behavior, cancellation, deadlines and bounded backoff remain.
- Corrected the provenance description to distinguish oracle update times from observation-block timestamps.
- The unchanged security gate rejected newly reported Vite editor-launch advisories. Pinned official patched Vite8.3.5 and its required lockfile updates. No audit-rule weakening or additional exception. [Advisory](https://github.com/advisories/GHSA-587h-7wmj-h5pm), [official release](https://github.com/vitejs/vite/releases/tag/v8.3.5).
- Approved logo, colors, public layout/background, authentication, financial arithmetic, existing integrations and user data remain. Floating Pause remains absent; accessible motion preferences work. No backend deployment, migration, credential, service or plan change.

## Release checks

| Gate | Evidence | Result |
| --- | --- | --- |
| Source CI |39565667407|PASS;306 Chromium cases and standard financial/API/security/database gates|
| PR CI |39565674047|PASS;306 Chromium cases|
| Worker root/bundle dry runs |39565674103|PASS|
| Firefox/WebKit fixtures |39565674155|PASS at306 per engine; Firefox required one job rerun, detailed below|
| Main Worker |39568559896|PASS|
| Main CI |39568560026|PASS; all four jobs including306 Chromium cases|
| Actual public Chromium |task output `partial-history-public-chromium-20261021.json`|30PASS|
| Actual public Firefox/WebKit |39568824246|30PASS per engine; zero driver releases|

Final fixture/public browser cases have zero skipped/flaky/unexpected results or test retries. Counts per engine are repeated coverage, not unique scenarios. Suites include295 financial/auth,30 API-edge,33 market,28 audit-gate,10 sequence-RPC,12 API-client,18 wallet and30 navigation-driver cases; Deno, types, builds, Python tests/audit, secrets, invariants, migrations and disposable-database restore gates pass in source/PR CI. [Ten-scenario workflow mapping](WORKFLOW_SCENARIO_COVERAGE.md) retains exact supported scope.

Fresh actual PublicNode collector reads on deployed source advanced **26239751→26239753**. ETH/BTC quotes were fresh; each asset returned eight historical observations plus the latest quote, nine distinct chart timestamps, with eight archive errors retained and no conflicts. Initial55RPC/21HTTP/6970ms; ordinary follow-up13RPC/5HTTP/1241ms. Collector SHA256 `5b6bcebb66e87a0621faed1caa125323ae3c42daff6bf3943ab1f6ecc79abf4b`. Earlier reads returned different sparse coverage; no fixed24-hour history is promised. This is a direct operator/provider check, not a signed-in UI or sustained-availability certification.

## Retained failures and limitations

Before correction nine collector regressions failed; the browser recovery test remained at24 archive calls after feed recovery. Corrected33 market units and21 market browser cases pass. Initial sourcea8db411 was rejected for Vite High/Moderate findings; a separate source PostgreSQL install failed with ConnectionResetError104, while its same-head PR database job passed. Patched-head source/PR gates passed without an audit exception expansion.

The first patched-head Firefox run passed305/306 and failed the375px planner-action handoff URL assertion. WebKit passed306. No application/assertion change was made to disguise that failure. The single full unchanged-head Firefox job retest passed306; cause of the original click/navigation failure remains unestablished. It used one existing guarded bare-GET driver recovery on `/workspace`: complete200 document, zero pending requests/page errors/resource failures/server failures; all later assertions executed. Ten additional Chromium handoff cases (five per375/1440px) pass. Two local Firefox attempts failed all ten cases before browser launch with `spawn UNKNOWN`, including after an official reinstall; these provide no local functional result. Original logs and failed evidence remain preserved. Do not claim a flawless first run or zero job reruns/driver recoveries.

The remaining npm findings are seven High package entries from the single unpatched braces build-tool advisory GHSA-vfj7-8cjw-p6xm. Registry braces latest remains3.0.3. Existing Supabase pg_net/nonrelocatable-extension and Pro-only leaked-password-protection advisories remain disclosed. No forced downgrade, extension drop, new privilege or paid plan was applied.

## Readiness and resume

**The market/security release is live and publicly verified. Full institutional/public-launch sign-off remains blocked.** Fresh genuine authenticated Settings, financial and report checks require the pending normal owner website login; no reusable credential/session is available, and no reset/import/bypass is authorized by this handoff. Independent installed-wallet permission UX, owned sending-domain/inbox placement, separate recovery-key custody/second-machine/full-service restore/RPO/RTO and sustained field/load/security/operating assurance remain open. These are not replaced by fixtures or bounded public checks. See [readiness](PRODUCTION_READINESS.md).

Financial model source is unchanged from the prior verified release. Existing dated independent integer reconciliation and real supported Aave/Morpho simulations remain evidence within their stated limits; no fresh authenticated financial certification is claimed. Existing API36/reports4/alerts5 and PostgreSQL17.11.0.003 are retained. Previous verified Worker38e5925c / app1bd99ed0 and protected recovery archives remain rollback references; do not restore production data for this frontend-only release.

Added recurring infrastructure services: **$0**. Core features remain available without payment, subject to existing quotas and supported coverage. This is not an independent account-wide billing certification. No fabricated data, custody, private-key request, signing or automatic execution was introduced.

Next required action is normal sign-in in the prepared existing RIVEXIS browser tab, followed by fresh authenticated workflow verification. Continue a specifically enabled owner gate or a newly evidenced defect; do not repeat finished implementation/releases solely in response to generic continue prompts. Screenshots/raw artifacts remain outside Git; a structured manifest hashes the selected non-secret evidence and excludes all protected recovery/key files.
