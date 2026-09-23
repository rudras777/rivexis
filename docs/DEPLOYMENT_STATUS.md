# Rivexis Deployment Status

Last updated: 2026-09-24

| Environment | Status | Evidence / meaning |
|---|---|---|
| Local development | AVAILABLE, NOT VERIFIED IN THIS CHAT | Repository contains SQLite/local and Docker/PostgreSQL development paths. No local shell execution was used for this update. |
| GitHub CI | PASS FOR CURRENT IMPLEMENTATION HEAD | Implementation head `c9baf68a045b194b9c8adb1557ac77091ae20b00` passed full CI #328 (`35928391144`): API ruff/pytest/pip-audit, web type/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and real PostgreSQL migration/runtime-control certification. |
| Free frontend preview | LIVE, DEPLOYMENT DRIFT DETECTED | `https://rivexis-web.rudrasingh0718.workers.dev` was previously reachable with public pages working, but unauthenticated `/workspace` showed an older generic/demo-safe shell rather than current-main access-withholding behavior. No private user/analysis data was observed. Current-main source is not claimed live. |
| Free API preview | LIVE / DEGRADED BY DESIGN | `https://rivexis-api.rudrasingh0718.workers.dev/health` previously reported the intentional degraded state because the approved free-tier stack does not host the authoritative FastAPI runtime. |
| Supabase PostgreSQL | ACTIVE_HEALTHY AT LAST VERIFIED CHECK | Project `ivszvufdonfgwjpfgwii`, region `ap-south-1`, PostgreSQL 17.6.1; prior direct grant/security checks preserved least-privilege behavior. |
| Brevo transactional layer | IMPLEMENTED, NOT ACTIVATED | Fail-closed transport/environment contract are implemented and CI-certified. Verification/reset templates 1 and 2 exist but remain intentionally inactive. Owned-domain sender authentication, runtime secrets, sandbox/real-delivery and lifecycle-event certification remain outstanding. |
| Staging | PARTIAL | Supabase exists, but there is no independently certified live FastAPI staging runtime with complete provider/browser/email evidence. |
| Production | BLOCKED | Frontend deployment parity is unverified, authoritative FastAPI runtime is absent, custom domain is unresolved, Brevo production sender/delivery certification is incomplete, and the release certification campaign is incomplete. |

## Current deployed topology

- **Web:** existing Cloudflare Worker `rivexis-web` via vinext, but deployed commit/Git-main parity is not currently verified.
- **API hostname:** Cloudflare Worker `rivexis-api`.
- **API free-tier behavior:** explicit degraded health/application boundary; it is not a substitute for FastAPI.
- **Database:** Supabase PostgreSQL.
- **Distributed runtime controls:** PostgreSQL-backed path is implemented, migrated and repeatedly CI-certified; Redis remains optional.
- **Email:** Brevo account verification is recorded complete and the repository has a fail-closed transactional transport plus inactive auth templates. Production delivery remains uncertified.
- **Custom domain:** none verified/configured for production in this build state.

## Current milestone verification

Milestone F remains active. The latest continuation hardened three additional deterministic boundaries without claiming unavailable provider depth:

- **F1:** engine `1.2.0`, calculation generation `f1-live-1.3.0`. One captured `eth_blockNumber` now pins every requested native/ERC-20 holdings read; evidence records the actual block tag used. CI #322 (`35927503622`) PASS and the same slice is included in final CI #328.
- **B1:** engine `1.3.0`. ABI decoding rejects non-canonical address high padding, non-0/1 booleans, narrow-integer overflow/sign-extension errors and non-zero fixed-bytes padding. Malformed approval-shaped calldata is not promoted into approval candidates. Final CI #328 PASS.
- **B4:** engine `1.0.0`. Direct native balance now uses the exact captured RPC block tag rather than `latest`, so block-stamped evidence and the actual RPC state are consistent. Final CI #328 PASS.

Prior B5/F4/F5/F2 hardening remains preserved. All ten engines retain targeted repository-level contract/input/provider/freshness integrity coverage. Remaining Milestone F work is capability depth requiring approved evidence sources or further deterministic implementation; this is not a claim that all engines are production-complete.

## Live browser / Cloudflare verification — retained state

Earlier browser verification established that homepage, login, signup, platform and security pages were reachable and the API health endpoint truthfully reported degraded runtime state. It also discovered the unauthenticated `/workspace` deployment drift described above.

The most recent Cloudflare dashboard attempt redirected to account sign-in and no authenticated Cloudflare browser session was available. During this continuation, a plugin-directory check also returned no callable Cloudflare plugin. Consequently:

- existing `rivexis-web` project details could not be inspected;
- GitHub repository/branch integration could not be verified;
- deployed commit/version could not be verified;
- no production deployment was triggered;
- no DNS, custom-domain, billing/plan, environment-variable, secret, route, API Worker or project setting was changed.

The deployment drift remains a P1 live-certification blocker.

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

- **Frontend deployment drift:** authenticated Cloudflare access is required to inspect/deploy the established `rivexis-web` project and re-certify live auth/workspace behavior.
- **FastAPI runtime:** explicit approval for Workers Paid or another approved FastAPI-capable production path is required; do not replace FastAPI with a fake Worker implementation.
- **Custom domain:** domain choice/ownership/configuration remains unresolved.
- **Brevo:** phone/account verification is not the blocker; owned-domain sender authentication, secrets and delivery-lifecycle certification remain outstanding.
- **Providers:** production credentials/licenses/customer contracts are still required where applicable; unavailable capabilities must remain explicit.
- **Release certification:** complete real-target deployment/browser/provider/email evidence remains outstanding.
