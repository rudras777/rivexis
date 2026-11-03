# Infrastructure

Verified inventory checkpoint: 3 November 2026. No resource was renamed, deleted or transferred during discovery.

| Service / identifier | Purpose / environment | Owner boundary | Dependencies / risk / action |
|---|---|---|---|
| GitHub `rudras777/rivexis` | Public authoritative repository; `main` | `rudras777` verified sole listed admin collaborator | Six strict checks; admin enforcement; preserve history. New secret scanning/push protection/private reporting verified enabled |
| Cloudflare account `0b22778ba197266a58dd26eeef0334a8` | Existing production account | Founder account verified by authenticated Wrangler | Broad local OAuth scopes; do not export tokens or refresh scopes unnecessarily |
| Worker `rivexis-web` | Current application / production | Same account | PR126 `e4a23c1`, version `02442078-81d5-45f5-a4c7-5f3d5f936c42`. Root/app/generated Wrangler configs are build entrypoints for this same Worker. Keep deployed name |
| Pages `rvea-rivexis-gateway` | Custom-host ingress / production | Same account | `RIVEXIS_WEB` binding to existing Worker; CLI confirms `rivexis.rvea.info`; preview rejects API/credential/write traffic |
| `rivexis.rvea.info` | Canonical application | Founder-managed Wix DNS | Fresh CNAME points at gateway; no nameserver or root/WWW change |
| Original Worker URL | Recovery/compatibility application origin | Same Worker | Retain existing auth/session boundary; never copy cookies between origins |
| GitHub Pages `main:/` | Historical redirect | Repository owner | Root HTML redirects to original Worker; not a second backend. Retain until redirect cleanup is reviewed |
| Supabase `ivszvufdonfgwjpfgwii` | One visible Rivexis project / production | Organization `ygqzbykzuaegubxxgiey`, Rivexis | Free plan, ap-south-1, ACTIVE_HEALTHY, PostgreSQL 17.11.0.003; organization IAM ownership transition not certified |
| `rivexis-api` | Core API / production | Existing Supabase project | Version 40 released/read back after PR125; version 39 retained for rollback. Application auth remains enforced with gateway verify_jwt=false |
| `rivexis-decision-reports` | Retained historical decision/report API | Same project | Version 6; preserve owner/tenant controls |
| `rivexis-alerts` | Retained alert management | Same project | Version 7; does not imply continuous DeFi risk monitoring |
| `rivexis-alert-dispatch` | Existing legacy dispatch integration | Same project | Version 5; integration/credential dependencies must be reviewed before retirement |
| `rivexis-cloudflare-recovery-relay` | Retired historical capability | Same project | Version 4, verify_jwt=true; source is a fixed 410 response. Do not delete based on name |
| Brevo workspace `Rivexis` | Existing SMTP/transactional delivery | Owner-confirmed Google account | Browser access verified; connector returns internal errors. Existing 300/day allowance, verified freemail sender, no sending domain, two active transactional templates and dated Delivered events observed; no new message/sender/key/plan |
| Ethereum PublicNode | Existing free RPC fallback | External provider | Availability/quota not guaranteed; failure withholds results; no new paid RPC subscription |
| Develoop 0.1.3 | Optional local development skill bundle | Local developer tooling | Manifest identifies `comfuture/agent-skills`, publisher Changkyun Kim; skills-only GitHub workflows, not a deployed Rivexis backend. No repository runtime reference found |

Full-account Cloudflare Worker inventory and dashboard-only TLS/rule/Builds settings remain unverified. Cloudflare dashboard currently requests sign-in; authenticated CLI is usable. Do not infer absence of other account resources from one verified application. Brevo's two active template records do not establish which flows invoke them; current Supabase Auth uses its own templates with the existing SMTP transport. Provider Delivered events do not guarantee inbox placement. The outbound-webhook view showed an empty setup state; inbound webhooks require Enterprise and were not enabled. Other Brevo automations remain unverified.

Local Dev: safe preview plus isolated browser fixtures. Staging: isolated local Worker/test fixtures exist; a complete independent Supabase staging reconstruction remains incomplete. Production: existing services above. No new permanent staging project was created.

The [4 November Supabase console audit](docs/governance/SUPABASE_CONSOLE_AUDIT_20261104.md) verified one listed Owner, Free subscription, enabled spend cap and no listed invoices. Auth redirects, email confirmation, refresh-token protection and the existing Brevo SMTP transport were inspected without saving changes. Managed scheduled backups and configurable session restrictions are unavailable on this Free plan; preserve the separate dated logical recovery evidence and explicit recovery gaps.

Names: [registry](docs/governance/NAMING_REGISTRY.md). Configuration and release: [deployment](DEPLOYMENT.md). Database/migration status: [database](DATABASE.md).
