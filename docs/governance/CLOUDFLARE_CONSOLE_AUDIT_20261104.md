# Cloudflare console audit — 4 November 2026

The existing account `0b22778ba197266a58dd26eeef0334a8` was inspected after specific owner approval of the existing Google sign-in. A saved-profile attempt failed; the ordinary Google flow and a fresh controllable tab subsequently reached the authenticated account. No new account, permission expansion, plan change, DNS change or resource deletion occurred.

## Inventory and deployment

The Workers & Pages view shows **three resources total**: `rivexis-web`, `rivexis-api` and Pages `rvea-rivexis-gateway`. The retained API Worker has no bindings, custom domains or routes listed; its manually deployed `c624a830` version is historical. The current product uses the existing Supabase Edge API. Historical status is not authorization to delete the Worker; other callers have not been exhaustively excluded.

`rivexis-web` is connected to `rudras777/rivexis`. Workers Builds is enabled for production branch `main`, root `/`, build command `npm run build`, deploy command `npx wrangler deploy --config apps/web/dist/server/wrangler.json`, include watch path `*`, no excluded paths shown. Build cache is disabled. The public build variable is `NEXT_PUBLIC_RIVEXIS_PUBLIC_WEB_URL=https://rivexis.rvea.info`. The existing build-token name is `Workers Builds - 2026-10-06 01:40`; no value was read. Runtime variables/secrets and bindings show no configured entries; logs are enabled, traces/issues disabled, and no cron/queue/email triggers are listed for this Worker. Compatibility date is `2026-09-22`, flag `nodejs_compat`.

The automatic [PR126 build](https://dash.cloudflare.com/0b22778ba197266a58dd26eeef0334a8/workers/services/view/rivexis-web/production/builds/6a6f6c99-7b27-4628-b1cc-faa2ac5ed057) identifies source `e4a23c1`. Wrangler deployment readback and the console agree: version **`2e2e1a45-b8f0-4316-aaeb-3c815c0bd147`**, deployment `b0b50f0b-1cc6-48db-8947-3f0e7d1c2bff`, 100% traffic, created `2026-11-03T18:13:03.404409Z`. It superseded the manual workflow's `02442078-81d5-45f5-a4c7-5f3d5f936c42` at `18:11:28Z`. Both are PR126 source; the 74 live public checks started after the automatic version became active. Do not label the earlier manual version the current deployment.

Normal releases should use protected merge to `main` and the existing automatic build. The main-only GitHub deployment workflow remains a verified fallback; avoid routinely dispatching it alongside a healthy automatic build. The existing watch path also includes documentation changes, so merging an evidence-only PR can trigger a build. No trigger was disabled during inspection.

## Access, cost and operational limits

The Members view lists one active member. Account settings show the require-2FA control unchecked/disabled and state that the current user must turn on 2FA before enforcing it for all members. Infrastructure account protection remains an owner action; Google sign-in success alone is not independent MFA/recovery assurance.

Workers plans marks **Free / $0** as current, with 100,000 daily requests, 10 ms/request advertised CPU and 3,000 monthly build minutes. One observed usage window showed 5,310/100,000 requests and 1,958/200,000 observability events. These are dated counters, not a capacity forecast. The deployment screen showed median CPU around 41 ms despite the advertised Free allowance; existing successful requests do not establish sustained free-tier capacity. Preserve static landing delivery, bounded quotas and explicit performance/provider limits; do not silently upgrade.

The gateway has no Git connection and retains the existing additional custom hostname. The account's `rvea.info` zone and personal Wix apex are outside this release's change scope. Complete TLS/security-rule coverage, billing across every product, provider transfer eligibility and independent operational assurance remain unfinished. No global account-security or institutional certification is asserted.
