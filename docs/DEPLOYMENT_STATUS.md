# Rivexis Deployment Status

Last updated: 2026-09-23

| Environment | Status | Evidence / meaning |
|---|---|---|
| Local development | AVAILABLE, NOT VERIFIED IN THIS CHAT | Repository contains SQLite/local and Docker/PostgreSQL development paths. No local shell execution was used for this update. |
| GitHub CI | PASS FOR CURRENT MILESTONE | PR #9 CI run #129 (`35828771358`) passed API, web/Playwright/Axe, invariants and PostgreSQL migration/runtime-control jobs. |
| Free frontend preview | LIVE, SOURCE MERGED / DEPLOYMENT UNVERIFIED | `https://rivexis-web.rudrasingh0718.workers.dev` returned the Rivexis public site on 2026-09-23. Current Milestone D source is merged and CI-verified but is not claimed live until a Cloudflare deployment is independently verified. |
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

- Pull requests #1–#7 remain merged and CI-verified as previously recorded.
- Pull request #9 (`Complete truthful workspace dashboard and settings summaries`) merged as `22a999d018e8c84dd907d48a973d58406aa5ed33`.
- PR #9 final head: `55dbcb2a2ba1373dc0504734e802d75826de0048`.
- CI run #129 (`35828771358`): API, web/Playwright/Axe, invariants and PostgreSQL migration/runtime-control jobs all PASS.
- Milestone D is repository-test complete: active workspace query isolation and in-place switching are retained; dashboard activity comes from authorized workspace History; static product counts are labeled metadata; History/Saved Analyses use supported-field summaries; Settings exposes authorized workspace/org membership data and creation outcomes without implying unsupported member administration.
- The first PR #9 browser run failed only because one legacy mock used a non-contract History field and one selector was ambiguous; both tests were corrected without weakening application behavior or isolation assertions.
- Real deployed browser/auth/workspace certification remains blocked until a live FastAPI runtime exists.
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
