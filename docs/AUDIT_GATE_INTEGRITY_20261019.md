# Release audit evidence integrity

19 October 2026, Asia/Calcutta. Existing RIVEXIS only; no application design, financial arithmetic, API, database, provider, auth or infrastructure changes.

## Defect and correction

`scripts/npm-audit-ci.mjs` previously treated absent `vulnerabilities` as an empty report. A registry error such as `{"error":{"code":"E500"}}`, malformed report metadata or an abnormal npm exit could therefore print PASS. It also recognized an advisory ID found in any title rather than requiring its authoritative URL. These were release-gate defects, not proof that production was exploited.

The corrected gate validates npm's v2 report structure, package/advisory severities, transitive evidence, summary counts and normal process exit. It requests an explicit info threshold so local npm configuration cannot change the expected exit semantics. An audit subprocess is bounded to60 seconds. Registry/CLI errors and missing/contradictory evidence fail closed. The existing exception requires the exact GitHub advisory URL on braces; a different High or any Critical remains rejected.

## Validation

- Before correction,22 real-CLI fixture scenarios produced10 passes and12 expected regression failures. The original log is retained outside source control.
- After correction,28 scenarios pass with no skips. They include clean/moderate reports, the one allowed exception, registry errors, unusual exits, truncated/missing/unknown schemas, hidden critical counts, understated severity, unrelated packages/advisories, spoofed titles, missing transitive evidence and repeated independent processes. The fake npm executable is confined to each test's temporary directory; no registry or production data is changed by those tests.
- The real npm registry audit passes only with its existing temporary exception: seven High package entries for GHSA-vfj7-8cjw-p6xm. GitHub still reports no patched release. No forced dependency downgrade or lockfile change.
- TypeScript and frontend AST checks passed. Exact-head CI/build and existing-URL verification are required before calling this merged/released. Functional browser count remains238, separate from28 audit-gate scenarios.

The branch also carries the already-validated performance-harness correction: trace/video off only during dedicated measurements; assertions still run after the measurement window. Documentation updates consolidate PR91's deployment identity. No runtime optimization claim follows from these test-harness changes.

## Release boundary

Candidate branch: `fix/audit-gate-failure-20261019`. Current verified runtime is PR91/20920918c46f23edc91d4f2edd57b8254bdafd4a until a newer marker is actually observed. Exact run/commit/deployment details will be recorded after release. Remaining domain, native wallet, recovery custody and separately authorized database maintenance gates are unchanged. No token creation or database upgrade is included.

References: https://docs.npmjs.com/cli/v11/commands/npm-audit/#exit-code and https://github.com/advisories/GHSA-vfj7-8cjw-p6xm .
