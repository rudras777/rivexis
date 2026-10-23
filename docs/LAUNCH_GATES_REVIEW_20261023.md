# RIVEXIS launch-gate review — 23 October 2026

The existing website remains on production commit `37d03fd3c539085538cbbca48ea2f29b91a581fb`, PR105. This continuation completes the specifically approved off-device copy of the 20 October recovery archive and records fresh provider, security and performance observations. It changes no application source, branding, financial model, authentication configuration, database, deployment or paid plan. The [evidence manifest](evidence/launch-gates-review-20261023.json) identifies the bounded checks and hashes; protected data and download credentials are excluded.

## Approved off-device recovery copy

The owner explicitly answered **“Approve the encrypted backup copy”** to the proposal identifying the 804,514-byte encrypted 20 October archive, its production database/authentication and Vault recovery contents, the existing owner-only RIVEXIS Recovery folder, and keeping the decryption key local. The upload completed once. Metadata readback confirms the expected existing parent, binary MIME type, expected size, shared=false and only the owner's permission on both the folder and new file. The actual Drive folder shows both the original 17 October archive and the new 20 October archive; the original is preserved.

An independent authenticated download of the new off-device file returned exactly **804,514 bytes**, SHA-256 **`fedbd8db3ea05414587fcc79989cdaad1cbf8f5314c52ac3e53dc3561f2d4724`**, matching the verified local ciphertext. No recovery key was read or uploaded; no decryption, plaintext transfer, new database export, access-token creation, permission change or database write occurred. Private Drive identifiers, account addresses and temporary download credentials are omitted from the repository.

This is a storage round trip for the **20 October pre-upgrade snapshot**, copied on **23 October**. The [20 October local recovery drill](FRESH_RECOVERY_DRILL_20261020.md) already verified authenticated decryption, all102 archived entries/32,179 rows and Vault recovery; that restore was not repeated today. Matching ciphertext preserves that package identity. This is not a new23 October database snapshot, independent key custody, second-machine recovery, an automatic retention policy, RPO/RTO validation or full provider/service reconstruction. The [17 October off-device verification](OFFSITE_RECOVERY_20261017.md) remains separately dated.

## Current production and security checks

- Fresh ordinary HTTP checks return the existing homepage200 with exact37d03fd identity and /health200 ready. The existing normal signed-in session opens the protected workspace; the selected LiquidationGuard title and description remain entirely inside their menu row with no selection line across the description.
- Actual Overview refresh advances Ethereum block26255373→26255377. ETH/BTC each show seven genuine oracle observations and the fee series advances from four to eight observations. Insufficient24-hour coverage remains explicit. One initial Overview heading wait deadline missed; the same navigation then arrived without a repeated click or reload. Cause is unestablished; the observation is retained.
- Fresh npm audit has zero critical and zero Next.js findings. Seven high package entries remain attributable only to the existing narrowly gated Braces advisory. The [upstream advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) still lists no patched version. No exception or dependency change was introduced.
- Fresh Supabase security advisors report19 intentional deny-default/RLS-without-policy INFO items, one extension-in-public WARN and one leaked-password-protection WARN. Performance advisors report114 unused-index INFO items and no WARN. Unused indexes were not deleted; recent maintenance can affect statistics, and INFO does not establish that an index is safe to remove.
- Read-only catalog inspection confirms pg_net0.20.4, extension schema public, **relocatable=false**, twelve member routines and zero member routines in public. The extension-schema advisory is not a count of public routines. Ordinary ALTER EXTENSION SET SCHEMA is unsupported for this installed extension. No catalog edits, grants or drop/recreate operation were attempted. [PostgreSQL relocation semantics](https://www.postgresql.org/docs/17/catalog-pg-extension.html), [Supabase advisory](https://supabase.com/docs/guides/database/database-linter?lint=0014_extension_in_public).
- Supabase [leaked-password protection](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection) remains a Pro-plan feature. No paid upgrade or substitute security claim was made.

## Bounded performance diagnosis

Three serial fresh guest Chromium contexts checked the actual production landing page at4x CPU slowdown, tracing/video disabled, five seconds of observation after DOM readiness, and no mock data. All returned200 with exact37d03fd identity, no recorded page/request/HTTP failures, loaded fonts and no horizontal overflow.

| Sample | Viewport | LCP ms | CLS | Navigation request start ms | Request-to-first-byte ms |
|---|---|---:|---:|---:|---:|
| Desktop first | 1440×900 | 4236 | 0.000027 | 3056.5 | 363.9 |
| Mobile viewport | 390×844 | 1108 | 0 | 248.9 | 262.8 |
| Desktop repeat | 1440×900 | 1608 | 0.001157 | 573.1 | 248.9 |

The slow sample spends2705ms before DNS starts. Its cause is not established; the measurement does not demonstrate a server or application delay of that duration. The original slow result is retained. Thirty local calls to the existing hypothetical landing illustration's frontier calculation measured median0.7102ms and maximum4.0684ms; this is not Worker CPU measurement, real-user field data or a financial-model change. Neither these three samples nor viewport emulation certify native mobile UX, load capacity, sustained availability or an SLA. No speculative optimization or visual redesign was applied.

## Provider resources and remaining decisions

The existing Cloudflare account's Domains view is empty. This does not establish whether the owner holds a domain elsewhere. The actual Brevo dashboard has one verified gmail.com sender, DKIM Default and a “Freemail domain is not recommended” warning; its Domains view has no configured domain. The senders connector returned an internal error, so the ordinary existing dashboard was used for verification. No email was sent and the working sender was preserved.

The owner has a pending choice: provide a domain already owned for authentication email, or explicitly retain the current verified sender for a bounded beta. No domain purchase, unowned DNS zone, sender replacement or assumption of consent was made. Prior actual verification/recovery delivery remains valid; inbox placement is not certified.

The actual billing page identifies **Workers Free**, and Brevo shows the existing300/day free allowance. Added recurring service cost remains **USD0**. These observations do not certify every account's total bill or future quota availability. No paid upgrade, new permanent project or new provider was created.

The installed native-wallet approval gate remains blocked: the available native Brave launch exposed no targetable window and follow-up inventory was empty. Mocked provider fixtures do not replace real permission UI certification. No wallet was imported, unlocked or asked to sign. Independent key custody/second-machine recovery, owned email-domain/inbox assurance, sustained field/load/availability and independent security/operating assurance remain unresolved. **Supported bounded beta workflows are deployed; unrestricted institutional launch certification remains BLOCKED.**

## Release evidence retained

PR105's [security/navigation closeout](NEXT_SECURITY_CLOSEOUT_20261023.md) retains all seven passing source/PR/main/Worker/fixture/public gates,326 controlled cases per Chromium/Firefox/WebKit and30 actual-public cases per engine. The final public run is [39836207489](https://github.com/rudras777/rivexis/actions/runs/39836207489): its CI-only HTTPS-mirror source differs only in workflow, while application/backend/dependency/test trees match production37d03fd. Previous failures remain recorded. Documentation commitc3d466bc6c70b3c2d75a9f72b7b9ca16acb8f10b has [passing CI39837162541](https://github.com/rudras777/rivexis/actions/runs/39837162541); the CI-only mirror commit also passed full CI39836206866. These are historical exact-head results, not claims that this new documentation commit has passed before it runs.

No runtime deployment is needed for this storage/audit-only continuation. Resume only a newly evidenced defect or the specific remaining resource/assurance gates; preserve the local key separately and never publish protected recovery material.
