# RIVEXIS security and navigation release — 23 October 2026

The selected workspace menu clipping and hover/keyboard dismissal defects are corrected on the existing production website. PR105 also updates Next.js to16.4.2 after the security gate detected newly reported advisories. Branding, public landing layout, animated background, financial models, authentication, APIs, Supabase data/schema, Brevo and hosting identity are preserved. Workspace programmatic page alignment now completes immediately; the public page retains smooth scrolling. There is no new recurring service or paid plan.

All seven exact-head source/PR/main/Worker/fixture/public release gates pass. The [structured manifest](evidence/next-security-release-20261023.json) records 54 evidence hashes and every gate URL. Source/PR/main Chromium326, fixture Firefox326/WebKit326 and actual-public30 per engine pass, with zero final skipped/flaky/unexpected cases or driver recoveries. Earlier navigation and financial receipts remain dated, with original failures retained.

## Exact production identity

| Item | Verified value |
|---|---|
| Existing website | https://rivexis-web.rudrasingh0718.workers.dev/ |
| Repository / release | [rudras777/rivexis, PR105](https://github.com/rudras777/rivexis/pull/105) |
| Tested source | `2b1cd762d2cbccf34bba913e4b2967bc9c1741a8` |
| Production merge | `37d03fd3c539085538cbbca48ea2f29b91a581fb` |
| Identical source/merge tree | `1be7166500aebc0b3df9457bd15f9efb7d9b071c` |
| Existing Worker | `rivexis-web` |
| Active Worker version | `c63e2bcd-64e0-44b8-914a-41e2103d3484`,100% allocation |
| Deployment | `d3a58268-88c5-4f7a-8ec7-ef55478bd033`,22October18:33:59UTC |
| Cloudflare native build | `ba158a6e-9d3f-4705-ab21-8ec0592353c5`,Ready |
| Backend / database | Existing API36/reports4/alerts5/dispatch3/relay3; project `ivszvufdonfgwjpfgwii`,17.11.0.003; no new migration/deployment |

Actual public HTML commit, health response, guest-session response, genuine signed-in DOM and native rollout identify the same production release. The native dashboard has no useful runtime-chart samples; that is not evidence of zero runtime errors or an availability SLA.

## Security correction and honest findings

Documentation CI[39824683538](https://github.com/rudras777/rivexis/actions/runs/39824683538) first observed the new critical finding at22October17:40:59UTC, after the navigation release gates had passed. The audit gate refused it. Official advisories identify16.4.1 as patched for [image-optimization RCE](https://github.com/advisories/GHSA-2464-fhr4-w9xw) and [App Router Server Actions denial of service](https://github.com/advisories/GHSA-p3m5-59mp-jv5r); the same-major [16.4.2 release](https://github.com/vercel/next.js/releases/tag/v16.4.2) is installed. Affected package ranges do not establish production exploitability or compromise. No exploit payload was sent.

Only Next.js and its matching env/SWC lock entries were updated. Node24.17 and React19.3 remain compatible. The fresh23October audit reports zero critical findings and no Next.js entry. Seven package entries still reach the known [unpatched Braces advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm). The original gate and its narrow Braces exception are unchanged; all28 audit-policy cases pass. No new waiver, forced override or weakened assertion was introduced.

Sharp0.35.5 was already installed through the existing root override, including the vendor's stated RCE workaround version. This does not prove complete non-applicability. `npm ls` reports Miniflare's exact0.35.4 constraint against that existing0.35.5 override; the diagnostic is retained and is not described as a clean dependency-tree result. Clean CI installation, Next/Vinext builds and Worker bundling pass. Worker dry run is1455.74KiB/gzip409.60KiB with the existing ASSETS binding only.

Existing Supabase advisory limits remain: pg_net in public, and leaked-password protection disabled on the existing free plan. No extension removal, authentication weakening, privilege expansion or paid upgrade was performed. The prior local protected backup/restore remains dated; recovery keys and private account exports are not included in release evidence.

## Tests and browser proof

| Check | Scope / result |
|---|---|
| Full controlled browser regression |326 cases per Chromium,Firefox,WebKit; final exact-source runs pass |
| Focused local regression |42 navigation/precision cases pass; initial alignment regression failed at683px instead of0 before correction |
| Financial / API / market |295 financial/auth cases,30 API-edge and33 market units pass through the unchanged release gates; detailed ten-or-more-scenario matrix retained |
| Policy / compilation |28 audit-policy cases,AST,Next,Vinext and Worker dry run pass |
| Actual-public Chromium |30 pass against exact production37d03fd; no mocked APIs |
| Actual-public Firefox/WebKit |30 pass each against exact production37d03fd; no mocked APIs |
| Genuine existing normal session |All five selected navigation groups: natural-height titles/descriptions inside their rows, left aligned, no crossing underline; original rapid pointer/keyboard sequence passes |
| Genuine private account reads |Five existing reports load without errors; all ten Settings sections open with matching selected tabs/headings; no account changes or private exports |
| Genuine current live market |ETH/BTC ten actual oracle-history points each, accessible tables and freshness labels; explicit refresh advances block26250056 to26250059 and fee samples4 to7. Insufficient24-hour comparison remains unavailable. No mocks or fabricated points. |

The critical-workflow scenario lists and executable files remain in [WORKFLOW_SCENARIO_COVERAGE.md](WORKFLOW_SCENARIO_COVERAGE.md). Repeated cases across engines and source/PR/main gates are not distinct financial scenarios. Actual mobile geometry is covered by controlled browser fixtures; the host viewport capability did not establish a genuine375px session, so native mobile certification is not claimed. Existing installed-wallet approvals are not certified by injected provider fixtures.

The preliminary ed7f3c9 source passed Chromium325 and WebKit325; Firefox324/325 missed a positive sub-cent chart result after Calculate and used one earlier guarded Settings GET navigation recovery. The missing result's cause is unestablished. A separate behavioral test reproduced inherited smooth programmatic workspace scrolling; the correction does not establish that it caused the earlier chart failure. Test-owned pointer/submit diagnostics retain all original precision assertions; no app instrumentation or financial model changes were made. Final source326-per-engine runs have zero unexpected,skipped,flaky cases and zero driver recoveries. Ubuntu browser dependency mirrors delayed setup; installation time is not application test execution. Earlier failed evidence and navigation-release installer timeouts are preserved.

Genuine current-release screenshots are retained locally as `security-next-live-liquidationguard-full-20261022.png` and `security-next-live-liquidationguard-detail-20261022.png`. The manifest hashes evidence; protected keys and raw private account data are excluded.

Public workflow39832590075 attempt1 completed Firefox30, but WebKit was cancelled at the20-minute runner limit during Ubuntu dependency downloads; no WebKit application tests or result file were produced. The full attempt1 log and status are retained. A single same-head failed-job rerun also encountered slow Azure downloads. The runner-only fallback on `ci/public-browser-mirror-20261023` selects Ubuntu's official HTTPS archive instead of its slow Azure HTTP mirror. Package signatures/keyrings, browser versions, assertions, retry policy and20-minute limit are unchanged. This is a separate workflow run, not a zero-rerun release.

The final actual-public workflow39836207489 uses workflow source `ec857ccbd0b31ab879b1484d0d4c7f791d5a3ec9` and explicitly expects deployed37d03fd. A source identity record confirms the only changed file is the workflow; complete web, API, Supabase and dependency trees, including the tests, match production exactly. Its two browsers execute all30 actual-public cases each; final counts are taken from that full log, not combined partial successes. Original setup failures/delays remain retained. The CI-only branch is preserved without a production code change or deployment.

After the full HTTPS-runner proof passed, the superseded slow attempt2 was intentionally cancelled during installation. Its completed status and full log are retained. The preliminary20-minute setup timeout and this superseded cancellation are not application-test passes or hidden test retries.

## Readiness, costs and rollback

The supported bounded Ethereum beta workflows are deployed. This record does not certify unrestricted institutional use. Aave V3 normal mode and the validated Morpho WBTC/USDC86% LLTV market retain explicit unsupported states. Defense Planner uses a bounded5% search with at most two actions; results are not a global optimum, guarantee of safety, or automatic execution. Independent real financial reconciliation remains dated21October, linked from [production readiness](PRODUCTION_READINESS.md); this dependency/navigation release did not repeat production financial simulations.

Remaining external gates are real installed-wallet permission UI certification; an owned email domain/DNS and inbox-placement assurance (verification mail previously observed in Spam); independent key custody and second-machine/full-service restore,RPO/RTO; sustained field/load/availability and independent security/operating assurance; the disclosed Braces and Supabase advisories. No plan was upgraded, no email sent, no transaction signed, no data deleted and no credentials reset. Added recurring service cost isUSD0; account-wide billing and future free-tier usage are not certified.

The prior Worker `b5f973a6-b683-413b-8bcc-c39d8fbed0d5` / commit `643de5a2d2aad9ca05caee32131685f0bc2f5d50` remains available for an availability rollback. It restores the affected Next.js package range and therefore requires a patched roll-forward; it is not a secure permanent fallback. Protected source/data recovery material remains separate. Documentation closeout is saved on its own branch without triggering another runtime deployment.

The resumable root tracker, [readiness matrix](PRODUCTION_READINESS.md), [structured release evidence](evidence/next-security-release-20261023.json) and task-local `ACTIVE_RELEASE_CHECKPOINT.json` contain the next steps. Previous75 navigation hashes and72 authenticated-workflow hashes are rechecked without altering their historical records.
