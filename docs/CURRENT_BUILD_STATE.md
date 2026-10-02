# Rivexis Current Build State

Last updated: 2026-10-02

This file is the authoritative compact continuation point for normal-chat execution. Always verify current `main`, current CI, Cloudflare build/deploy state and the live Worker before making claims. Never reset to an older snapshot.

## Current source and certification

- Repository: `rudras777/rivexis`; branch: `main`.
- Runtime/deployment source immediately before this state-note commit: `c35e39f2c7f27a3094e9094b3a430e91743ff832` (`Make token-based deploy a manual fallback`).
- Exact-head predecessor `ec1d2a08060f568d035333c5ec54317eb8d5f529` passed all CI gates in run `36978799270`.
- Certified gates include Python API lint/tests/audit, Edge typecheck/tests, PostgreSQL migrations/runtime controls, invariants, migration checks, secret scan, web typecheck/build, Vinext build, `npm audit --audit-level=high`, Playwright browser tests and accessibility checks.
- JavaScript security graph remains patched and locked: Next `16.3.8`, `@cloudflare/vite-plugin` `1.62.3`, Wrangler `4.145.0`, with the root Wrangler override retained.
- CI runtime remains aligned on Node 24/npm 11.

## Royal Graphite production source

The current source applies the Royal Graphite / Obsidian system across the shared public, authentication and authenticated shells:

- obsidian black canvas with layered charcoal, graphite and gunmetal surfaces;
- platinum, silver and pearl text/detail hierarchy;
- restrained neutral metallic action treatment instead of electric-blue dominance;
- technical grid/radial visual fields rather than blank-white surfaces;
- official Rivexis wordmark, lockup and icon assets retained;
- compact institutional controls instead of generic rounded AI/SaaS boxes;
- dark authentication cards, inputs, tables, panels, evidence surfaces and navigation rail;
- accessible contrast, visible focus states and reduced-motion support retained.

## Functionality and scope hardening in current source

- Public mobile navigation keeps Platform, product sections, login and workspace creation reachable on small screens.
- Login, signup, forgot-password, verify-email and reset-password forms explicitly use POST semantics.
- Saved analyses, history and Decision Desk async completions are scoped to their originating workspace so switching workspaces cannot leak stale completion state into another workspace.
- Organization member role/update/remove/claim mutation results are scoped to the originating organization; stale success/error UI is not rendered under another organization.
- Membership-claim organization input is frozen while claim generation is pending.
- `organization-scope-switching.spec.ts` now includes regression coverage for role-draft isolation, stale completed mutation banners and claim-target locking while the request is pending.
- Current source audit found no `href="#"` placeholder navigation, no TODO stubs and no null click handlers.
- Existing authentication, CSRF, RLS, tenant isolation and evidence rules were not weakened.

## Backend production truth

- Authoritative compatibility backend is Supabase Edge/PostgreSQL.
- Public same-origin `/health` returns ready JSON for service `rivexis-api`, runtime `supabase-edge`, API version `v1`, environment `production`.
- Supabase project is `ACTIVE_HEALTHY`.
- Latest security-advisor review found no critical finding. Informational/advisory items included deny-by-default RLS information, `pg_net` in `public`, and leaked-password protection disabled. Do not move `pg_net` blindly because the certified scheduled dispatch path depends on it.
- Existing alert scheduler/Brevo, decision-report, monitoring, organization, history and engine compatibility work remains preserved unless a newer source explicitly changes it.

## Authoritative frontend truth

Production URL:

`https://rivexis-web.rudrasingh0718.workers.dev/`

### Deployed / production verified

Production is not called current until the public Worker exposes the exact certified Git commit through the `rivexis-build` metadata marker.

Last independently observed stale marker before native-Git deployment verification:

`fcea992098b377780b77516a0230490cbd83ad5d`

## Deployment architecture

### Primary path: Cloudflare Workers Builds + GitHub

The preferred production path is Cloudflare Workers Builds connected directly to the existing `rivexis-web` Worker and `rudras777/rivexis` GitHub repository.

Source preparation completed:

- `apps/web/scripts/cloudflare-workers-build-deploy.mjs` requires a valid `WORKERS_CI_COMMIT_SHA`, restricts itself to `WORKERS_CI=1`, forces `NEXT_PUBLIC_RIVEXIS_API_URL=same-origin`, and stamps `NEXT_PUBLIC_RIVEXIS_BUILD_SHA` from the exact Cloudflare build commit;
- `apps/web/package.json` exposes this as the standard `deploy` script while preserving `deploy:vinext`;
- CI performs `node --check` on the native Workers Builds entrypoint;
- the existing `deploy-web` GitHub Actions workflow is `workflow_dispatch` only, retained as a manual token-based fallback rather than auto-failing after every successful CI run.

Expected native Workers Builds configuration for the existing Worker:

- repository: `rudras777/rivexis`;
- production branch: `main`;
- root directory: `apps/web`;
- deploy command: `npm run deploy`;
- Workers Builds deployment authority: Cloudflare-managed;
- Worker name: `rivexis-web`.

The owner reported this Git connection completed on 2026-10-02. This state-note commit intentionally creates a fresh `main` push so the new Cloudflare integration can prove itself on a post-connection commit. Do not call the integration verified until a Cloudflare build/deploy signal appears and the public Worker marker equals the exact new head.

### Manual fallback: GitHub Actions token deploy

The GitHub Actions `deploy-web` workflow remains available only through manual dispatch. Its stored `CLOUDFLARE_API_TOKEN` is currently invalid and repeated verification returned Cloudflare error `6003`; the account-ID secret is structurally valid. This fallback must not be used unless a valid token is deliberately configured.

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

1. Observe Cloudflare Workers Builds on this fresh post-connection push.
2. Exact-head certify this trigger commit through GitHub CI.
3. If the Cloudflare build fails, fix the build configuration/source and push again.
4. Independently fetch production and confirm `rivexis-build` equals the exact deployed certified head before stating `deployed` or `production verified`.
5. After native deployment is verified, retire or rotate the invalid GitHub `CLOUDFLARE_API_TOKEN` fallback secret as appropriate.
