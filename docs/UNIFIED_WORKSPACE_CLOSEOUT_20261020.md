# Verified unified workspace release — 20 October 2026

## Outcome and identity

The existing [RIVEXIS production website](https://rivexis-web.rudrasingh0718.workers.dev/) is deployed and verified for controlled early access within its documented Ethereum coverage. Unrestricted institutional certification remains blocked by the owner/resource and assurance gates below. This report records completed application work; it does not broaden coverage or certify continuous availability.

- Final application commit: **4849a626d433c051f440d2b9aff434cc4435e277**.
- [PR96](https://github.com/rudras777/rivexis/pull/96): implementation source 83ec3746329dafa016a937a890bc9e07062301ae, merge fd294bf05b9fb9256ccbffa8609e8613e1eb913c.
- [PR97](https://github.com/rudras777/rivexis/pull/97): test-only source 910a60a5e66cec6ce245c0b0c6a3120d17332098, merge 4849a626. Application/runtime trees match PR96 exactly.
- Existing rivexis-web Worker version **6824855c-fed9-45ae-8d6b-72e85fa93476**, 100% configured allocation; deployment 0d9b69e0-2bc0-42b7-aebf-9c1fe81fce3d; native build cac2f5f3-b11f-461a-b4a8-17e92b8fc3ef succeeded.
- No-cache public HTTP200, genuine signed-in DOM and the deployment identity independently agree on 4849a626. The evidence-only closeout branch does not trigger another application release.

## Completed application changes

The legacy /app entry now redirects to /workspace with obsolete query parameters discarded. The authenticated educational /demo uses the same horizontal dropdown navigation and saved Appearance settings. Its separate provider isolates explicitly hypothetical inputs from actual inspected positions; returning to Overview preserves the actual analysis. The old numbered educational tabs and duplicated public header are removed from that entry.

A reproduced hover-then-click dropdown race is fixed, with mobile, keyboard, modified-click links and heading focus retained. Settings now invokes the existing logout controller directly rather than depending on an effect-installed global event listener. Pending logout disables Settings writes; provider failure preserves the session for explicit retry. The controller's CSRF, failure handling, memory clearing and redirect logic are unchanged. A regression intentionally failed against the old event bridge and passed after correction.

The approved logo, colors, public layout, background and financial logic are preserved. No floating bottom-right Pause button is present; accessible motion preferences remain. Mandatory authentication, free core access, Settings, wallet/contract interfaces, private reports/history and earlier chart/storage/request-resilience work remain included. Obsolete B1–B5/F1–F5 public product interfaces remain retired; reusable backend and rollback history are retained.

AST/tree comparisons confirm 17 financial handlers and seven calculation expressions, the logout controller, API34/backend, dependencies, styles and public assets were not changed by PR96. PR97 changes only the actual-public canonical-login test. No production data, account settings, schema, grants, credentials, plan or integration configuration was changed in this release.

## Validation evidence

| Gate | Verified result |
| --- | --- |
| Final source CI [39373801206](https://github.com/rudras777/rivexis/actions/runs/39373801206) and PR CI [39373806917](https://github.com/rudras777/rivexis/actions/runs/39373806917) | PASS; 291 Chromium workflow cases each |
| Final compatibility [39373806920](https://github.com/rudras777/rivexis/actions/runs/39373806920) | PASS; 291 Firefox and 291 WebKit; 455409.806 ms /409788.097 ms |
| Final Worker gate [39373807026](https://github.com/rudras777/rivexis/actions/runs/39373807026) | PASS |
| Final main CI [39374822104](https://github.com/rudras777/rivexis/actions/runs/39374822104) and Worker [39374822122](https://github.com/rudras777/rivexis/actions/runs/39374822122) | PASS; main Chromium 291 plus standard gates |
| Actual final public URL, Chromium |30/30 PASS; 112341.254 ms |
| Actual final public URL [39375045067](https://github.com/rudras777/rivexis/actions/runs/39375045067) | Firefox 30/30, WebKit 30/30 PASS; 68272.822 ms /64321.042 ms |
| Financial / API-edge / audit / sequence-RPC policy |221 /30 /28 /10 PASS |
| Market / API client / wallet / browser-driver safety |21 /12 /18 /30 PASS |
| Builds and engineering gates | Next and Vinext production builds, official typegen, types, AST 173, Python/API/security/Postgres migration/restore/invariant/secret gates PASS |

Final browser case results have zero skipped, unexpected or flaky cases, zero test retries and zero guarded driver GET releases. Counts across engines and repeated release gates are not unique scenarios. The separate inactive fixture job in the public-mode workflow is intentionally not selected; no browser cases were skipped. The [scenario matrix](WORKFLOW_SCENARIO_COVERAGE.md) maps at least ten scenarios per critical workflow, including invalid inputs, constraints, stale evidence, provider failures and repeated operations.

Actual-public tests use no route mocks, fabricated market responses, production account writes or signing. Browser regression fixtures exercise controlled error paths separately. Real native-wallet permission dialogs and live Settings session revocation were not performed in this release; those controls are covered by bounded provider/controller tests and earlier service evidence, within the limits stated below.

## Genuine financial and browser observations

On final4849a626, a genuine signed-in read of public-reference wallet 0xbdc3c47122d033ccd1Ad7b986071187Be597fF72 produced Morpho block **26231717**, hash 0x52225d94f29cef51683ee677d49598f715d26203e120468f113143432288e9e6. Displayed collateral $9, 928, 946.26, debt $6, 828, 631.80 and health1.250 are observations, not wallet ownership or current quotes.

Budget3000, assumed fee 25, target 1.50 and zero shocks examined59 allocations and returned six alternatives, all honestly marked target unmet. The actual UI JSON export was independently checked with integer/rational arithmetic, without importing application models or making new RPC calls. Baseline, all six outcomes, debt-share rounding, wallet balances, costs/fees and unrounded budget bounds reconcile exactly. No transaction was signed, submitted or saved to the account. The three-minute evidence age limit correctly withholds subsequent calculations when stale.

Earlier genuine sequence evidence at 26229566→26229567 remains included: three steps, 3, 639, 338 raw WBTC delta and 132, 065 summed gas independently reconcile exactly. This release did not run a new sequence simulation or broaden sequential protocol coverage.

Actual authenticated navigation, all ten Settings sections, /app redirect, educational sample isolation and restored actual analysis were inspected. Natural market polling advanced26231654→26231670 and fee history12→24 without clock/network changes; ETH/BTC oracle history contained seven observations each. Missing24-hour coverage remains explicitly stated. Final Overview screenshot/DOM record4849a626, actual position 26231717 and market 26231726, including freshness and understandable charts/tables.

## Rejected evidence and recovery

Earlier mixed-theme accessibility and historical-report/logout failures were retained and their heads rejected, as detailed in [canonical entry development evidence](CANONICAL_WORKSPACE_ENTRY_20261020.md). No accessibility violations or financial assertions were suppressed.

The first actual-public runs on PR96 passed29/30 per engine because a test incorrectly expected /login?next=%2Fworkspace instead of canonical /login. PR97 corrects that expectation and actually follows the link to verify the login form; runtime code is unchanged.

A subsequent actual-public Firefox run 39373826528 passed29/30: the /demo document remained unanswered for 15 seconds. The guard refused recovery, with zero driver releases; cause is unestablished. Two later no-cache probes returned200 in 943 ms and 226 ms. The final bounded run on 4849a626 passes all30 per engine. This recovery does not erase the timeout or establish an availability/performance SLA.

## Security, recovery and cost

Fresh read-only Supabase catalog checks: existing projectivszvufdonfgwjpfgwii ACTIVE_HEALTHY, 17.6.1.166; 61 public tables, zero without RLS; nine public security-definer functions, zero executable by anon/authenticated. Nineteen INFO findings reflect intentional private deny-by-default tables. Warnings remain for [pg_net in public](https://supabase.com/docs/guides/database/database-linter?lint=0014_extension_in_public) and [disabled leaked-password protection](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection), the latter requiring Pro in the checked project. No paid upgrade or privilege widening was performed.

Python audit reports no known vulnerabilities. The npm gate retains the disclosed, narrowly scoped High build-tool advisory **GHSA-vfj7-8cjw-p6xm**, appearing through seven package entries; no patched braces version was available at the checked state. The28-case gate rejects other high/critical findings and malformed/error audit results. A passing gate is not a clean dependency audit.

The existing GitHub/Cloudflare/Supabase/Brevo resources, users and data remain intact. Added recurring services cost is **$0**; account-wide billing is not independently certified. Prior Worker versions and baseline/pre-defi-transformation-20261009 remain rollback references. The17 October read-only logical archive/isolated restore and private off-device encrypted-copy/hash/decryption checks are recorded in [recovery](RECOVERY_DRILL_20261017.md) and [off-device evidence](OFFSITE_RECOVERY_20261017.md). Protected archives/keys are excluded from Git and this manifest; the key was not uploaded.

## Remaining launch boundaries and next safe actions

1. Provide owned sending-domain/DNS control before authenticating the sender. Existing verification/recovery delivery works, but Spam was observed; inbox placement is uncertified. No purchase/new SMTP is authorized.
2. Provide an actual unlocked native test wallet for permission-UX verification. Injected-provider tests are not native-dialog certification. No importing/unlocking/signing or private-key request is authorized.
3. Establish independent recovery-key custody, second-machine/full-service recovery, retention and RPO/RTO. Existing local/off-device encrypted-copy verification does not establish those properties.
4. A fresh protected backup before maintenance requires the specific pending approval for a new 24-hour privileged Supabase token, then revocation. The previous token was revoked; no new one was created. The offered 17.11.0.003 upgrade separately requires explicit approval for up-to-one-hour downtime and no downgrade after a fresh recovery path. No upgrade/reset was performed.
5. Establish sustained field performance, load/provider availability and institutional operating/security assurance. Retain the observed public timeout and variable lab measurements.
6. Resolve or formally accept the disclosed dependency and Supabase configuration advisories through a safe recovery/change process; never silently buy a plan or force a breaking dependency upgrade.

Validated financial scope remains Ethereum Aave V3 normal mode with WETH/USDC/USDT/WBTC adapters and the pinned Morpho WBTC/USDC86% LLTV market. Defense Planner uses a bounded 5% grid and at most two actions; it does not guarantee global optimality, safety or future execution. Monitoring is bounded browser work/history, not continuous server monitoring. Reports include JSON evidence; no new PDF workflow is claimed.

## Evidence and resumability

[Structured release proof](evidence/unified-workspace-release-20261020.json) contains release/run identities and SHA256 hashes of 21 allowlisted raw logs, receipts, independent checks and the final screenshot in the task outputs directory. [Current checkpoint](../RIVEXIS_PRODUCTION_COMPLETION_TRACKER.md) and [readiness matrix](PRODUCTION_READINESS.md) distinguish completed implementation from the remaining owner/assurance gates. Historical records stay dated; do not repeat completed deployment or disclose protected recovery material.
