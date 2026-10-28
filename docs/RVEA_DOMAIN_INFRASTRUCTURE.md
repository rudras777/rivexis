# RVEA Domain Infrastructure — Migration Inventory and Release Gate
_Observed 2026-10-29 (Asia/Kolkata). This is a **read-only audit checkpoint**, not a completed deployment certificate._

## Approved public namespace

| Hostname | Purpose | Required destination | Current production verification |
| --- | --- | --- | --- |
| `https://rvea.info` | Rudra Singh personal portfolio | Existing Wix website, unchanged | **Unverified** from available live DNS/browser access |
| `https://www.rvea.info` | Portfolio alias | Same Wix website or established Wix canonical redirect | **Unverified** |
| `https://rivexis.rvea.info` | RIVEXIS platform | Existing Cloudflare Worker `rivexis-web` | **Not attached or verified in this audit** |
| `https://rivexis-web.rudrasingh0718.workers.dev` | Existing application / migration rollback | Same existing Worker | Source-referenced; live response not verified in this audit |
| `<future-project>.rvea.info` | New projects | Project-specific host, created only when needed | Convention only; no wildcard DNS |

Do **not** migrate/rebuild Wix, create another Worker, rename projects, purchase domains, or deploy placeholder subdomains.

## Confirmed connected project resources

- GitHub repository: `rudras777/rivexis`, default branch `main`.
- Existing web Worker: `rivexis-web` according to `apps/web/wrangler.jsonc` and the root `wrangler.jsonc`.
- Existing Cloudflare API Worker configuration: `apps/api/cloudflare/wrangler.jsonc`, separate from the web Worker. Never attach the RIVEXIS web hostname to the wrong Worker.
- Supabase project: `Rivexis` (`ivszvufdonfgwjpfgwii`), `ap-south-1`; observed project state `ACTIVE_HEALTHY`. No database or auth mutation was made for this checkpoint.
- Existing application authentication: FastAPI endpoints under `/api/v1/auth`, account records in application tables, and Brevo transactional email integration; this is **not proven to be hosted Supabase Auth**. See `apps/api/rivexis_api/services/auth_email.py`. Do not blindly change Supabase Auth settings in place of the application's actual URL/origin configuration.
- `RIVEXIS_PUBLIC_WEB_URL` is used to build password-reset destinations. Existing production environment value must be obtained from deployment settings (not inferred from the example configuration).
- Brevo account/sender/domain inventory could not be obtained through the current connected endpoint; sender or template changes are **not verified**.

## Required authoritative DNS/Wix inventory before any write

Not yet verified: registrar nameserver delegation, Wix current connection method, Cloudflare zone activation and assigned nameservers, complete `A/AAAA/CNAME/MX/TXT/CAA/SRV/NS/DS` records, SPF/DKIM/DMARC, Wix-specific pointing values, root/WWW canonical behavior, active redirects and certificates.

1. Domain owner confirms registrant verification is complete via their registrar/Wix account.
2. Export or record the **full current authoritative DNS zone** and domain connection settings. Include DNSSEC/DS and all email/verification records.
3. Inspect Wix's exact current A/CNAME pointing instructions for the existing site. Do not fabricate values.
4. Confirm whether Cloudflare is already authoritative. Cloudflare custom domains require an **active zone**.
5. If nameserver migration is needed, prepare the complete Cloudflare zone, record an explicit rollback, check existing DS state, and obtain any required registrar approval **before** changing delegation.
6. Use **DNS Only / unproxied** for the Wix-pointing A/CNAME records where Wix requires it. Keep the apex exclusively on the Wix portfolio.
7. Avoid conflicting `rivexis` CNAME records: Cloudflare Workers **Custom Domain** provisions its own DNS and TLS.

## Cloudflare Worker custom-domain activation

After zone and DNS safety gates are satisfied:

1. Open Cloudflare Workers & Pages → existing `rivexis-web` → Settings → Domains & Routes.
2. Add **Custom Domain** `rivexis.rvea.info` to this Worker; do **not** create a new Worker or attach `rvea.info`.
3. Confirm automatically managed DNS, certificate issuance, correct route handling, and uninterrupted `workers.dev` fallback.
4. Validate main page, `/login`, `/signup`, `/forgot-password`, `/reset-password`, `/verify-email`, authenticated `/workspace`, `/gasguard`, `/liquidationguard`, API relay, and API/Edge-origin behavior.

## Auth, transactional email, and security migration

After the custom hostname is actually reachable:

1. Inspect production bindings/secrets **by key name only** (never copy values into this document). Set the existing service's `RIVEXIS_PUBLIC_WEB_URL` to `https://rivexis.rvea.info` only when new-domain cutover is ready.
2. Audit `RIVEXIS_ALLOWED_ORIGINS`, CORS, CSRF/Origin validation, cookie domain/SameSite/Secure behavior, CSP and client URLs for this additional origin. Preserve the existing Worker hostname until rollback and test needs are resolved.
3. Inspect actual Brevo transactional sender/template IDs and reset/verification links. Modify only proven outdated application links. Preserve email domain authentication DNS.
4. Confirm whether managed Supabase Auth is used anywhere before changing its Site URL or redirect allowlist; the observed main login flow uses application-level auth. Never reset existing user tables or service credentials.
5. Recheck Supabase security and performance advisors after any relevant code/database change; do not weaken RLS or expose service-role credentials.
6. Avoid broad wildcard OAuth redirects and shared authentication cookies across future unrelated `*.rvea.info` projects.

## Release verification (all pending)

- DNS authority validated from the registry and authoritative nameservers.
- Wix root and WWW content, canonical redirect, HTTPS and no loops verified.
- RIVEXIS custom hostname TLS certificate, DNS and exact Worker mapping verified.
- Original `workers.dev` hostname still functions.
- Login, signup, email verification, reset link, session reload, logout, unauthorized access and legitimate test-account flow passed.
- Same-origin API, WebSockets (if present), wallet/contract paths, reports, responsive desktop/mobile and error handling passed.
- No mixed-content, unintended redirects or cross-project cookie leakage.
- Old-to-new origin cutover has deploy SHA, tests, and rollback evidence.

**No pass may be claimed until the corresponding real production test has run.**

## Rollback and future projects

Retain the old Worker custom hostname, deployed Worker version, GitHub revision, verified DNS export, existing Wix pointing records, old auth origin settings and email configuration. On regression, revert only the impacted layer and re-test, without broad changes to database or user accounts.

For each future project: choose a unique lowercase slug, deploy to its own existing host, attach one exact subdomain, verify DNS/TLS, scope auth/cookies/API permissions to that project, complete smoke tests, then document ownership and rollback. Do **not** add wildcard DNS now.

## Access limitations and next steps

This audit had working GitHub and Supabase read access, but no authenticated Wix/Cloudflare DNS dashboard control and no verified public DNS/HTTPS response; Brevo account inspection returned a connector error. Therefore **no nameserver/DNS, Worker custom-domain, Supabase Auth, Brevo sender, or production code modification is asserted**.

Next authorized implementation must first obtain the registrar/Wix and Cloudflare zone record inventories; then proceed with the exact verified configuration above, run actual application end-to-end tests, and update this file with explicit evidence and final status. 
