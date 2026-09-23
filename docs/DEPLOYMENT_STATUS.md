# Rivexis Deployment Status

Last updated: 2026-09-24

| Environment | Status | Evidence / meaning |
|---|---|---|
| Local development | AVAILABLE, NOT VERIFIED IN THIS CHAT | Repository contains SQLite/local and Docker/PostgreSQL development paths. No local shell execution was used for this update. |
| GitHub repository | PUBLIC / MAIN ACTIVE | `rudras777/rivexis` is currently public. The newer GitHub Pages fallback files are preserved on `main`. |
| GitHub CI | PASS FOR CURRENT IMPLEMENTATION HEAD | Implementation head `c5f9b083229e61297375f0c02ded6cc1ecdbada9` passed full CI #340 (`35931269784`): API ruff/pytest/pip-audit, web type/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and PostgreSQL migration/runtime-control certification. |
| GitHub Pages fallback | ENABLED / NOT APPLICATION CERTIFICATION | Repository Pages is enabled and the root fallback/navigation files are present. This does not establish parity with the Cloudflare Next.js deployment or provide the authoritative FastAPI runtime. |
| Free Cloudflare frontend preview | LIVE, DEPLOYMENT DRIFT DETECTED | `https://rivexis-web.rudrasingh0718.workers.dev` was previously reachable with public pages working, but unauthenticated `/workspace` showed an older generic/demo-safe shell rather than current-main access-withholding behavior. No private user/analysis data was observed. Current-main source is not claimed live there. |
| Free API preview | LIVE / DEGRADED BY DESIGN | `https://rivexis-api.rudrasingh0718.workers.dev/health` previously reported the intentional degraded state because the approved free-tier stack does not host the authoritative FastAPI runtime. |
| Supabase PostgreSQL | ACTIVE_HEALTHY AT LAST VERIFIED CHECK | Project `ivszvufdonfgwjpfgwii`, region `ap-south-1`, PostgreSQL 17.6.1; prior direct grant/security checks preserved least-privilege behavior. |
| Brevo transactional layer | IMPLEMENTED, NOT ACTIVATED | Fail-closed transport/environment contract are implemented and CI-certified. Verification/reset templates 1 and 2 exist but remain intentionally inactive. Owned-domain sender authentication, runtime secrets, sandbox/real-delivery and lifecycle-event certification remain outstanding. |
| Staging | PARTIAL | Supabase exists, but there is no independently certified live FastAPI staging runtime with complete provider/browser/email evidence. |
| Production | BLOCKED | Cloudflare frontend parity is unverified, authoritative FastAPI runtime is absent, custom domain is unresolved, Brevo production sender/delivery certification is incomplete, and the release certification campaign is incomplete. |

## Current deployed topology

- **Public repository/Pages:** GitHub repository is public and Pages fallback/navigation files exist. This surface is not the production application runtime.
- **Web application:** existing Cloudflare Worker `rivexis-web` via vinext, but deployed commit/Git-main parity is not currently verified.
- **API hostname:** Cloudflare Worker `rivexis-api`.
- **API free-tier behavior:** explicit degraded health/application boundary; it is not a substitute for FastAPI.
- **Database:** Supabase PostgreSQL.
- **Distributed runtime controls:** PostgreSQL-backed path is implemented, migrated and repeatedly CI-certified; Redis remains optional.
- **Email:** Brevo account verification is recorded complete and the repository has a fail-closed transactional transport plus inactive auth templates. Production delivery remains uncertified.
- **Custom domain:** none verified/configured for production in this build state.

## Current Milestone F verification

The latest bulk campaign hardened four additional trust boundaries and passed final CI #340:

- **B2:** engine `1.1.0`, calculation `b2-live-1.2.0`. Contract bytecode is validated and observed at the captured block; approval decoding reuses canonical calldata rules; malformed transaction/code state remains explicit.
- **B3:** engine `1.1.0`, calculation `b3-live-1.2.0`. Native balance, runtime code, optional token supply and supplied Chainlink state all share one captured block tag; future/stale timestamp semantics remain fail-closed.
- **F3:** engine `1.3.0`, calculation `f3-live-1.3.0`. Modeled quantities/debt price reject bool/non-finite economics; Chainlink ABI/price/timestamp evidence validates and is block-pinned; CoinGecko comparison price/timestamp evidence is independently normalized.
- **F2:** engine `1.2.0`, calculation `f2-live-1.3.0`. Boolean provider TVL/timestamp fields can no longer masquerade as numeric protocol evidence; audit metadata protections remain preserved.

Earlier F1/B1/B4 and B5/F4/F5 hardening remains intact. All ten engines retain targeted repository-level input/provider/freshness/runtime integrity coverage. Remaining Milestone F work is capability depth rather than a claim that all engines are production-complete.

## Live browser / Cloudflare verification — retained state

Earlier browser verification established that homepage, login, signup, platform and security pages were reachable and the API health endpoint truthfully reported degraded runtime state. It also discovered the unauthenticated `/workspace` Cloudflare deployment drift described above.

The most recent Cloudflare dashboard attempt redirected to account sign-in and no authenticated Cloudflare browser session was available. A plugin-directory check also returned no callable Cloudflare plugin. Consequently:

- existing `rivexis-web` project details could not be inspected;
- GitHub repository/branch integration could not be verified;
- deployed Cloudflare commit/version could not be verified;
- no Cloudflare production deployment was triggered;
- no DNS, custom-domain, billing/plan, environment-variable, secret, route, API Worker or project setting was changed.

The GitHub Pages fallback does not resolve this P1 Cloudflare live-certification blocker.

## Supabase verification notes retained

- Last verified project state: `ACTIVE_HEALTHY`.
- PostgreSQL engine: 17.6.1.
- Runtime-control migrations are present and the same migration/runtime-control path continues to pass CI.
- Prior security-advisor inspection returned no findings.
- Prior direct grants inspection found no `anon` or `authenticated` public-table grants. Generic non-RLS warnings are not permission to weaken controls; any future RLS/grant change must remain migration/test backed.

## Brevo production state

- Owner-side phone/account verification is complete.
- SMTP relay and an active sender were verified; the observed sender is Gmail and is not evidence of an authenticated Rivexis-owned domain.
- Template `1` — account verification code — inactive.
- Template `2` — password reset — inactive.
- Repository transport treats provider send success only as `accepted`/`sandbox_accepted`, never as proof of delivery.
- No production verification/reset endpoint is exposed and no real auth mail was sent during this build campaign.
- Activation remains gated on owned-domain sender authentication, production runtime secret installation, sandbox certification, controlled real delivery and transactional delivered/bounced/failed lifecycle evidence.

## Production activation gates

- **Cloudflare frontend deployment drift:** authenticated Cloudflare access is required to inspect/deploy the established `rivexis-web` project and re-certify live auth/workspace behavior.
- **FastAPI runtime:** explicit approval for Workers Paid or another approved FastAPI-capable production path is required; do not replace FastAPI with a fake Worker implementation.
- **Custom domain:** domain choice/ownership/configuration remains unresolved.
- **Brevo:** phone/account verification is not the blocker; owned-domain sender authentication, secrets and delivery-lifecycle certification remain outstanding.
- **Providers:** production credentials/licenses/customer contracts are still required where applicable; unavailable capabilities must remain explicit.
- **Release certification:** complete real-target deployment/browser/provider/email evidence remains outstanding.
