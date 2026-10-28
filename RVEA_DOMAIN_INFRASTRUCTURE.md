# RVEA domain infrastructure

Checkpoint: 28 October 2026. Migration incomplete; public DNS remains at Wix.

## Intended mapping

| Host | Destination |
| --- | --- |
| https://rvea.info | Existing Rudra Singh Wix portfolio |
| https://www.rvea.info | Same Wix portfolio / existing canonical alias |
| https://rivexis.rvea.info | Existing Cloudflare Worker rivexis-web |

No new Worker, database, domain purchase, wildcard or paid service is authorized or needed by this checkpoint. Existing GitHub repository is rudras777/rivexis; production branch main. Verified baseline merge 1d4f0772aba12cf7cd96735c6685ddcb9bbe9531; prior Cloudflare version 750ac172-a50e-4b91-b78d-99563ab80bd7.

## Actual findings and preservation

Google public DNS returned Wix nameservers ns4.wixdns.net and ns5.wixdns.net. Apex A records: 185.230.63.107, 185.230.63.171, 185.230.63.186 (TTL 3600). www CNAME: cdn3.wixdns.net (TTL 3600). No apex MX, TXT, CAA, AAAA or registrar DS answer in this snapshot. This is NOT a complete inventory of records at arbitrary subdomains or DKIM selectors. Full Wix account inventory remains required. rivexis.rvea.info returns NXDOMAIN.

Cloudflare account 0b22778ba197266a58dd26eeef0334a8 contains pending Full zone af74f9f2c1d47209440a0756b251af9f. Assigned nameservers: melody.ns.cloudflare.com and wilson.ns.cloudflare.com. Zone has exactly four imported Wix records matching the public targets. All four were incorrectly Proxied. Changed only their proxy status to DNS Only, saved and read back; no record values deleted or altered. Pending zone is not authoritative, so this staging correction does not change public resolution. Exported staged BIND zone in task outputs/rvea-domain-20261028-cloudflare-staged-zone.txt. Before/after account snapshots and screenshots are preserved there.

Apex HTTPS redirects to https://www.rvea.info/; both return 200 with normal certificate verification. Visible portfolio heading is Rudra Singh. Browser title remains Home | My Site 1 (unfixed SEO defect). Do not change design/content. Wix setup shows Light plan, no business email, and a domain contact verification deadline of 10 November 2026. Registrar identity, expiration, auto-renew and verification completion are not yet independently confirmed.

Existing workers.dev landing loads correctly in the connected browser. Python urllib request returned 403; retained as a client-specific failure, not treated as proof of an outage or bypassed. Second resolver HTTPS lookup failed local issuer certificate verification; no TLS checks were disabled and no two-resolver claim is made.

User signed in to Wix in newly connected Chrome. Both dashboard embedded Domains panel and standalone /account/domains remain blank/loading after normal navigation and one reload. Do not import browser credentials or invent private API access to bypass this blocker.

## Authentication and application migration inventory

Existing Supabase project: ivszvufdonfgwjpfgwii. Actual Auth Site URL remains https://rivexis-web.rudrasingh0718.workers.dev and existing redirect allowlist contains that origin /**. Recorded read-only; no Auth setting changed while custom hostname is unavailable. Existing users and database untouched; no mail sent.

Source audit found hostname dependencies:
- apps/web/app/layout.tsx metadataBase.
- supabase/functions/rivexis-api/index.ts LIVE_ORIGIN used for signup confirmation, resend and recovery.
- rivexis-decision-reports and rivexis-alerts LIVE_ORIGIN.
- rivexis-alert-dispatch/delivery.mjs email image and alert URL.
- apps/api/cloudflare origin configuration and legacy placeholder.

Audit each consumer and deployed binding before changes. Do not globally replace test, preview, rollback or internal API URLs. Keep cookies host-scoped; never share session cookies with the Wix root or future projects. Do not transfer existing session cookies between origins. Preserve current Brevo sender and signing records unless separately justified. New-host signup, verification, recovery, authenticated features and email links remain UNTESTED.

