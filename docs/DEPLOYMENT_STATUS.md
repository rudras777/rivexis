# Rivexis Deployment Status

Last updated: 2026-09-23

| Environment | Status | Evidence / meaning |
|---|---|---|
| Local development | AVAILABLE, NOT VERIFIED IN THIS CHAT | Repository contains SQLite/local and Docker/PostgreSQL development paths. No local shell execution was used for this update. |
| GitHub CI | PASS FOR CURRENT MILESTONE | PR #5 CI run #77 (`35798213551`) passed API, web/Playwright/Axe, invariants and PostgreSQL migration/runtime-control jobs. |
| Free frontend preview | LIVE, SOURCE MERGED / DEPLOYMENT UNVERIFIED | `https://rivexis-web.rudrasingh0718.workers.dev` returned the Rivexis public site on 2026-09-23. Current auth/session source is merged and CI-verified but is not claimed live until a Cloudflare deployment is independently verified. |
| Free API preview | LIVE / DEGRADED BY DESIGN | `https://rivexis-api.rudrasingh0718.workers.dev/health` returned `status=degraded`; application routes intentionally return 503. |
| Supabase PostgreSQL | ACTIVE_HEALTHY | Project `ivszvufdonfgwjpfgwii`, region `ap-south-1`; 53 product + 2 runtime-control tables verified. |
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

- Pull request #1 (`Add durable build state and global degraded-service UX`) merged to `main` as `ca16f39898b6392a022372ffe04cc595278a1fb6`.
- Pull request #2 (`Harden authenticated workspace shell states`) merged to `main` as `773a2faa2a6653c79972e98df505f01b15d702ea`.
- Pull request #3 (`Harden responsive and keyboard workspace shell`) merged to `main` as `926265f2c0e44a5a0f74caf6c815c2cf0e638f72`.
- Pull request #4 (`Harden browser authentication and resumable onboarding`) merged to `main` as `543dcccff3a2b094c504d68453000685648c96ec`.
- Pull request #5 (`Harden browser session restoration and logout lifecycle`) merged to `main` as `158eedd7a13bf0dd0089a5d60138dcd18de6f46d`.
- PR #5 final head: `f1016623466c86c5b15250ed3e25cd262ea258df`.
- CI run #77: all four jobs PASS.
- Repository-level browser session continuity/logout/revocation is verified; real deployed browser/auth certification remains blocked until a live FastAPI runtime exists.
- Durable plan synchronization continued on `main` after each merge.
- No paid Cloudflare feature, new vendor, production credential, email send or external provider activation was performed.
- The live Worker is not claimed to contain the current merged source until a real deployment is verified.

## Supabase verification notes

- Project state: `ACTIVE_HEALTHY`.
- PostgreSQL engine: 17.
- Runtime-control migration present.
- Supabase security advisor: no findings at verification time.
- Generic table listing warns about non-RLS reference/system tables; direct grant inspection found no explicit `anon` or `authenticated` table privileges. This is not permission to weaken controls or expose those tables.

## Production activation gates

Production requires explicit approval/action for paid FastAPI-capable hosting, domain, production auth secret, least-privilege database runtime credential, isolated migration execution, final HTTPS origin, provider secrets/licenses, Brevo phone/domain setup and complete certification evidence.
