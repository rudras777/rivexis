# Rivexis Current Build State

Last updated: 2026-10-04

This is the authoritative compact continuation point for normal-chat execution. Always verify current `main`, current CI, Supabase runtime state, Cloudflare deployment state, and the live Worker before making production claims. Never reset to an older handoff or ZIP snapshot.

## Current source baseline

- Repository: `rudras777/rivexis`; branch: `main`.
- Hardened source immediately before this state-note commit: `95920e1eb153fed2ed41d283fefbe0044ed90c3b` (`Harden Edge role validation and test coverage`).
- The preceding fully certified application commit `0aa47be79370c13fae2b90a9da9b290279e70911` passed API tests/audit, PostgreSQL migration certification, invariants/secret scan, real frontend static validation, typechecks/builds, the scoped npm audit gate and full Playwright E2E.
- The one-shot role-hardening workflow tested its exact Edge patch and self-deleted successfully. Because a `GITHUB_TOKEN` self-push does not trigger normal repository CI, this state-note commit intentionally creates a fresh ordinary `main` push so the complete `95920e1e...` tree and this note are re-certified through standard CI/Worker workflows.

## Repairs completed on 2026-10-04

### Database / tenant security

- Organization RLS was split into explicit SELECT/UPDATE/DELETE policies plus one secure INSERT bootstrap policy.
- Repeated `current_setting(...)` policy lookups were rewritten to cached scalar subqueries.
- FORCE RLS and least-privilege runtime roles were preserved.
- Both organization bootstrap paths were rollback-tested: the pre-scoped Supabase Edge path and the authenticated FastAPI path. No probe rows persisted.
- The current organization bootstrap contract is source-controlled in Supabase migrations and Alembic and certified by PostgreSQL CI.
- Anonymous/public roles have no CREATE privilege on the `public` schema; Rivexis SECURITY DEFINER bridge RPCs are not executable by `anon` or `authenticated`.

### Authentication / email lifecycle

- Browser auth/recovery forms retain explicit POST semantics so passwords and verification/recovery values do not fall back into query strings.
- FastAPI password-reset state no longer marks a user email as verified merely because a reset was requested. A legacy user remains unverified until a valid reset token is actually consumed.
- A regression test covers the legacy-account reset edge case and session revocation behavior.
- The live Supabase Edge runtime uses Supabase Auth as its browser identity authority; `email_confirmed_at` is the live verification source.
- Supabase leaked-password protection remains disabled and requires an authenticated Supabase dashboard/configuration action to enable.

### Edge API contract / test coverage

- Invalid public roles no longer silently coerce to `Individual` in source. Signup, user-role update and workspace creation reject malformed roles; legacy metadata may still receive an explicit safe `Individual` default.
- `membership.test.mjs`, which existed but was previously omitted from the root Edge test command, is now included.
- A dedicated role parser/test was added to enforce the four public roles: `Individual`, `Fund`, `Treasury`, `Analyst`.
- The temporary write-capable one-shot maintenance workflow removed itself after applying and testing this patch.

### CI / dependency controls

- The old Next 16 `next lint || tsc --noEmit` fallback was removed because it could pass without performing a real lint/static gate.
- `lint:web` now executes the existing frontend AST validator and CI runs it separately from TypeScript typecheck.
- The AST gate checks TS/TSX parse diagnostics, duplicate object-literal keys and presence of the browser certification harness.
- The known unpatched `braces` High advisory reached through the Vinext/Cloudflare build chain is handled by a narrow fail-closed CI exception for exactly `GHSA-vfj7-8cjw-p6xm`. Any other High/Critical advisory, severity escalation, malformed audit output or changed dependency chain still fails CI.

### Web/UI regressions

- Route-specific titles are present in current source.
- Mobile landing-page overflow was fixed and regression-tested.
- Mobile public navigation is covered by browser regression tests.
- Login/signup/password-reset/email-verification fallback semantics are covered by browser tests.

## Supabase production truth

