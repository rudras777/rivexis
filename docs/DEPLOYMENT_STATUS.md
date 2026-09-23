# Rivexis Deployment Status

Last updated: 2026-09-24

| Environment | Status | Evidence / meaning |
|---|---|---|
| Local development | AVAILABLE, NOT VERIFIED IN THIS CHAT | Repository contains SQLite/local and Docker/PostgreSQL development paths. No local shell execution was used for this update. |
| GitHub repository | PUBLIC / MAIN ACTIVE | `rudras777/rivexis` is currently public. The GitHub Pages fallback files are preserved on `main`. |
| GitHub CI | PASS FOR LATEST APPLICATION HEAD | `61b728edf259ccafda256f2ab6f221e918e1f0ef` passed full CI #353 (`35934430946`): API ruff/pytest/pip-audit, web type/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and PostgreSQL migration/runtime-control certification. |
| GitHub Pages fallback | ENABLED / PASSING / NOT APPLICATION CERTIFICATION | Pages deployment #24 (`35934430378`) passed on the same application head. This does not establish parity with the Cloudflare Next.js deployment or provide the authoritative FastAPI runtime. |
| Free Cloudflare frontend preview | LIVE, DEPLOYMENT DRIFT DETECTED | `https://rivexis-web.rudrasingh0718.workers.dev` was previously reachable with public pages working, but unauthenticated `/workspace` showed an older generic/demo-safe shell rather than current-main access-withholding behavior. No private user/analysis data was observed. Current-main source is not claimed live there. |
| Free API preview | LIVE / DEGRADED BY DESIGN | `https://rivexis-api.rudrasingh0718.workers.dev/health` previously reported the intentional degraded state because the approved free-tier stack does not host the authoritative FastAPI runtime. |
| Supabase PostgreSQL | ACTIVE_HEALTHY AT LAST VERIFIED CHECK | Project `ivszvufdonfgwjpfgwii`, region `ap-south-1`, PostgreSQL 17.6.1; prior direct grant/security checks preserved least-privilege behavior. |
| Brevo transactional layer | IMPLEMENTED, NOT ACTIVATED | Fail-closed transport/environment contract are implemented and CI-certified. Verification/reset templates 1 and 2 remain intentionally inactive. Owned-domain sender authentication, runtime secrets, sandbox/real-delivery and lifecycle-event certification remain outstanding. |
| Staging | PARTIAL | Supabase exists, but there is no independently certified live FastAPI staging runtime with complete provider/browser/email evidence. |
| Production | BLOCKED | Cloudflare frontend parity is unverified, authoritative FastAPI runtime is absent, custom domain is unresolved, Brevo production sender/delivery certification is incomplete, and the release certification campaign is incomplete. |

## Current deployed topology

- **Public repository/Pages:** GitHub repository is public and Pages fallback/navigation files deploy successfully. This surface is not the production application runtime.
- **Web application:** existing Cloudflare Worker `rivexis-web` via vinext, but deployed commit/Git-main parity is not currently verified.
- **API hostname:** Cloudflare Worker `rivexis-api`.
- **API free-tier behavior:** explicit degraded health/application boundary; it is not a substitute for FastAPI.
- **Database:** Supabase PostgreSQL.
- **Distributed runtime controls:** PostgreSQL-backed path is implemented, migrated and repeatedly CI-certified; Redis remains optional.
- **Email:** Brevo account verification is recorded complete and the repository has a fail-closed transactional transport plus inactive auth templates. Production delivery remains uncertified.
- **Custom domain:** none verified/configured for production in this build state.

## Current Milestone F verification

The latest certified continuation added two deterministic integrity/depth improvements:

- **B1:** verified-ABI dynamic `bytes`/`string` and supported static-element dynamic arrays are now bounded/canonical. Invalid offsets, tail lengths, padding and elements fail closed; unsupported tuple/fixed/nested composite layouts are explicit. Certified in CI #350 on `2d0e2338e75114089e94c8623bb76fe7c8d79bf5`.
- **B4:** direct native-balance evidence remains LIVE and block-pinned, while Etherscan/Nansen/Arkham evidence without provider-specific block/timestamp provenance no longer inherits the direct RPC block or a global LIVE freshness claim. External evidence is `UNKNOWN`, aggregate freshness is `UNKNOWN` when it is consumed, and the direct snapshot remains separately `LIVE` with `direct_state_block_number`. Certified in CI #353 on `61b728edf259ccafda256f2ab6f221e918e1f0ef`.

Earlier B2/B3/F3/F2, F1/B1/B4 and B5/F4/F5 hardening remains intact. All ten engines retain targeted repository-level input/provider/freshness/runtime integrity coverage. Remaining Milestone F work is capability depth rather than a claim that all engines are production-complete.

## Live browser / Cloudflare verification — 2026-09-24

Earlier browser verification established that homepage, login, signup, platform and security pages were reachable and the API health endpoint truthfully reported degraded runtime state. It also discovered the unauthenticated `/workspace` Cloudflare deployment drift described above.

A fresh Cloudflare dashboard automation was run against `https://dash.cloudflare.com/` using the available saved browser profile and vault. The run completed without authenticating and returned the explicit blocker that no Cloudflare credentials are configured for the available browser account/profile. Consequently:

- existing `rivexis-web` project details could not be inspected;
- GitHub repository/branch integration could not be verified;
- deployed Cloudflare commit/version could not be verified;
- no Cloudflare production deployment was triggered;
- no DNS, custom-domain, billing/plan, environment-variable, secret, route, API Worker or project setting was changed.

A plugin-directory recheck also returned no callable native Cloudflare plugin in this chat runtime. The GitHub Pages fallback does not resolve this P1 Cloudflare live-certification blocker.

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

- **Cloudflare frontend deployment drift:** authenticated Cloudflare access is required to inspect/deploy the established `rivexis-web` project and re-certify live auth/workspace behavior. The latest browser profile does not contain usable Cloudflare credentials.
- **FastAPI runtime:** explicit approval for Workers Paid or another approved FastAPI-capable production path is required; do not replace FastAPI with a fake Worker implementation.
- **Custom domain:** domain choice/ownership/configuration remains unresolved.
- **Brevo:** phone/account verification is not the blocker; owned-domain sender authentication, secrets and delivery-lifecycle certification remain outstanding.
- **Providers:** production credentials/licenses/customer contracts are still required where applicable; unavailable capabilities must remain explicit.
- **Release certification:** complete real-target deployment/browser/provider/email evidence remains outstanding.
