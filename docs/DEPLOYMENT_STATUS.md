# Rivexis Deployment Status

Last updated: 2026-09-23

| Environment | Status | Evidence / meaning |
|---|---|---|
| Local development | AVAILABLE, NOT VERIFIED IN THIS CHAT | Repository contains SQLite/local and Docker/PostgreSQL development paths. No local shell execution was used for this update. |
| GitHub CI | PASS FOR CURRENT MILESTONE SLICE | Latest engine-integrity gate: PR #30 head `efbff97df9574bd15c4e1b6c74850fcc59bd2c3f`, CI #293 (`35897012617`), with API, web/Playwright/Axe, invariants/secret/migration checks and PostgreSQL migration/runtime-control jobs all passing. |
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
- PRs #13–#15 established shared live version/consensus/conflict and explicit F3-adapter trust boundaries.
- PRs #16–#25 established the first engine-depth/integrity campaign and synchronized the durable state.
- PR #26 (`B1 canonical standard event effects`) CI #271 (`35857083832`) PASS before merge.
- PR #27 (`F1 numeric/completeness integrity`) CI #277 (`35861080306`) PASS before merge.
- PR #28 (`B4 token identity and counterparty-flow integrity`) CI #282 (`35895021465`) PASS; merged as `d8bb045800ee534d182acc88d094589bafa816a2`.
- PR #29 (`B1 event parser ABI/input bounds`) CI #287 (`35896050913`) PASS; merged as `0d56ba9ca80e340b21ea48f6f990aa7d04d77b3e`.
- PR #30 (`B3 monitoring runtime integrity`) final head `efbff97df9574bd15c4e1b6c74850fcc59bd2c3f`; CI #293 (`35897012617`) PASS; merged as `042f08376f3b27cbd87dec0df6fb72ed063cdb52`.
- All ten engines retain targeted repository-level contract/input/provider/freshness integrity coverage. Recent slices deepen B1 standard-event parsing, B3 malformed-state/oracle semantics, B4 fund-flow identity/counterparty semantics and F1 completeness/numeric boundaries.
- Remaining Milestone F work is capability depth requiring approved evidence sources or additional deterministic normalization; it is not a claim that all ten engines are production-complete.
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
