# Rivexis Deployment Status

Last updated: 2026-09-23

| Environment | Status | Evidence / meaning |
|---|---|---|
| Local development | AVAILABLE, NOT VERIFIED IN THIS CHAT | Repository contains SQLite/local and Docker/PostgreSQL development paths. No local shell execution was used for this update. |
| GitHub CI | PASS FOR CURRENT MILESTONE SLICE | PR #15 CI run #187 (`35836050226`) passed API, web/Playwright/Axe, invariants and PostgreSQL migration/runtime-control jobs after PR #13/#14 also passed their full gates. |
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
- Milestone F ten-engine contract audit is active and recorded in `docs/TEN_ENGINE_CONTRACT_AUDIT.md`.
- PR #13 (`Normalize ten-engine live evidence contracts`) final head `195dbdd39db9dffa13eba0626a31a569bbeeb32c`; CI #175 (`35834716319`) PASS; merged as `7571776acc222f53458823b8a2fe962d5f22cb29`.
- PR #14 (`Fail closed on explicit F3 protocol-adapter requests`) final head `a6e86cd23b57d1eaf1b1131c46b09d4ac1792595`; CI #181 (`35835418949`) PASS; merged as `3f3a637c1e3e5ff55b5d1211db7780e43fd69943`.
- PR #15 (`Promote unresolved live provider conflicts to conflicting status`) final head `34f66a0abd9794efd9352b73e733212cc5a2a350`; CI #187 (`35836050226`) PASS; merged as `faf0652cf6834a59c7e55d09759bdbf13689218f`.
- Current live-dispatch contract now aligns current result/evidence engine versions, preserves specific calculation versions, derives provider consensus from actual evidence, promotes unresolved provider conflicts to `CONFLICTING_DATA`, and keeps historical persisted analyses unchanged.
- F3 explicit authoritative adapter requests no longer silently fall through to a generic modeled risk conclusion; missing authoritative adapter evidence fails closed.
- B4 external identity-label disagreement no longer remains an ordinary partial state; conflict consensus and status now agree.
- These are repository-level implementation and CI findings only. They are not live-provider or production certification evidence.
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
