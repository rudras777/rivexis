# Rivexis Deployment Status

Last updated: 2026-09-23

| Environment | Status | Evidence / meaning |
|---|---|---|
| Local development | AVAILABLE, NOT VERIFIED IN THIS CHAT | Repository contains SQLite/local and Docker/PostgreSQL development paths. No local shell execution was used for this update. |
| GitHub CI | PASS FOR CURRENT MILESTONE SLICE | Latest engine-integrity gate: PR #24 head `dc8a481ca2136db83e13ee6b24c5ccf1b7e1bc04`, CI #255 (`35851151093`), with API, web/Playwright/Axe, invariants/secret/migration checks and PostgreSQL migration/runtime-control jobs all passing. |
| Free frontend preview | LIVE, SOURCE MERGED / DEPLOYMENT UNVERIFIED | `https://rivexis-web.rudrasingh0718.workers.dev` was previously reachable. Current Milestone F source is merged and CI-verified but is not claimed live until a Cloudflare deployment is independently verified. |
| Free API preview | LIVE / DEGRADED BY DESIGN | `https://rivexis-api.rudrasingh0718.workers.dev/health` previously returned `status=degraded`; application routes intentionally return 503. |
| Supabase PostgreSQL | ACTIVE_HEALTHY | Project `ivszvufdonfgwjpfgwii`, region `ap-south-1`; 53 product + 2 runtime-control tables previously verified. |
| Staging | PARTIAL | Supabase exists, but there is no separate live FastAPI staging runtime with complete provider/browser/email certification. |
| Production | BLOCKED | No live FastAPI runtime, no custom domain, no completed email/domain/provider certification and no complete release certification campaign. |

## Current deployed topology

- **Web:** Cloudflare Worker `rivexis-web` via vinext.
- **API hostname:** Cloudflare Worker `rivexis-api`.
- **API behavior on free tier:** health only + explicit degraded/503 application boundary.
- **Database:** Supabase PostgreSQL.
- **Distributed runtime controls:** PostgreSQL-backed path is implemented and migrated; Redis remains optional.
- **Email:** Brevo account/sender preparation exists, but production delivery is not certified.
- **Custom domain:** none configured.

## Current milestone verification

- Milestone E repository implementation is complete through PR #12.
- Milestone F remains the active repository milestone; its ten-engine audit is recorded in `docs/TEN_ENGINE_CONTRACT_AUDIT.md`.
- PRs #13–#15 established the shared live version/consensus/conflict and explicit F3-adapter trust boundaries.
- PRs #16–#20 added engine-specific integrity coverage for B1, F1, B5, B2 and B3.
- PR #21 (`F5 treasury input integrity`) CI #235 (`35849027346`) PASS; merged as `7e00dfd174d9d45a15f9ac8e24b8f81be5ea4ca0`.
- PR #22 (`F4 selector/freshness integrity`) CI #241 (`35849611567`) PASS; merged as `6b08418e2721d8f9cffeca406db5953746272cfc`. Its initial API audit attempt failed only at `pip-audit`; rerunning the same failed job on the unchanged dependency graph passed, and the full workflow concluded success before merge.
- PR #23 (`F2 provider payload/freshness integrity`) CI #249 (`35850515073`) PASS; merged as `f0676d0a911398a396aa5f32b187a1f14b5ee187`.
- PR #24 (`B4 entity/fund-flow provider integrity`) final head `dc8a481ca2136db83e13ee6b24c5ccf1b7e1bc04`; CI #255 (`35851151093`) PASS; merged as `683ff4d67a4923338d82c4be4656d62a81413adc`.
- All ten engines now have targeted repository-level integrity coverage for the contract/input/provider/freshness defects identified by the Milestone F audit. Remaining work is deeper evidence/capability completion, not a claim that all engine functionality is complete.
- These are repository-level implementation and CI findings only. They are not live-provider or production certification evidence.
- Real deployed browser/auth/workspace/analysis certification remains blocked until a live FastAPI runtime exists.
- No paid Cloudflare feature, new vendor, production credential, email send or external provider activation was performed by these slices.
- The live Worker is not claimed to contain the current merged source until a real deployment is verified.

## Supabase verification notes

- Project state: `ACTIVE_HEALTHY` at last verification.
- PostgreSQL engine: 17 at last verification.
- Runtime-control migration present.
- Supabase security advisor previously returned no findings.
- Generic table listing warns about non-RLS reference/system tables; direct grant inspection previously found no explicit `anon` or `authenticated` table privileges. This is not permission to weaken controls or expose those tables.

## Production activation gates

Production requires explicit approval/action for paid FastAPI-capable hosting, domain, production auth secret, least-privilege database runtime credential, isolated migration execution, final HTTPS origin, provider secrets/licenses, Brevo phone/domain setup and complete certification evidence.
