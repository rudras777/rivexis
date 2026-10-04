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
