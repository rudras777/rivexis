# RVEA → RIVEXIS Pages gateway (non-disruptive alternative)

**Scope:** a small Cloudflare Pages Function invokes the **existing** `rivexis-web` Worker over a Cloudflare Service Binding. This does **not** replace, rename or duplicate the RIVEXIS application, Supabase project or database.

## Why

Wix registration and original Wix site stay untouched at `rvea.info` and `www.rvea.info`. The prior Wix-to-Cloudflare nameserver attempt caused a 404 and was rolled back. Unlike Workers Custom Domains (requires active Cloudflare zone), **Cloudflare Pages supports external-DNS subdomains** on Wix nameservers.

Cloudflare official references:

- https://developers.cloudflare.com/pages/configuration/custom-domains/
- https://developers.cloudflare.com/pages/functions/bindings/#service-bindings
- https://developers.cloudflare.com/pages/functions/advanced-mode/
- https://developers.cloudflare.com/pages/functions/wrangler-configuration/

## Deployment sequence

1. Keep Wix nameservers `ns4.wixdns.net` / `ns5.wixdns.net` and root/www records unchanged.
2. Create a separate Cloudflare Pages project `rvea-rivexis-gateway` in the **same Cloudflare account** as the existing Worker `rivexis-web`, using its free tier if available.
3. Deploy `public/_worker.js` in Pages Advanced Mode, with `wrangler.jsonc` and the `RIVEXIS_WEB` Service Binding to `rivexis-web`. Deploy a preview first and verify `https://rvea-rivexis-gateway.pages.dev/__rvea_gateway_status` responds 200 with `ready:true`. Ordinary preview browsing is read-only and does not permit authenticated endpoints.
4. In Pages > Custom Domains, **first** associate `rivexis.rvea.info` with `rvea-rivexis-gateway`. Check that Cloudflare accepts the external-DNS setup and the pending full zone does not interfere. **Do not assume it will work if blocked**.
5. Only after the Pages custom-domain registration is accepted, add a single `CNAME` on the authoritative Wix DNS zone: `rivexis.rvea.info` → `rvea-rivexis-gateway.pages.dev`. No DNS change to apex/www. Never create the CNAME before associating the custom domain; Cloudflare documentation warns of 522 errors.
6. Verify public DNS, Cloudflare-issued TLS, the Worker landing, static assets, deep links, response headers and host-only cookies.
7. Review and deploy the separate application-origin migration PR #119, and configure actual Supabase Auth redirect URLs, API origin allowlist, email link origins and any required service bindings only after the new host is ready. Keep the original `workers.dev` entry fully functional.
8. Complete an authorized test-account signup, verification, password recovery, login, session reload, logout, protected routes, Settings/reports, mobile/browser and wallet acceptance.
9. Take evidence and record final deployment SHA, branch, Worker/Pages version IDs, DNS snapshot, tests, and rollback.

## Safeguards

- Do not alter Wix site assignment, nameservers, primary site domain, database rows, existing Supabase users, Brevo senders or protected project secrets.
- Do not proxy arbitrary origin hosts. The Pages gateway accepts only the exact custom hostname and its fixed Pages preview hostname. On Pages preview, POST and private API/cookie requests are rejected.
- No anonymous preview API access. No credential tokens in logs or the repository.
- Pages gateway adds an extra network/runtime dependency. Retain the direct original Worker and certify performance/errors before shifting real users.
- The staged full Cloudflare zone may need Cloudflare account-side cleanup if it prevents Pages custom domain association. Never delete the zone merely to experiment.
- No paid Cloudflare upgrade is authorized. Check the exact plan cost before enabling new services.

## Rollback

Delete **only** the Wix `rivexis` CNAME, once documented, or detach the Pages custom-domain mapping; do not touch root/www Wix DNS. Restore previous exact auth redirect/canonical settings if previously changed. Original `https://rivexis-web.rudrasingh0718.workers.dev` remains available throughout.

**Status:** source only until actual Pages project, domain mapping, DNS, auth and end-to-end production smoke tests are observed.
