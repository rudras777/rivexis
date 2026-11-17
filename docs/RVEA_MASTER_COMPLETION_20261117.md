# RVEA master-prompt completion record — 17 November 2026

This reconciles the original migration prompt with actual evidence. The existing Wix portfolio, original RIVEXIS Worker, Supabase project and production data remain in place. Historical acceptance is dated explicitly; an unavailable product capability is not described as a successful live test.

## Architecture and current observations

| Requirement | Status and evidence |
|---|---|
| Root and WWW retain the Wix portfolio | **Publicly verified 17 November:** root redirects to WWW; both return HTTPS 200, Rudra Singh identity and the intended title |
| Custom hostname serves the original application | **Publicly verified 17 November:** custom and original Worker landing HTML have identical hashes and build `1212d5d776b589ce77360009400a8ccbb678865f`, the release before this audit note |
| Normal HTTPS | All 32 public probes used normal certificate verification; no bypass or hosts-file override |
| Wix remains authoritative | Authoritative Wix queries, local DNS and Google DNS agree on `ns4.wixdns.net`, `ns5.wixdns.net`, original three apex A values, WWW CNAME and the single RIVEXIS CNAME |
| Gateway invokes the original Worker | Production and preview gateway status report ready; preview public reads work and API/credential probes return 403. Eight gateway regressions passed locally |
| Production deployment configuration | Main CI, Worker-bundle and Workers Builds checks passed for the release above. PR119/120 are merged; superseded PR118 is closed; PR139 is merged |
| Supabase connectivity and data safeguards | **Verified 17 November:** ACTIVE_HEALTHY; all 61 public tables have RLS; zero client-accessible no-policy tables, zero client-callable public security-definer functions and zero API roles with database LOGIN |
| Retained identities | Auth user count remains 10, matching the prior completion checkpoint; no user, schema or workspace was created or deleted in this recheck. Counts alone are not row-by-row preservation proof |
| Portfolio pages | Home, About, Projects, Research, Experience, Resume and Contact returned 200 today; desktop/mobile rendering, title/description and H1 checks were completed on 13 November |

Runtime metadata changes with later documentation/build commits. After any merge, read the actual public `rivexis-build` and `/health`; do not treat the pre-audit SHA above as a permanent current-release claim.

## Authentication and transactional email

- **Implemented and deployed:** custom Supabase Site URL, exact confirmation/recovery callbacks, retained legacy callback, trusted origins, host-only Secure/HttpOnly cookies, CSRF controls and restricted CORS. The complete configuration and source readback are in [the production runbook](RVEA_PRODUCTION_RUNBOOK.md).
- **Actually tested 29 October:** approved signup accounts, fresh code-based email verification through the real browser form, verified login, identity/session persistence, logout and protected-route behavior. Recovery delivery, two safe GET handoffs, native reset POST, new-password login, refresh-session revocation and replay rejection passed. Browser password submission was not performed.
- **Actually tested 13 November:** twenty real authentication-link cases across both hosts and the normal QA logout boundary. PR139 passed 352 fixture cases in each of Chromium, Firefox and WebKit; fixture counts are not live customer tests.
- **Freshly verified 17 November:** one recovery request for the previously approved, existing QA alias returned 202. Its message reached Gmail within seconds with SPF, DKIM and DMARC passing. The Brevo dashboard subsequently showed Sent and Delivered events. No password was changed, recovery token consumed or new account created.
- The sender still uses the existing authenticated Brevo rewrite. This is not a claim that `rvea.info` is an authenticated sending domain.
- The address reported as missing signup mail was already verified in the targeted 13 November review. It should use login/recovery; a new device does not require another signup email. Do not recreate that identity or disable confirmation.

## Existing DNS and infrastructure

| Record | Preserved value |
|---|---|
| Apex A | `185.230.63.171`, `185.230.63.186`, `185.230.63.107` |
| WWW CNAME | `cdn3.wixdns.net` |
| RIVEXIS CNAME | `rvea-rivexis-gateway.pages.dev` |
| Authoritative NS | `ns4.wixdns.net`, `ns5.wixdns.net` |
| Existing Worker / Pages project | `rivexis-web` / `rvea-rivexis-gateway` |
| Service binding | `RIVEXIS_WEB` to original `rivexis-web` |
| Existing Cloudflare account | `0b22778ba197266a58dd26eeef0334a8` |
| Existing Supabase project | `ivszvufdonfgwjpfgwii`, `ap-south-1` |

