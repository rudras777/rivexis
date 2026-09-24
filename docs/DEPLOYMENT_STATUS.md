# Rivexis Deployment Status

Last updated: 2026-09-24

| Environment | Status | Evidence / meaning |
|---|---|---|
| Local development | AVAILABLE, NOT VERIFIED IN THIS CHAT | Repository contains SQLite/local and Docker/PostgreSQL development paths. No local shell execution was used for this update. |
| GitHub repository | PUBLIC / MAIN ACTIVE | `rudras777/rivexis` is currently public. The GitHub Pages fallback files are preserved on `main`. |
| GitHub CI | PASS FOR LATEST APPLICATION HEAD | `7a5f6aa284b35f8388915788ce1f444410f5ae4d` passed full CI #358 (`35977258512`): API ruff/pytest/pip-audit, web type/build/vinext/npm-audit/Playwright E2E, invariants/secret/migration checks, and PostgreSQL migration/runtime-control certification. |
| GitHub Pages fallback | ENABLED / PASSING / NOT APPLICATION CERTIFICATION | Pages deployment #29 (`35977258067`) passed on the same application head. This does not establish parity with the Cloudflare Next.js deployment or provide the authoritative FastAPI runtime. |
| Free Cloudflare frontend preview | LIVE / CURRENT APPLICATION SOURCE | `https://rivexis-web.rudrasingh0718.workers.dev` serves Worker version `258a0507-177e-43ae-84da-ebc037d29d03`, rebuilt from application head `e6e8fea6162ae6b00e3915a165423096ab404aba`. Unauthenticated `/workspace` now withholds protected content. Preview URLs are disabled. |
| Free API preview | LIVE / DEGRADED BY DESIGN | `https://rivexis-api.rudrasingh0718.workers.dev/health` returns HTTP 200 with explicit `degraded` state; application/auth endpoints return 503 because the approved free-tier stack does not host the authoritative FastAPI runtime. |
| Supabase PostgreSQL | ACTIVE_HEALTHY / SCHEMA VERIFIED | Project `ivszvufdonfgwjpfgwii`, region `ap-south-1`, PostgreSQL 17.6.1; 55 application tables and migration `0011_postgres_runtime_controls` verified. Security advisors returned no findings and `anon`/`authenticated` have no public-table grants. |
| Brevo transactional layer | IMPLEMENTED, NOT ACTIVATED | Fail-closed transport/environment contract are implemented and CI-certified. Verification/reset templates 1 and 2 remain intentionally inactive. Owned-domain sender authentication, runtime secrets, sandbox/real-delivery and lifecycle-event certification remain outstanding. |
| Staging | PARTIAL | Supabase exists, but there is no independently certified live FastAPI staging runtime with complete provider/browser/email evidence. |
| Production | PARTIAL / BLOCKED ON APPLICATION RUNTIME | Cloudflare frontend parity is repaired. The authoritative FastAPI runtime is absent, custom domain is unresolved, Brevo production sender/delivery certification is incomplete, and the release certification campaign is incomplete. |

## Current deployed topology

- **Public repository/Pages:** GitHub repository is public and Pages fallback/navigation files deploy successfully. This surface is not the production application runtime.
- **Web application:** Cloudflare Worker `rivexis-web` via vinext; current application head is deployed as version `258a0507-177e-43ae-84da-ebc037d29d03` at 100% traffic.
- **API hostname:** Cloudflare Worker `rivexis-api`.
- **API free-tier behavior:** explicit degraded health/application boundary; it is not a substitute for FastAPI.
- **Database:** Supabase PostgreSQL.
- **Distributed runtime controls:** PostgreSQL-backed path is implemented, migrated and repeatedly CI-certified; Redis remains optional.
- **Email:** Brevo account verification is recorded complete and the repository has a fail-closed transactional transport plus inactive auth templates. Production delivery remains uncertified.
- **Custom domain:** none verified/configured for production in this build state.

## Current Milestone F verification

The latest certified continuation added F1 ERC-20 direct-state integrity on top of the prior B1/B4 work:

- **F1:** engine `1.2.0`, calculation `f1-live-1.4.0`. Explicit ERC-20 `decimals()` and `balanceOf(address)` reads share the captured RPC block; both must decode from canonical 32-byte ABI uint256 return words. Caller decimals must match on-chain decimals before raw balance scaling, generic block/native quantities are uint256-bounded, and mismatch/malformed state fails closed before valuation. Direct token-metadata evidence records the verified decimals at the captured block. Contract/symbol/CoinGecko identity remains caller-supplied rather than falsely “discovered.” Certified in CI #358 on `7a5f6aa284b35f8388915788ce1f444410f5ae4d`; Pages #29 also passed.
- **B1:** verified-ABI dynamic `bytes`/`string` and supported static-element dynamic arrays are bounded/canonical. Invalid offsets, tail lengths, padding and elements fail closed; unsupported tuple/fixed/nested composite layouts are explicit. Certified in CI #350 on `2d0e2338e75114089e94c8623bb76fe7c8d79bf5`.
- **B4:** direct native-balance evidence remains LIVE and block-pinned, while Etherscan/Nansen/Arkham evidence without provider-specific block/timestamp provenance no longer inherits the direct RPC block or a global LIVE freshness claim. External evidence is `UNKNOWN`, aggregate freshness is `UNKNOWN` when it is consumed, and the direct snapshot remains separately `LIVE` with `direct_state_block_number`. Certified in CI #353 on `61b728edf259ccafda256f2ab6f221e918e1f0ef`.

Earlier B2/B3/F3/F2, F1/B1/B4 and B5/F4/F5 hardening remains intact. All ten engines retain targeted repository-level input/provider/freshness/runtime integrity coverage. Remaining Milestone F work is capability depth rather than a claim that all engines are production-complete.

## Live browser / Cloudflare verification — 2026-09-24

Cloudflare account/API and dashboard inspection identified two Workers, no Pages projects, no custom Worker domains and no custom routes. `rivexis-web` has only the `ASSETS` binding; `rivexis-api` has no bindings or secrets and remains the intentional degraded placeholder.

Current application source was built with `NEXT_PUBLIC_RIVEXIS_API_URL=https://rivexis-api.rudrasingh0718.workers.dev` and deployed to `rivexis-web`. Live checks passed for `/`, `/login`, `/signup`, `/workspace`, `/platform`, `/security`, `/methodology` and `/defi-risk`; an unknown route returned 404. Unauthenticated `/workspace` now displays `Application services unavailable` and withholds protected navigation/content. A safe invalid-login probe produced `Authentication service is temporarily unavailable`; the browser console had no warnings or errors. Worker preview URLs were explicitly disabled after deployment and verified disabled through the Cloudflare API.

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

- **Cloudflare frontend deployment drift:** RESOLVED. Current application source is deployed and live behavior is re-certified; CI/CD remains manual rather than repository-connected.
- **FastAPI runtime:** explicit approval for Workers Paid or another approved FastAPI-capable production path is required; do not replace FastAPI with a fake Worker implementation.
- **Custom domain:** domain choice/ownership/configuration remains unresolved.
- **Brevo:** phone/account verification is not the blocker; owned-domain sender authentication, secrets and delivery-lifecycle certification remain outstanding.
- **Providers:** production credentials/licenses/customer contracts are still required where applicable; unavailable capabilities must remain explicit.
- **Release certification:** complete real-target deployment/browser/provider/email evidence remains outstanding.
