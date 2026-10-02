# Rivexis Current Build State

Last updated: 2026-10-02

This file is the authoritative compact continuation point for normal-chat execution. Always verify current `main`, current CI and the live Worker before making claims. Never reset to an older snapshot.

## Current source and certification

- Repository: `rudras777/rivexis`; branch: `main`.
- Source immediately before this state-note commit: `c498f1d18ac59c2bd53f161316f0516ddc584da0` (`Remove temporary Cloudflare credential diagnostic`).
- Exact-head CI run: `36976960298` — **SUCCESS**.
- Certified gates include Python API lint/tests/audit, Edge typecheck/tests, PostgreSQL migrations/runtime controls, invariants, migration checks, secret scan, web typecheck/build, Vinext build, `npm audit --audit-level=high`, Playwright browser tests and accessibility checks.
- JavaScript security graph remains patched and locked: Next `16.3.8`, `@cloudflare/vite-plugin` `1.62.3`, Wrangler `4.145.0`, with the root Wrangler override retained.
- CI/deploy Node runtime remains aligned on Node 24/npm 11.
- The temporary credential-shape diagnostic workflow used during deployment triage was removed from `main`; no credential value was printed or persisted in source.

## Royal Graphite production source

The current certified source applies the Royal Graphite / Obsidian system across the shared public, authentication and authenticated shells:

- obsidian black canvas with layered charcoal, graphite and gunmetal surfaces;
- platinum, silver and pearl text/detail hierarchy;
- restrained neutral metallic action treatment instead of electric-blue dominance;
- technical grid/radial visual fields rather than blank-white surfaces;
- official Rivexis wordmark, lockup and icon assets retained;
- compact institutional controls instead of generic rounded AI/SaaS boxes;
- dark authentication cards, inputs, tables, panels, evidence surfaces and navigation rail;
- accessible contrast, visible focus states and reduced-motion support retained.

Visual-system browser assertions were updated to certify the actual Royal Graphite palette and all certified browser/accessibility tests pass.

## Functionality and scope hardening in current source

- Public mobile navigation keeps Platform, product sections, login and workspace creation reachable on small screens.
- Login, signup, forgot-password, verify-email and reset-password forms explicitly use POST semantics.
- Saved analyses, history and Decision Desk async completions are scoped to their originating workspace so switching workspaces cannot leak stale completion state into another workspace.
- Organization member role/update/remove/claim mutation results are scoped to the originating organization; stale success/error UI is not rendered under another organization.
- Membership-claim organization input is frozen while claim generation is pending.
- Existing authentication, CSRF, RLS, tenant isolation and evidence rules were not weakened.
- Current browser coverage is the authority for functional claims; untested controls must not be called production-verified.

## Backend production truth

- Authoritative compatibility backend is Supabase Edge/PostgreSQL.
- Public same-origin `/health` returns ready JSON for service `rivexis-api`, runtime `supabase-edge`, API version `v1`, environment `production`.
- Supabase project is `ACTIVE_HEALTHY`.
- Latest security-advisor review found no critical finding. Informational/advisory items included deny-by-default RLS information, `pg_net` in `public`, and leaked-password protection disabled. Do not move `pg_net` blindly because the certified scheduled dispatch path depends on it.
- Existing alert scheduler/Brevo, decision-report, monitoring, organization, history and engine compatibility work remains preserved unless a newer source explicitly changes it.

## Authoritative frontend truth

Production URL:

`https://rivexis-web.rudrasingh0718.workers.dev/`

### Source implemented / CI certified

Royal Graphite, current functionality hardening and deployment workflow hardening are implemented in GitHub. Exact-head CI passed for cleanup source `c498f1d18ac59c2bd53f161316f0516ddc584da0` in run `36976960298`.

### Deployed / production verified

Production is **not yet on the certified source**.

Latest independently observed public build marker before this state update:

`fcea992098b377780b77516a0230490cbd83ad5d`

Therefore the public Worker remains stale relative to certified GitHub source. `/health` is ready, but current-source parity must not be claimed until exact-SHA promotion succeeds.

## Current deployment blocker

The deployment workflow now safely normalizes common accidental wrappers around `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`, verifies both supported Cloudflare user/account token scopes, checks access to the existing `rivexis-web` Worker before build/deploy, and never prints credential values.

Repeated preflight verification still returns Cloudflare error `6003` for the stored API-token secret after safe normalization. The account-ID secret has been structurally confirmed as a correctly formed 32-character Cloudflare account ID, while the stored API-token value does not match a valid current or legacy Cloudflare API-token format and cannot authenticate either supported token scope.

A browser recovery path was also attempted. No authenticated Cloudflare dashboard session exists in the remote browser, and federated sign-in requires owner authentication on a recognized device. No password, passkey, MFA code or recovery credential was requested, captured, guessed or bypassed.

This is an external deployment-authority blocker, not an application build, test, database or source-code failure.

## Security/evidence invariants

Keep all of these non-negotiable:

- never weaken authentication, CSRF, RLS or tenant isolation to make a UI path appear functional;
- never expose secrets or persist credentials in source/logs;
- never fabricate provider evidence;
- missing/unverified provider evidence remains UNKNOWN/unavailable;
- demonstration output stays explicitly synthetic;
- provider acceptance is not inbox-delivery proof;
- continuous alert delivery is not continuous threat ingestion;
- every legitimate source change must be committed to `main` and re-certified.

## Immediate execution target

1. Restore valid Cloudflare deployment authority by replacing `CLOUDFLARE_API_TOKEN` with a valid Cloudflare API token for the account containing `rivexis-web`, or by authenticating the Cloudflare dashboard on a recognized owner device and establishing an authorized Git/Workers deployment path.
2. Re-run `deploy-web` only after CI success.
3. Require the workflow's exact-SHA verification step to pass.
4. Independently fetch production and confirm `rivexis-build` equals the deployed certified head before stating `deployed` or `production verified`.
5. Continue route/control-level hardening only from the newest `main` after production parity is established.
