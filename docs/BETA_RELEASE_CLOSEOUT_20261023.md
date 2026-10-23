# Verified controlled-beta release — 23 October 2026

**GO for the supported, small controlled beta on24 October, Asia/Calcutta.** PR106 was merged and deployed to the existing RIVEXIS Worker. This does not certify unrestricted institutional use, unlimited free capacity or guaranteed financial outcomes. The owner explicitly chose to retain the current verified sender for this beta.

## Observed release identity

| Item | Verified value |
|---|---|
| Existing public site | https://rivexis-web.rudrasingh0718.workers.dev/ |
| Release pull request | [PR106](https://github.com/rudras777/rivexis/pull/106) |
| Tested source | `34d0f1687696db5b992487d5e142daa759027c34` |
| Actual deployed merge | `63049e1b04eba6f03c3ee503a13de0d2f861ca0b` |
| Merge/source Git tree | `06050528a229d417fcd37e6eb50fabc6fd2914ca`, exactly equal |
| Native Worker version | `6beb786b` (dashboard prefix; full UUID not collected) |
| Native build | `a8f9f2f4-2df8-4e4d-b7b8-2f1c6e477847`, Ready42s, main,100% traffic |
| Availability rollback | Patched PR105/`37d03fd3c539085538cbbca48ea2f29b91a581fb`, Worker`c63e2bcd-64e0-44b8-914a-41e2103d3484` retained |

Independent HTTPS reads and actual browsers observe the deployed build marker. `/health` returns200/ready. An unauthenticated request to `/api/v1/defi/reports` returns401/Authentication required without cookies. A preliminary default Python request returned403; its cause is unestablished. Subsequent Node HTTPS requests and all90 actual-public browser cases passed. The403 is retained, not represented as a demonstrated application defect or erased from the record.

## Release gates and actual workflow checks

| Exact-source gate | Result |
|---|---|
| [Source CI39968967259](https://github.com/rudras777/rivexis/actions/runs/39968967259) | All four jobs PASS;326 Chromium/295 financial-auth cases |
| [PR CI39969050560](https://github.com/rudras777/rivexis/actions/runs/39969050560) | All four jobs PASS;326 Chromium/295 financial-auth cases |
| [PR Worker39969050503](https://github.com/rudras777/rivexis/actions/runs/39969050503) | Configured-root and default-root bundle/dry-run checks PASS |
| [Fixture compatibility39969050597](https://github.com/rudras777/rivexis/actions/runs/39969050597) | Firefox326/WebKit326 PASS; zero skipped/flaky/unexpected test cases |
| [Main CI39971037273](https://github.com/rudras777/rivexis/actions/runs/39971037273) | All four jobs PASS;326 Chromium/295 financial-auth cases |
| [Main Worker39971037212](https://github.com/rudras777/rivexis/actions/runs/39971037212) | Both bundle/dry-run checks PASS |
| Actual-public Chromium on deployed merge |30/30 PASS; zero skipped/flaky/unexpected cases, retries disabled |
| [Actual-public39971347806](https://github.com/rudras777/rivexis/actions/runs/39971347806) | Firefox30/WebKit30 PASS against exact deployed merge; zero skipped/flaky/unexpected cases or driver releases |

Fixture Firefox recorded one guarded navigation-driver GET release. Its retained diagnostic shows a completed200 document, zero pending requests, zero page/resource/server errors, and content/build markers present. All assertions still ran; no application action or failed test was retried as success. WebKit and both public engines recorded zero driver releases. The conditionally unused fixture/public workflow job is skipped by design; no browser test case is skipped. Existing earlier failures remain dated in their original records.

After deployment, the ordinary existing verified account still opens the authorized workspace without session import, password reset or bypass. All five top navigation menus keep every title and description inside its row and viewport. All six private saved reports load. All ten Settings sections render; Dark/Comfortable/System-motion preferences remain saved. This final Settings check submitted no preference, security, session or account-management change. Fresh market observations advance26255976→26256010; ETH/BTC series contain8/7 actual points and the fee series grows4→24. Missing24-hour coverage remains explicit. Bounded captured browser errors: zero. These observations are neither a field availability guarantee nor server-wide telemetry certification.

## Scope, financial evidence and preserved infrastructure

This promotion fixes the observed Ubuntu package-download setup stall by selecting official HTTPS archives on ephemeral CI runners. Package verification, pinned versions, timeouts, assertions and navigation policy are preserved. It also places the dated security, approved recovery-copy and launch acceptance records in main. No application, financial model, API/backend, authentication, Supabase schema, dependency, deployment configuration, logo, palette, layout or background source changes are included.

Application, Supabase, shared-package, manifest and lockfile Git objects match the prior production release exactly. Therefore the genuine23October financial acceptance remains applicable with its original observation times: [Aave/Morpho/planner/GasGuard and both selected sequences](BETA_LAUNCH_20261024.md), [35 original receipt/checker hashes](evidence/beta-launch-20261024.json). Six standalone accounting checkers independently reconcile the actual downloaded receipts using integer/rational references. These are genuine observations, separate from the [ten-or-more controlled scenarios per critical workflow](WORKFLOW_SCENARIO_COVERAGE.md). The planner remains bounded and cannot guarantee a globally optimal strategy, safety or execution. No private key, signature, approval transaction or transaction submission was used.

Existing Cloudflare, Supabase and Brevo resources, users and reports are retained. No backend deployment, SQL mutation, new service, paid plan, sender or sharing change occurred in this release. Added recurring service cost:USD0; account-wide future billing is not certified. Server limits remain300 analyses per UTC day globally, four per wallet per minute and20 reports per account. Start within this shared beta budget. The approved encrypted recovery copy has independent ciphertext verification; its separate key was not read or uploaded.

## Remaining assurance and resume rule

Native installed-wallet permission dialogs, owned-domain/inbox assurance, independent protected-key custody and second-machine/full-service recovery/RPO/RTO, sustained load/provider availability and independent security/operating assurance remain unverified. Existing unpatched Braces and Supabase configuration advisories remain disclosed in the dated reports. The beta sender decision is resolved, not waiting for another owner answer.

No known supported-workflow code blocker was found in this release. Preserve the patched rollback and dated evidence. Resume for an observed defect or the external assurance resources above; do not repeat completed releases or represent this controlled-beta decision as institutional certification. [Release evidence hashes](evidence/beta-release-20261023.json) accompany this closeout; raw receipts, account data, credentials and recovery keys stay outside Git. The final PR body and local resumable checkpoint hold the observed release identities without requiring a self-referential redeployment for documentation.