## Exact next steps

1. Restore a working Wix domain management page; export full authoritative records and confirm registrar, expiry, renewal, DNSSEC and contact verification. Contact verification was completed by the owner and confirmed in the Wix success page on 28 October; no further contact-verification action is needed.
2. Confirm exact site-specific external-DNS pointing instructions and continued portfolio assignment. Current Wix custom nameserver documentation requires unassigning first and warns of SSL renewal effects. This conflicts with the explicit requirement not to disconnect the portfolio: do not unassign or assume existing DNS alone guarantees continuing Wix service. Resolve supported connection method with Wix before migration; obtain approval if temporary disconnection is unavoidable.
3. Reconcile complete source zone with staged Cloudflare records, including mail, verification, CAA and selectors. Keep Wix records DNS Only. Capture rollback and resolve any registrar DS before authority change.
4. Only after preservation and supported Wix mapping are verified, change registrar nameservers to the exact assigned Cloudflare pair. Check authoritative and recursive answers and zone Active; do not confuse pending status with propagation completion.
5. Attach ONLY rivexis.rvea.info through existing Worker Custom Domains. Let Cloudflare manage its DNS/certificate, no conflicting CNAME and no apex Worker route. Keep workers.dev enabled.
6. Verify TLS and routing first; then implement narrow origin/metadata/email-link changes on this branch, preserve origin fences, deploy through protected GitHub workflow. Update Auth Site URL and precise actual redirect destinations; retain necessary recovery origin entries.
7. Verify root/www portfolio, custom RIVEXIS, login/signup/verification/recovery/logout, host-scoped cookies, protected routes, reports/settings, live data and provider flows on desktop/mobile. Use authorized test account; retain failures honestly. No current new-host acceptance test has passed.

## Rollback

Before authority change, all production routing is unchanged. Staged proxy correction should remain DNS Only for Wix. If the eventual cutover fails, restore captured original Wix nameservers ns4.wixdns.net / ns5.wixdns.net and the verified portfolio assignment according to Wix's supported method. Preserve original records and workers.dev recovery endpoint. Restore prior Auth URL configuration and source release if hostname-dependent behavior breaks. Do not restore database or delete users as a DNS rollback.

## Future project procedure

Choose lowercase exact slug; check conflicts; identify its host/owner; deploy to that service; attach only its exact subdomain using provider-supported mechanism; validate certificate, auth callbacks and host-scoped cookies; test refresh/deep links and mobile; record deployment and rollback. Do not create placeholder or wildcard records. Keep portfolio root and project data/auth independently scoped.

## Official references

- https://developers.cloudflare.com/workers/configuration/routing/custom-domains/
- https://support.wix.com/en/article/connecting-a-domain-to-wix-using-the-pointing-method
- https://support.wix.com/en/article/changing-nameserver-ns-records-for-a-wix-domain

Completion status: staged DNS safety correction and audit completed; authority/custom-domain/authentication migration NOT completed. Added recurring service cost: USD 0.

## Follow-up verification

Owner contact verification confirmed on 28 October: Wix displays Your Contact Information is Confirmed / No further action is needed. Reopened signed-in Chrome Domains page still spins; embedded-frame read timed out, with no error-level console entries available. Cloudflare overview still shows Pending and the same assigned nameservers. No nameserver, Worker route, Auth, database or mail change in this follow-up. Existing 31 proxy regression cases were rerun with rivexis.rvea.info as the request origin: 31 passed, zero failed/skipped/cancelled. This is an isolated stubbed-upstream test, NOT live custom-host authentication or DNS acceptance. Test output saved in task outputs/rvea-domain-20261028-custom-origin-proxy.log. Python console printing initially failed encoding Unicode test marks after the test finished; retained log confirms pass counts.

## Wix manager recovered; actual migration gate

