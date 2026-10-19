# NPM audit exceptions

## GHSA-vfj7-8cjw-p6xm — `braces`

**Status:** temporary, narrowly-scoped CI exception  
**Recorded:** 2026-10-04  
**Severity:** High

Rivexis currently reaches `braces` through the Cloudflare/Vinext build-tool chain:

`@vinext/cloudflare` → `vinext` → `vite-plugin-commonjs` → `vite-plugin-dynamic-import` → `fast-glob` → `micromatch` → `braces`

GitHub's advisory currently reports no patched `braces` release. `npm audit fix --force` proposes a breaking Vinext downgrade, so Rivexis does not apply that destructive automatic remediation.

CI uses `scripts/npm-audit-ci.mjs`. It permits only this exact High advisory and only through the named dependency chain. Any other High or Critical vulnerability, any Critical escalation, a changed advisory, malformed audit output, or an audit execution failure still fails the build.

Remove this exception as soon as an upstream dependency chain resolves the advisory. Re-run a normal `npm audit --audit-level=high` after every Vinext/build-tool upgrade and before deleting this record.

Reference: https://github.com/advisories/GHSA-vfj7-8cjw-p6xm

## Audit evidence validation — 19 October 2026

The gate rejects registry/CLI error JSON, unsupported or missing report schemas, malformed advisory evidence, inconsistent package/severity counts and contradictory process exits. It requests an explicit `info` threshold from npm so a configured severity threshold cannot hide an execution mismatch, and limits the subprocess to 60 seconds. The exception requires the exact GitHub advisory URL on the `braces` advisory; finding its ID in another title is insufficient.

`node --test scripts/npm-audit-ci.test.mjs` exercises the actual CLI using an isolated fixture npm executable. These tests make no registry requests and do not modify the lockfile. CI runs these cases before application checks; the subsequent real registry audit is still required. The current real audit remains seven High package entries for the one documented transitive advisory, not a clean dependency report. Registry errors fail the gate rather than returning PASS. npm exit-code documentation: https://docs.npmjs.com/cli/v11/commands/npm-audit/#exit-code .
