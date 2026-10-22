# Workspace navigation production closeout

Verified 22 October 2026, Asia/Calcutta. The selected-function clipping and the subsequently reproduced interaction defects are corrected on the [existing production website](https://rivexis-web.rudrasingh0718.workers.dev/). Production commit **643de5a2d2aad9ca05caee32131685f0bc2f5d50**, merged [PR104](https://github.com/rudras777/rivexis/pull/104), matches source 4ec652976805455979f80cbd3537603a994ad55a and tree 7c1d4ef4437a2b8c96a4cda34973431b56bb8afe. [PR103](https://github.com/rudras777/rivexis/pull/103) supplied the clipping correction; PR104 completed interaction verification and correction.

The same rivexis-web Worker serves version b5f973a6-b683-413b-8bcc-c39d8fbed0d5 at 100%, deployment a47f428d-9d1d-4a64-ad0c-8d0c00b51f2b. Native Cloudflare build 93aa29ad-d811-49c5-a8b0-85d3e156c080 is Ready. Actual public HTML, health, guest-session status and the genuine signed-in browser identify the same commit. No separate site, Worker, repository or deployment provider was created.

## Completed corrections

- Scoped the top-navigation selection underline to its direct link, preventing it from crossing selected dropdown descriptions.
- Kept complete titles/descriptions left-aligned in natural-height rows. Short desktop/compact windows have bounded scrolling; keyboard-focused rows scroll fully into view. Nested compact submenus share the outer scroller.
- Cancelled stale hover timers on intentional keyboard activation, Escape, focus departure and outside clicks. Clicked menus remain available after pointer exit; hover-opened menus still dismiss on departure.

The logo, colors, public landing layout, background, authentication, financial models, API, schema and integrations are retained. The completed branch-only diagnostic workflow was removed; its logs and local-fixture click/request evidence remain retained.

## Verification

| Evidence | Result and scope |
|---|---|
| Exact source/PR/main/Worker gates | All seven recorded gates PASS. Main/source/PR Chromium 325; fixture Firefox 325 and WebKit 325. |
| Final actual-public suites | Chromium 30, Firefox 30, WebKit 30 PASS on 643de5a. Zero skipped/flaky/unexpected cases, test retries or driver recoveries in the final release evidence. |
| Focused navigation/connectivity | All 27 PASS. Sixteen navigation profiles added since the prior309-case release. Three interaction regressions fail before correction and pass afterward. |
| Financial/authentication and API controls | Financial/auth 295, API-edge 30, market units 33 and the full standard gates PASS. Thirteen retained source trees/files, including all backend functions/migrations and financial/API/authentication components, match the prior validated release. |
| Genuine signed-in production | All five groups navigate to their actual destinations. Every selected title/description fits inside its row, aligned without crossing decoration. The original rapid pointer/keyboard route sequence passes on 643de5a. Existing normal owner session; no session import, signing, report writes or account export. |
| Responsive/accessibility scope | Controlled desktop/mobile, short-window and enlarged-text geometry, keyboard and accessibility cases pass. A temporary host viewport request did not produce375px; that tab was closed and the override reset. No real-device mobile certification is inferred from it. |
| Prior evidence integrity | All 72 hashes in the prior authenticated-workflow manifest rechecked. Current manifest records 75 output hashes. Private recovery keys/data and account exports are excluded. |

The earlier live Aave/Morpho/planner/GasGuard integer reconciliations and recovery drill remain dated in [authenticated financial evidence](AUTHENTICATED_WORKFLOW_REVIEW_20261021.md). This navigation release does not re-certify current oracle prices, arbitrary protocols, signing or future execution. Supported coverage and modeling limits remain unchanged.

| Gate | Run |
|---|---|
| Source CI | [39820545164](https://github.com/rudras777/rivexis/actions/runs/39820545164) |
| PR CI | [39820588974](https://github.com/rudras777/rivexis/actions/runs/39820588974) |
| Worker bundle | [39820589053](https://github.com/rudras777/rivexis/actions/runs/39820589053) |
| Fixture Firefox/WebKit | [39820589119](https://github.com/rudras777/rivexis/actions/runs/39820589119) |
| Main CI | [39822245795](https://github.com/rudras777/rivexis/actions/runs/39822245795) |
| Main Worker bundle | [39822245668](https://github.com/rudras777/rivexis/actions/runs/39822245668) |
| Actual-public Firefox/WebKit | [39822464022](https://github.com/rudras777/rivexis/actions/runs/39822464022) |

## Retained failures and limits

Original corrected before-change clipping profiles failed 7/13; the initial fixture's mobile Escape expectation and a nullable test diagnostic-label type were corrected separately. Preliminary Firefox 319/322 exposed the short-window focus defect plus report/transaction five-second failures. A later 321/322 run repeated the report-request failure. The latter timeout causes remain unestablished; no financial assertion was weakened. Three isolated report-save runs and the instrumented full suites passed. One initial diagnostic workflow argument error ran no tests. Superseded/cancelled runs are retained separately.

PR103's intermediate public WebKit job exhausted its 20-minute job budget while installing Ubuntu browser dependencies; its application tests did not run. The final PR104 public WebKit 30/30 result comes from a fresh completed job. Local Firefox could not launch with spawn UNKNOWN, so Linux CI supplies Firefox coverage. PR103's final fixture Firefox recorded one guarded driver GET recovery; PR104's final fixture/public engines recorded zero. Final successes do not erase earlier observations.

The separate six-sample performance observation remains a small lab measurement, with one desktop LCP4616ms and no established cause; it is not field Core Web Vitals, load capacity or an SLA. Earlier read-only provider aggregates cover only their explicitly recorded window/stream. Cloudflare runtime metrics displayed No data, so zero runtime errors are not certified.

## Readiness, cost and rollback

These navigation corrections and existing supported bounded-beta workflows are deployed and verified within their recorded scope. **Unrestricted institutional launch remains BLOCKED** by native installed-wallet permission UX, owned sending-domain/inbox placement, independent key custody/second-machine/full-service recovery and sustained field/load/security/operating assurance. The disclosed unpatched braces and Supabase configuration advisories remain open. See [readiness matrix](PRODUCTION_READINESS.md); no paid upgrade or unreviewed security weakening was performed.

The 22 October read-only security refresh confirms the same findings. [The official braces advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) still lists no patched version. Supabase warns about [extension placement](https://supabase.com/docs/guides/database/database-linter?lint=0014_extension_in_public) and [leaked-password protection](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection); its no-policy informational entry concerns the retained deny-default tables. No schema, account or plan setting was changed by this refresh.

Added recurring service cost: **$0**. Total account billing is not independently certified. Rollback remains 99eee482686be6bb99a79f9c99127dc18a97ab0d / Worker 0c9491a8-d8b1-41ef-88aa-316434b8919c, with older c829a3d/a77fd608 also retained. No database migration or user-data deletion accompanies this release.

Structured release identities, counts, scope and local artifact hashes: [workspace navigation evidence](evidence/workspace-navigation-release-20261022.json). Screenshots in task outputs: menu-intent-live-liquidationguard-detail-20261022.png and menu-intent-live-liquidationguard-full-20261022.png. A documentation closeout branch records these final observations without causing another runtime deployment.
