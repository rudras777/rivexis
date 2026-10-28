# Wix support question — prepared, not sent

I own rvea.info, registered through Wix, and host my existing portfolio on Wix. I need to retain that same Wix site at the root/www while using Cloudflare authoritative DNS so an existing Cloudflare Worker can serve rivexis.rvea.info. The Wix zone contains three apex A records and a www CNAME; I preserved them DNS Only in Cloudflare.

The Wix UI requires unassigning the domain before switching to external nameservers. After switching, assigning it back to the same Wix site is blocked by Reset nameservers to Wix first. The portfolio returned 404, so I restored Wix nameservers and the original site assignment; it is working again. Contact verification is complete.

Can this Wix-registered domain remain assigned to the same Wix site using external authoritative DNS? If supported, please provide the exact connection/assignment procedure and SSL renewal requirements, or enable the supported account configuration. Please do not transfer the domain, change hosting/content, add paid services, or disconnect the working portfolio without approval.