28 October follow-up: Domains panel loaded successfully. Primary domain rvea.info renews on 27 October 2027; successful contact verification is shown in the domain card. Manage DNS Records contains exactly the three apex A records and www CNAME recorded above; TXT/SRV/MX sections have no configured rows. Source account AX inventory saved as rvea-domain-20261028-wix-authoritative-records.txt in task outputs. Complete exported Cloudflare zone matches these four targets and keeps them DNS Only.

Clicking Use custom nameservers opens the explicit blocking dialog: "Unassign this domain first" and "Changing nameservers would take that site offline." No name server editor is available while the domain remains assigned. No unassignment or nameserver change was performed. Screenshot and text saved as rvea-domain-20261028-wix-unassign-warning.*. This supersedes the prior loading blocker; the current gate is approval for a potentially disruptive cutover, contrary to the original no-disconnection constraint.

Proposed cutover, only with explicit exception approval: preserve the captured Wix assignment/zone; unassign only if necessary; set melody.ns.cloudflare.com and wilson.ns.cloudflare.com; verify Cloudflare Active and continued Wix portfolio using the preserved DNS Only records; restore original nameservers and Wix assignment if portfolio continuity cannot be established. Do not guarantee uninterrupted availability or assume DNS alone preserves application assignment. Keep existing Worker recovery URL and Auth settings until custom hostname is reachable and validated. Attach only rivexis.rvea.info; never route apex/www to RIVEXIS.

Official Cloudflare alternatives checked: partial/CNAME zone setup requires Business or Enterprise; delegated child zones require Enterprise. Neither is a free-plan workaround and no upgrade was selected. Official Worker Custom Domain setup requires an active zone. No unsupported CNAME-to-workers.dev record was created.

## Approved cutover attempted and rolled back

Owner explicitly approved the controlled cutover after the outage warning. Unassigned rvea.info from existing My Site 1; Wix confirmed unassignment. Saved the exact Cloudflare pair melody.ns.cloudflare.com / wilson.ns.cloudflare.com; Wix displayed MANAGED EXTERNALLY and update success. Root and www then returned 404. Immediately attempted to reassign to the SAME original site. Wix blocked this with Reset nameservers to Wix first: external nameservers prevent assigning this domain to a Wix site. This is an observed account restriction, not an inferred lack of credentials or incomplete contact verification.

Rollback completed: Reset to Wix saved ns4.wixdns.net / ns5.wixdns.net; selected original site 35246fe9-12e6-45c0-84ef-2f93f7697986 and restored primary domain. Wix success said rvea.info was successfully assigned to My Site 1. A fresh direct Domains page independently confirmed Primary domain under that site. Initial post-restore requests still returned cached/distributed 404; subsequent canonical root and www requests returned HTTPS 200 with Rudra Singh identity. Browser reload of plain https://www.rvea.info/ confirmed the actual portfolio. Google resolver NS and A results remain original Wix values. Do not claim global propagation or no outage: a brief 404 outage occurred during this approved attempt. No further nameserver switching should be repeated without a different supported provider solution.

Evidence in task outputs: nameservers-saved.png, wix-reassign-blocked.png, wix-assignment-restored.png, assignment-readback.txt, rollback-http.json (initial failures), rollback-http-final.json (both 200), portfolio-recovered.png, all with prefix rvea-domain-20261028-. Production Worker/source/Auth/Brevo/database were not modified. Custom RIVEXIS hostname is NOT live; contact verification IS complete. Added service cost remains zero.

Provider action needed: obtain a supported Wix method to retain this Wix-registered domain assigned to its existing Wix site while authoritative nameservers are external. Current UI requires unassignment to switch, and requires resetting to Wix to reassign. Ordinary external-domain pointing documentation does not override this account restriction. Keep the portfolio live on Wix meanwhile. Paid Cloudflare partial DNS or domain/hosting migration are outside current authorization; do not purchase or migrate blindly.
