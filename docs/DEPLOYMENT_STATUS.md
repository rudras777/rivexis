# Rivexis Deployment Status

Last updated: 2026-09-23

| Environment | Status | Evidence / meaning |
|---|---|---|
| Local development | AVAILABLE, NOT VERIFIED IN THIS CHAT | Repository contains SQLite/local and Docker/PostgreSQL development paths. No local shell execution was used for this update. |
| GitHub CI | PASS FOR CURRENT MILESTONE | PR #10 CI run #144 (`35830902047`) passed API, web/Playwright/Axe, invariants and PostgreSQL migration/runtime-control jobs. |
| Free frontend preview | LIVE, SOURCE MERGED / DEPLOYMENT UNVERIFIED | `https://rivexis-web.rudrasingh0718.workers.dev` returned the Rivexis public site on 2026-09-23. Current Milestone E source is merged and CI-verified but is not claimed live until a Cloudflare deployment is independently verified. |
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

- Pull requests #1–#10 relevant to the current baseline remain merged and CI-verified as recorded in `BUILD_EXECUTION_PLAN.md`.
- Pull request #10 (`Harden decision evidence integrity and uncertainty semantics`) merged as `deca453077f51101ef853161d07836a26472778d`.
- PR #10 final head: `c817b0a9774faf1612faa4da61269d3b99911e4d`.
- CI run #144 (`35830902047`): API, web/Playwright/Axe, invariants and PostgreSQL migration/runtime-control jobs all PASS.
- The first Milestone E integrity slice is repository-test verified: persisted analyses are rehydrated before decision scoring, duplicate analysis/engine references cannot silently skew aggregate weighting, incomplete/conflicting/stale/unavailable requested evidence remains WAIT/UNKNOWN unless an explicit hard blocker independently requires AVOID, and decision methodology/evidence provenance is persisted and exposed through grounded explanations.
- Adversarial API regression coverage proves a caller cannot reuse a valid persisted analysis ID while replacing its risk/confidence/blocker fields with a forged safe payload.
- Real deployed browser/auth/workspace/analysis certification remains blocked until a live FastAPI runtime exists.
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
