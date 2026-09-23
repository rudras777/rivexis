# Rivexis Deployment Status

Last updated: 2026-09-23

| Environment | Status | Evidence / meaning |
|---|---|---|
| Local development | AVAILABLE, NOT VERIFIED IN THIS CHAT | Repository contains SQLite/local and Docker/PostgreSQL development paths. No local shell execution was used for this update. |
| GitHub CI | PASS FOR CURRENT MILESTONE | PR #12 CI run #164 (`35832725687`) passed API, web/Playwright/Axe, invariants and PostgreSQL migration/runtime-control jobs. |
| Free frontend preview | LIVE, SOURCE MERGED / DEPLOYMENT UNVERIFIED | `https://rivexis-web.rudrasingh0718.workers.dev` was previously reachable. Milestone E source is merged and CI-verified but is not claimed live until a Cloudflare deployment is independently verified. |
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
- PR #12 (`Add canonical provenance inspection to workspace History`) merged as `ad136be86f8536bbd5d2e917d7dc8a086b376ac4`.
- PR #12 final head: `b7c3b7e3c974ea901c3d920278b1c42f6396fcbc`.
- CI run #164 (`35832725687`): API, web/Playwright/Axe, invariants and PostgreSQL migration/runtime-control jobs all PASS.
- Workspace History now loads canonical persisted analysis/decision provenance only when requested, using the existing authorized detail endpoints. It does not fan out across the capped history list or dump raw persisted payloads.
- History provenance detail is workspace-query-keyed and cleared on active-workspace changes; browser coverage proves old-workspace evidence/provenance does not remain visible after a switch.
- Decision-integrity and report/engine provenance controls from PR #10/#11 remain preserved and CI-green.
- Milestone F (ten-engine completion) is now the active repository milestone.
- Real deployed browser/auth/workspace/analysis certification remains blocked until a live FastAPI runtime exists.
- No paid Cloudflare feature, new vendor, production credential, email send or external provider activation was performed.
- The live Worker is not claimed to contain the current merged source until a real deployment is verified.

## Supabase verification notes

- Project state: `ACTIVE_HEALTHY` at last verification.
- PostgreSQL engine: 17 at last verification.
- Runtime-control migration present.
- Supabase security advisor previously returned no findings.
- Generic table listing warns about non-RLS reference/system tables; direct grant inspection previously found no explicit `anon` or `authenticated` table privileges. This is not permission to weaken controls or expose those tables.

## Production activation gates

Production requires explicit approval/action for paid FastAPI-capable hosting, domain, production auth secret, least-privilege database runtime credential, isolated migration execution, final HTTPS origin, provider secrets/licenses, Brevo phone/domain setup and complete certification evidence.