The pending Full Cloudflare zone is not required for this externally hosted DNS subdomain. No apex/WWW/NS/mail record, Wix assignment, subscription, paid plan or future-project deployment changed in this recheck. Cloudflare's [subdomain custom-domain](https://developers.cloudflare.com/pages/configuration/custom-domains/) and [service-binding](https://developers.cloudflare.com/pages/functions/bindings/) documentation supports this architecture.

## Repeatable Cloudflare configuration audit

The [rvea-production-audit workflow](../.github/workflows/rvea-production-audit.yml) runs only from trusted `main`, manually or when its own reviewed code changes, with repository contents-read permission. It uses the two existing encrypted deployment credentials, with no new token, principal or permission grant. The audit makes three fixed GET requests: the existing Pages project, its custom domains and the existing Worker's deployments. Redirects are refused. Its code performs no deployment, binding update, DNS write, resource creation or email send.

[The audit script](../scripts/audit-rvea-cloudflare.mjs) emits only allowlisted deployment IDs, binding targets, domain/certificate status, compatibility date, fail-open value and active Worker traffic allocation. Complete provider responses, environment values, token values, analytics credentials and author identities are excluded. Regression tests exercise redaction, fixed destinations/methods, malformed credentials, sanitized failures and configuration mismatches. The report is retained for seven days as an Actions artifact. Run it for fresh provider identifiers instead of copying old version IDs from an earlier checkpoint.

The 17 November public recheck's Google DNS and authoritative Wix queries passed. Python's optional Cloudflare DNS-over-HTTPS requests failed local issuer-certificate validation; those failures were retained and certificate verification was not disabled. All actual website TLS checks passed.

## Boundaries that must remain explicit

| Item | Honest status / exact next action |
|---|---|
| Live oracle and generic engine coverage | Some existing adapters/providers remain unsupported or unconfigured. Validate the original adapter contracts and evidence with the product owner before enabling additional outputs; a new RPC URL alone does not implement them |
| Continuous DeFi alert email | Existing capability remains disabled. It needs a separately reviewed product implementation and real acceptance; it was not invented as part of a DNS migration |
| Wallet acceptance | Selector was exercised; no compatible injected provider was available in the recorded acceptance. Retest with an owner-selected wallet/browser, stopping before signing or transactions |
| Browser password-reset submit | Safe browser handoff and actual reset API were tested separately. Final browser password submission is an owner-only acceptance step; never ask for a password/code in chat |
| Supabase advisories | Nineteen no-policy notices remain informational with no effective client table grants. `pg_net` is non-relocatable; do not blindly move/drop it. Leaked-password protection remains disabled; no paid upgrade is authorized |
| Owner recovery codes / backup MFA | Custody was not completed by the agent. The owner should privately finish/confirm setup in Account Security; no code, seed or new password should enter source, logs or this report |
| Dashboard/connector access | Wix connector requires reconnection; Brevo connector failed internally, so its existing authenticated dashboard was used. Cloudflare browser requires sign-in; the scoped read-only Actions audit provides the configuration check without automating authentication dialogs |

These are not hidden successes. The migration's domain, ingress, deployment, account and mail integrations have actual acceptance evidence; broader product coverage and owner-held security material cannot be called universally complete.

## Rollback and future projects

Use [the production runbook's rollback and future-project procedures](RVEA_PRODUCTION_RUNBOOK.md). Preserve the root portfolio, Wix NS/assignment and all existing data. Roll back only the failing layer: an accepted existing Worker version, the Pages deployment, or the exact RIVEXIS CNAME/custom-domain mapping. Keep the original Worker URL and legacy callbacks available. Never restore a database or switch nameservers to repair an ingress issue.

The audit workflow itself is read-only; reverting its source removes an operational check without changing production settings. Its output is a snapshot, not a deployment instruction. Future `<project>.rvea.info` services require their own reviewed preview, exact hostname association, minimal Wix record, origin/callback/cookie boundaries and rollback. No speculative Qelly or wildcard deployment is needed.
