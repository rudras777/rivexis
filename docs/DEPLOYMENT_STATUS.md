# Rivexis Deployment Status

Last updated: 2026-09-24

| Environment | Status | Evidence / meaning |
|---|---|---|
| Local development | AVAILABLE, NOT VERIFIED IN THIS CHAT | Repository contains SQLite/local and Docker/PostgreSQL development paths. No local shell execution was used for this update. |
| GitHub CI | PASS FOR CURRENT IMPLEMENTATION SLICE | Head `6eecf44c921c6b31dddc265c2e62c60ac664a44e` passed full CI #302 (`35916994577`): API lint/tests/pip-audit, web type/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and PostgreSQL migration/runtime-control certification all passed. A later documentation-only state synchronization commit may therefore be ahead of this implementation head. |
| Free frontend preview | LIVE, DEPLOYMENT DRIFT DETECTED | `https://rivexis-web.rudrasingh0718.workers.dev` is reachable. Public pages `/`, `/login`, `/signup`, `/platform` and `/security` loaded successfully on 2026-09-24. However, an unauthenticated real-browser visit to `/workspace` rendered an older demo-safe workspace shell instead of the access-withholding behavior in current `main`; no private user/analysis data was observed. Current-main source is therefore not claimed live. |
| Free API preview | LIVE / DEGRADED BY DESIGN | `https://rivexis-api.rudrasingh0718.workers.dev/health` returned `{"status":"degraded","service":"rivexis-api","reason":"FastAPI runtime unavailable on the approved free-tier stack"}`. |
| Supabase PostgreSQL | ACTIVE_HEALTHY | Project `ivszvufdonfgwjpfgwii`, region `ap-south-1`, PostgreSQL 17.6.1. Six environment-management migrations were visible. Product/runtime tables exist; direct inspection found no `anon` or `authenticated` public-table grants, while the security advisor returned no findings. |
| Staging | PARTIAL | Supabase exists, but there is no separate live FastAPI staging runtime with complete provider/browser/email certification. |
| Production | BLOCKED | Current frontend source is not yet independently verified deployed, there is no live FastAPI application runtime, no custom domain, no implemented/certified Brevo transactional-email layer, and no complete release certification campaign. |

## Current deployed topology

- **Web:** Cloudflare Worker `rivexis-web` via vinext.
- **API hostname:** Cloudflare Worker `rivexis-api`.
- **API behavior on free tier:** health only + explicit degraded/503 application boundary.
- **Database:** Supabase PostgreSQL.
- **Distributed runtime controls:** PostgreSQL-backed path is implemented and migrated; Redis remains optional.
- **Email:** owner-side Brevo phone/account verification is recorded complete by the authoritative production-build mandate, but the repository currently has no Brevo environment contract/client/template implementation and production delivery is not certified.
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
- Direct-main implementation commit `6eecf44c921c6b31dddc265c2e62c60ac664a44e` hardens F2 DefiLlama audit metadata so malformed, contradictory, insecure or declaration-only audit data cannot reduce protocol risk; CI #302 (`35916994577`) PASS.
- All ten engines retain targeted repository-level contract/input/provider/freshness integrity coverage. Remaining Milestone F work is capability depth requiring approved evidence sources or additional deterministic normalization; it is not a claim that all ten engines are production-complete.
- These are repository-level implementation and CI findings only. They are not live-provider or full production certification evidence.

## Live browser verification — 2026-09-24

Verified without entering credentials or creating production data:

- homepage loaded and advertised evidence-driven blockchain/crypto-finance decision infrastructure;
- `/login` loaded the email/password login surface;
- `/signup` loaded the workspace/role onboarding surface;
- `/platform` and `/security` loaded normally;
- API `/health` truthfully reported degraded runtime state;
- unauthenticated `/workspace` did **not** redirect to login and rendered a demo-safe workspace shell with generic engine/product metadata. No user PII, private investigation data or stored analysis records were observed in that browser check.

Current `main` does not match that live workspace behavior: `AppShell` first calls `/api/v1/workspaces`; pending/error/session states withhold authenticated navigation/content, and 401/403/503 paths do not render workspace children. The live discrepancy is therefore recorded as deployment drift until a current-main Cloudflare deployment is verified.

## Cloudflare deployment access check — 2026-09-24

- Cloudflare dashboard was reached in a real browser but redirected to account login.
- The available browser profile/vault contains no Cloudflare credentials.
- Consequently the existing `rivexis-web` project, production deployment identity and GitHub/main integration could not be inspected, and no new production deployment was triggered.
- No DNS, environment variable, billing/plan, API Worker or secret setting was changed.

## Supabase verification notes

- Project state: `ACTIVE_HEALTHY`.
- PostgreSQL engine: 17.6.1.
- Runtime-control migration is present.
- Supabase security advisor returned no findings in the 2026-09-24 check.
- Generic table listing warns that several public reference/system tables do not have RLS enabled, but direct `information_schema.role_table_grants` inspection returned no `anon` or `authenticated` public-table grants. This is not permission to weaken controls or expose those tables; any future RLS/grant change must preserve current least-privilege behavior and be migration/test backed.

## Production activation gates

- **Frontend deployment drift:** authenticated Cloudflare dashboard access is required to inspect/deploy the existing `rivexis-web` production project and then re-certify the live workspace/auth boundary.
- **FastAPI runtime:** explicit approval for Workers Paid or another already-approved FastAPI-capable production path is still required; do not replace FastAPI with a fake Worker implementation.
- **Custom domain:** user domain choice/ownership remains unresolved.
- **Brevo transactional email:** phone/account verification is not the current blocker. Code integration, environment contract, owned-domain/sender authentication, production credentials and delivery certification remain outstanding.
- **Providers:** production credentials/licenses/customer contracts are still required where applicable; unavailable capabilities must remain explicit.
- **Release certification:** complete real-target deployment/browser/provider/email evidence remains outstanding.
