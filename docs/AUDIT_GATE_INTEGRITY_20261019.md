# Verified release audit evidence integrity

19 October 2026, Asia/Calcutta. Existing RIVEXIS only; no application design, financial arithmetic, API, database, provider, auth or infrastructure changes.

## Verified release

Merged PR92: https://github.com/rudras777/rivexis/pull/92 . Source **e9fe582d6f1c7c1ce606ac048435fc7b8274ab1e**, production merge **ddb70a7dcaee5691cf49b829acd891f992998c16**. Existing URL https://rivexis-web.rudrasingh0718.workers.dev/ exposes that exact marker over HTTP200 and genuine authenticated DOM. Existing Worker **d7c23d0f-88d8-4c3a-b000-e458e88ec0b9** has100% configured allocation, independently read with Wrangler. Native build **74b5e477-83b0-4f45-8c1b-7db6312f9f46** has a successful Cloudflare provider check on the same commit; no new dashboard Ready-row observation is claimed.

| Gate | Actual run | Result |
| --- | --- | --- |
| Source CI |39252650174|PASS;238 browser cases;28 audit-gate scenarios and existing financial/API/security/PostgreSQL suites|
| PR CI |39252691381|PASS;238 browser cases and28 audit-gate scenarios|
| PR Worker |39252691501|PASS; both existing root/bundle configurations|
| Main CI |39253505281|PASS;238 browser cases and28 audit-gate scenarios|
| Main Worker |39253505689|PASS|
| Existing public URL |28 cases,109.307s|PASS; zero retries/skips/flakes|

## Defect and correction

`scripts/npm-audit-ci.mjs` previously treated absent `vulnerabilities` as an empty report. A registry error such as `{"error":{"code":"E500"}}`, malformed report metadata or an abnormal npm exit could therefore print PASS. It also recognized an advisory ID found in any title rather than requiring its authoritative URL. These were release-gate defects, not proof that production was exploited.

The corrected gate validates npm's v2 report structure, package/advisory severities, transitive evidence, summary counts and normal process exit. It requests an explicit info threshold so local npm configuration cannot change the expected exit semantics. An audit subprocess is bounded to60 seconds. Registry/CLI errors and missing/contradictory evidence fail closed. The existing exception requires the exact GitHub advisory URL on braces; a different High or any Critical remains rejected.

## Validation

- Before correction,22 real-CLI fixture scenarios produced10 passes and12 expected regression failures. The original log is retained outside source control.
- After correction,28 scenarios pass with no skips. They include clean/moderate reports, the one allowed exception, registry errors, unusual exits, truncated/missing/unknown schemas, hidden critical counts, understated severity, unrelated packages/advisories, spoofed titles, missing transitive evidence and repeated independent processes. The fake npm executable is confined to each test's temporary directory; no registry or production data is changed by those tests.
- The real npm registry audit passes only with its existing temporary exception: seven High package entries for GHSA-vfj7-8cjw-p6xm. GitHub still reports no patched release. No forced dependency downgrade or lockfile change.
- TypeScript, frontend AST165, both builds, secret scan and exact-head source/PR/main checks passed. Functional browser count remains238, separate from28 audit-gate scenarios and28 actual-public cases.

The branch also carries the already-validated performance-harness correction: trace/video off only during dedicated measurements; assertions still run after the measurement window. Documentation updates consolidate PR91's deployment identity. No runtime optimization claim follows from these test-harness changes.

## Genuine financial and market verification

The existing dedicated QA session opened the deployed workspace. A fresh supported public-reference Morpho read at block26226679 showed collateral$9,992,848.74, debt$6,827,899.92 and health1.258, with sensitivity/readout consistency. Default$3,000 capital,$25 assumed fees and1.500 target returned six alternatives, correctly reporting that none reached target. Downloaded receipts were independently reconciled with integer/rational Python reference arithmetic, without application model imports or additional RPC. Baseline, all six action outcomes, shared wallet constraints, reported costs and exact unrounded budget feasibility matched.

Selected Morpho approval/supply sequence: parent26226684, simulated child26226685; reset/approve/supply succeeded with validation true, no state/block overrides, WBTC delta3615052 and gas28384+48320+55361=132065. Native health/debt/token/approval arithmetic matched exactly. This is simulation evidence, not execution, safety or global-optimum certification. No ownership claim, wallet permission, signing or transaction submission occurred.

Planner-to-GasGuard handoff preserved exact0.03615052 WBTC. Individual preview at26226691 honestly reported insufficient protocol allowance and unavailable independent call/gas/fee evidence. A successful sequence with included approvals does not turn an unapproved standalone call into success. Genuine network context displayed a fresh block and four historical base-fee observations. No invented points or production clock overrides.

Three additional public mobile4x-CPU probes with trace/video off passed behavior assertions: LCP5568/2240/4260ms; response-start3621/634/563ms; CLS0/0/0.000943. The variation remains unresolved and does not establish field performance or an SLA. Earlier samples remain retained.

## Remaining boundary

**READY FOR CONTROLLED EARLY ACCESS** within existing supported lending scope and quotas; unrestricted institutional certification remains blocked by sender-domain authentication, real native-wallet permission testing, independent recovery custody/full-service recovery and security/operational assurance. New privileged backup-token approval remains pending; no token creation, database upgrade, paid plan or key upload occurred. Added recurring cost$0. The approved visual design, authentication and financial source are preserved. This separate documentation closeout is not a newer runtime and needs no extra deployment merely to name itself.

Raw outside-repository records: `audit-gate-release-proof-20261019.json`; source/PR/main/Worker logs; `pr92-native-build-check-20261019.json`; `pr92-worker-deployments-20261019.json`; HTTP/browser identity and28-case results; planner/sequence/individual receipts; independent reference script/reconciliations; genuine screenshots; three mobile measurement JSON/log pairs. Original regression failures and slower samples remain retained. Never commit keys, credentials, session material or unrelated outputs.

References: https://docs.npmjs.com/cli/v11/commands/npm-audit/#exit-code and https://github.com/advisories/GHSA-vfj7-8cjw-p6xm .
