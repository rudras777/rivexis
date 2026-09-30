# Rivexis Current Build State

Last updated: 2026-10-01

This file is the authoritative compact continuation point for normal-chat execution. Always verify current `main`, current CI and the live Worker before making claims. Never reset to an older snapshot.

## Current source and certification

- Repository: `rudras777/rivexis`; branch: `main`.
- Source immediately before this state-note commit: `0e2f6eb034ccbeca603daab8f9ddbb44b0744785` (`Certify real public Royal Obsidian background`).
- Exact-head CI run: `36762835292` — **SUCCESS**.
- Certified gates include Python API lint/tests/audit, Edge typecheck/tests, PostgreSQL migrations/runtime controls, invariants, migration checks, secret scan, web typecheck/build, Vinext build, `npm audit --audit-level=high`, Playwright browser tests and accessibility checks.
- JavaScript security graph is patched and locked: Next `16.3.8`, `@cloudflare/vite-plugin` `1.62.3`, Wrangler `4.145.0`, with the root Wrangler override retained. `npm audit --audit-level=high` passes.
- CI/deploy Node runtime is aligned on Node 24/npm 11 so the secured lockfile is interpreted consistently.

## Royal Obsidian production source

The current certified source applies the Royal Obsidian system across the shared public/authenticated shell:

- obsidian black canvas;
- layered graphite/gunmetal surfaces;
- platinum/silver text and detail hierarchy;
- controlled royal sapphire blue for focus/action states;
- technical grid/radial visual fields rather than blank-white surfaces;
- official Rivexis wordmark/lockup/icon assets retained;
- compact high-standard controls instead of generic rounded AI/SaaS boxes;
- dark authentication cards/inputs and authenticated workstation surfaces;
- dark tables, panels, evidence surfaces and navigation rail;
- reduced-motion support and visible focus states retained.

The finishing pass also repaired two real accessibility contrast regressions found by Playwright and replaced one stale visual-contract assertion with a test for the actual public technical background.

## Functionality fixes in the current source

- Public mobile navigation now keeps Platform, product sections, login and workspace creation reachable on small screens.
- Login, signup, forgot-password, verify-email and reset-password forms explicitly use POST semantics; browser tests prevent mutation inputs from regressing to GET semantics.
- Existing authentication, CSRF, RLS, tenant isolation and evidence rules were not weakened by the visual work.
- No `href="#"` dead navigation was found in the current default branch audit.
- Current browser coverage remains the authority for functional claims; do not call an untested control production-verified.

## Backend production truth

- Authoritative compatibility backend is Supabase Edge/PostgreSQL.
- Public same-origin `/health` currently returns HTTP-ready JSON with service `rivexis-api`, runtime `supabase-edge`, API version `v1`, environment `production`.
- Supabase project is `ACTIVE_HEALTHY`.
- Latest security-advisor review found no critical finding. Remaining informational/advisory items included a deny-by-default RLS info item, `pg_net` in `public`, and leaked-password protection disabled. Do not move `pg_net` blindly because the certified scheduled dispatch path depends on it.
- Existing alert scheduler/Brevo, decision-report, monitoring, organization, history and engine compatibility work from prior certified state remains preserved unless a newer source explicitly changes it.

## Authoritative frontend truth

Production URL:

`https://rivexis-web.rudrasingh0718.workers.dev/`

### Source implemented / CI certified

Royal Obsidian and the functionality/security fixes above are implemented in GitHub and exact-head CI passed at `0e2f6eb034ccbeca603daab8f9ddbb44b0744785`.

### Deployed / production verified

Production is **not yet on that certified source**.

A fresh public fetch on 2026-10-01 exposed build marker:

`fcea992098b377780b77516a0230490cbd83ad5d`

Therefore the live Worker is stale relative to certified GitHub source. `/health` is ready, but Royal Obsidian/current-source parity must not be claimed until exact-SHA promotion succeeds.

### Current deployment blocker

Deploy run `36763032103` reached the actual Wrangler deploy step after successful checkout, Node setup, locked install, typecheck and Vinext build, then Cloudflare rejected authentication:

- Worker service request: authentication failed, HTTP 400, code `9106`.
- Token verification: invalid request headers, code `6003`.
- Authorization header: invalid format, code `6111`.

This proves the blocker is the stored Cloudflare credential value/authority, not application build failure. The token must be repaired in GitHub Actions before automated production promotion can succeed.

The deploy workflow now performs a fast Cloudflare token verification and target-Worker access preflight before installing/building. It never prints the token. It expects the raw API token value only and gives an explicit error for malformed credentials or an account/permission mismatch.

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

1. Repair the narrowly scoped `CLOUDFLARE_API_TOKEN` GitHub Actions secret (raw token value only) and confirm the configured account ID targets the account containing `rivexis-web`.
2. Re-run/trigger `deploy-web` only after CI success.
3. Require the workflow's exact-SHA verification step to pass.
4. Independently fetch production and confirm `rivexis-build` equals the deployed certified head before stating `deployed` or `production verified`.
5. Then continue route/control-level hardening from the newest `main`, prioritizing any real browser failure or dead control over cosmetic work.
