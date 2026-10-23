# NPM audit policy and exception history

## Current policy — 23 October 2026

**No active High or Critical exceptions.** GitHub withdrew [GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) at12:53:02UTC on23 October because it was not practically exploitable. The fresh15:17UTC npm audit of the unchanged lockfile reports zero findings at every severity (371 dependencies reported). This is registry/advisory evidence at the stated time, not independent security certification.

The former package/advisory allowlist is removed from `scripts/npm-audit-ci.mjs`. Every High or Critical finding now fails, including a future report of the withdrawn ID and all seven formerly excepted package entries. Existing JSON/schema/count/severity/transitive-evidence/process-exit validation, the60-second subprocess limit and registry-error rejection remain intact. Moderate-only valid reports retain the existing severity policy.

All29 gate scenarios pass locally. Before the correction, the two new/changed retired-exception expectations fail because the actual old gate returns success; afterward both fail-closed expectations pass. The real updated gate passes against the zero-finding registry report. No dependency, lockfile, application, financial, authentication or deployment configuration changes are required. Exact source/PR/main results belong to the release record; local results do not predeclare deployment success.

## Historical exception: GHSA-vfj7-8cjw-p6xm — `braces`

**Status:** retired23 October 2026; the following describes the earlier policy
**Recorded:** 2026-10-04
**Severity:** High

Rivexis currently reaches `braces` through the Cloudflare/Vinext build-tool chain:

`@vinext/cloudflare` → `vinext` → `vite-plugin-commonjs` → `vite-plugin-dynamic-import` → `fast-glob` → `micromatch` → `braces`

At the time of the exception, GitHub reported no patched `braces` release. `npm audit fix --force` proposed a breaking Vinext downgrade, so Rivexis did not apply that automatic remediation.

CI uses `scripts/npm-audit-ci.mjs`. The earlier policy permitted only this exact High advisory through the named dependency chain. Any other High or Critical vulnerability, any Critical escalation, a changed advisory, malformed audit output, or an audit execution failure failed the build. The current policy above removes the exception entirely.

The exception was retired after the upstream advisory withdrawal and a real zero-finding npm audit. Preserve this historical record. Re-run the real audit after every Vinext/build-tool upgrade; do not restore a blanket allowance for the former chain.

Reference: https://github.com/advisories/GHSA-vfj7-8cjw-p6xm

## Audit evidence validation — 19 October 2026

The gate rejects registry/CLI error JSON, unsupported or missing report schemas, malformed advisory evidence, inconsistent package/severity counts and contradictory process exits. It requests an explicit `info` threshold from npm so a configured severity threshold cannot hide an execution mismatch, and limits the subprocess to 60 seconds. The exception requires the exact GitHub advisory URL on the `braces` advisory; finding its ID in another title is insufficient.

`node --test scripts/npm-audit-ci.test.mjs` exercises the actual CLI using an isolated fixture npm executable. These tests make no registry requests and do not modify the lockfile. CI runs these cases before application checks; the subsequent real registry audit is still required. The real audit at that date had seven High package entries for the one documented transitive advisory. It is retained as historical evidence; the current23October audit above has zero findings. Registry errors fail the gate rather than returning PASS. npm exit-code documentation: https://docs.npmjs.com/cli/v11/commands/npm-audit/#exit-code .
