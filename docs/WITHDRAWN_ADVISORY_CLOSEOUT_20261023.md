# Withdrawn Braces advisory and strict audit policy — 23 October 2026

The previously disclosed Braces advisory is now withdrawn upstream. GitHub's [reviewed advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) and public API report withdrawal at12:53:02UTC,23 October2026, because the reported issue was not practically exploitable. A real npm audit at15:17UTC returns exit0 and zero findings at every severity across371 reported dependencies. This updates the earlier seven-High-entry observation; preserve those earlier receipts with their actual dates. No patched Braces version or package upgrade is being claimed.

## Implemented policy

`scripts/npm-audit-ci.mjs` removes the entire advisory-ID/package-chain allowance. Every High or Critical finding now fails, including the withdrawn advisory should it return. The gate still validates schema, package identity, advisory evidence, severity ordering, transitive references, counts and subprocess status. Registry/CLI errors, empty/truncated output and contradictory evidence still fail. The60-second subprocess bound and explicit npm audit severity threshold remain unchanged. Valid Moderate-only findings retain their existing policy.

The real gate is exercised through an isolated fixture npm executable. With the new retired-advisory expectations but the old implementation,27 cases pass and two fail because the old exception returns success. After removing the allowance, all29 pass, including the complete former seven-package chain, a different High advisory, Critical escalation, spoofed title and malformed/error evidence. The real corrected gate independently passes against the current zero-finding registry response. The [seven-file local manifest](evidence/withdrawn-advisory-20261023.json) preserves the raw before/after failure evidence and official withdrawal metadata outside Git.

## Application and release boundary

No application, shared financial model, API/backend, authentication, schema, dependency, lockfile, deployment configuration, logo, palette, layout or animated background changes are included. These source objects remain identical to verified production63049e1/PR106. The [post-release evidence record](BETA_RELEASE_CLOSEOUT_20261023.md) accompanies this policy change; no private receipt, recovery key, account export or credential is added to Git.

Require exact source/PR CI and existing Worker build checks before merge. The existing Cloudflare main integration, deployed marker, main CI and independent public browser checks must be verified after merge. No condition, timeout, assertion, signature/keyring validation or browser recovery policy is weakened. Exact final source/merge/build/Worker identities and gate URLs are recorded in the release PR and resumable checkpoint; this source report does not declare pending remote gates successful.

## Operational observations and remaining assurance

An independent public probe on63049e1 returns homepage200, exact build marker, health200/ready and guest private-reports401. Read-only Supabase aggregate observations show zero recorded/open legacy provider circuits and zero recent legacy rate events. Empty legacy telemetry is not evidence of current DeFi-provider availability. The existing retained notification dispatcher reports scheduled/Brevo readiness, recent successful runs, zero processed/delivered/failed and no error code; that is not a delivered-mail/inbox test. No SQL write, dispatch, email, account-setting or paid-plan operation was performed.

GO for the previously accepted small supported beta remains unchanged. The owner chose the existing verified sender. Native installed-wallet permission UX, owned-domain/inbox assurance, independent protected-key/second-machine/full-service recovery/RPO/RTO, sustained field/load/provider availability and independent security/operating assurance remain outside verified scope. Existing Supabase configuration advisories remain. A clean npm registry report and stricter CI policy do not establish unrestricted institutional readiness.

Added recurring service cost:USD0. Preserve the current users/data, free-tier limits and patched rollback. Resume only for an observed defect or the resources needed for the remaining assurance items.