- Project: Rivexis (`ivszvufdonfgwjpfgwii`), region `ap-south-1`.
- Project health: `ACTIVE_HEALTHY` at the latest audit.
- Runtime logs inspected on 2026-10-04 showed zero severe events across Postgres, PostgREST, Edge Functions and the pooler in the checked window.
- `pg_net` is installed in `public`, but installed version `0.20.4` reports `relocatable = false`; do not force-move it to another schema.
- `alert_delivery_runtime` intentionally has RLS with no user-facing policies and remains deny-by-default.
- Unused-index advisor findings are informational. Do not delete structural/FK or low-traffic indexes merely because usage counters are currently zero.
- Three application `public.users` rows currently have no custom `user_auth_state` row. This does not break the live browser runtime because Supabase Edge uses Supabase Auth for identity/verification; treat it as cross-runtime compatibility debt, not permission to fabricate verification state.
- Deployed `rivexis-api` was version 9 at the latest runtime inspection. Its source is tracked in `supabase/functions/rivexis-api`; current `main` contains the stricter role-validation patch and should not be called deployed until a newer Edge function version is explicitly deployed and smoke-tested.

## Cloudflare frontend production truth

Production URL:

`https://rivexis-web.rudrasingh0718.workers.dev/`

Production is current only when the public Worker exposes the exact certified Git commit through the `rivexis-build` metadata marker.

Last independently observed live marker on 2026-10-04:

`fcea992098b377780b77516a0230490cbd83ad5d`

That marker is stale relative to current `main`. The live public site therefore must not be described as current even when source CI is green.

### Deployment blocker

- GitHub's manual Cloudflare deployment workflow is fail-closed and correctly verifies deployment authority before build/deploy.
- The stored `CLOUDFLARE_API_TOKEN` currently fails Cloudflare verification with error `6003`; the token must be replaced with a valid least-privileged Bearer API token.
- A secure browser attempt on 2026-10-04 found both Cloudflare and GitHub browser sessions unauthenticated, so no credential was created, copied or changed.
- Do not bypass the authority check, expose a Cloudflare token in chat, or weaken the workflow to force a deployment.

## Brevo / transactional email truth

- The Brevo connector is currently unable to connect to the account, so Brevo-side account/template/delivery certification is blocked until the connector is re-authenticated.
- Provider acceptance is not inbox-delivery proof. Do not claim verification/reset delivery is certified until the Brevo connection and an end-to-end email test are verified.

## Repository governance

- `main` is currently unprotected. The available GitHub App connection does not expose repository-administration writes for branch protection, and the browser session is not authenticated.
- Do not weaken CI because branch protection is absent. When GitHub admin access is available, require the standard CI checks before direct/merged changes to `main`.

## Security / evidence invariants

Keep these non-negotiable:

- never weaken authentication, CSRF, RLS or tenant isolation to make a UI path appear functional;
- never expose or persist credentials in source, logs or chat;
- never fabricate provider evidence;
- missing/unverified provider evidence remains UNKNOWN/unavailable;
- demonstration output stays explicitly synthetic;
- continuous alert delivery is not continuous threat ingestion;
- every legitimate source change must be committed to `main` and re-certified;
- source, deployed Edge runtime and deployed Cloudflare Worker are three separate states and must be verified independently.

## Immediate execution target

1. Certify this fresh `main` push through standard GitHub CI and Worker dry-run workflows.
2. Deploy and smoke-test the hardened `rivexis-api` Edge source so production no longer trails the role-validation contract.
3. Re-authenticate Brevo and certify transactional verification/reset delivery.
4. Replace the invalid GitHub `CLOUDFLARE_API_TOKEN` through authenticated Cloudflare/GitHub UI without exposing it, trigger production deployment, and verify the live `rivexis-build` marker equals the exact certified head.
5. Enable Supabase leaked-password protection through authenticated Auth settings when access is available.
6. Enable branch protection / required checks on `main` when GitHub administrative access is available.
