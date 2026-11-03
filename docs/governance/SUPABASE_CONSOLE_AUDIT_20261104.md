# Supabase console audit — 4 November 2026

Read-only inspection of the existing `ivszvufdonfgwjpfgwii` project in organization `ygqzbykzuaegubxxgiey`. The owner specifically approved the existing GitHub sign-in continuation; the console then authenticated as the existing account. No new account, project, paid plan, password reset or configuration save occurred. This extends console coverage; it does not redate the [3 November product acceptance](RELEASE_ACCEPTANCE_20261103.md).

## Observed configuration

| Area | Console evidence |
|---|---|
| Project | Existing production `main`, Healthy, Nano; one visible project; no repository connected in the overview |
| Organization access | Team page lists one member, Owner. The existing account Security page explicitly shows “No authenticator apps yet”; console MFA is not enrolled |
| Billing | Free Plan, spend cap enabled, no past invoices listed. The console warns quota exhaustion can cause unresponsiveness or read-only behavior; this is not a full account-wide cost certification |
| Site URL | `https://rivexis.rvea.info` |
| Allowed redirects | `https://rivexis.rvea.info/login?verified=1`, `https://rivexis.rvea.info/reset-password`, and the retained recovery origin `https://rivexis-web.rudrasingh0718.workers.dev/**` |
| Providers | Email enabled; all other listed providers disabled; no custom provider listed |
| Signup controls | New signup enabled; confirmation required; anonymous sign-in and manual identity linking disabled |
| Access token lifetime | 3600 seconds |
| Refresh-token protection | Replay detection/revocation enabled; reuse interval 10 seconds |
| Session restrictions | Single-session enforcement, time box and inactivity timeout are disabled/unavailable on Free; console requires Pro for these controls. No plan change or forced logout |
| Rate limits | Refresh 150 per IP per 5 minutes; verification and signup/sign-in 30 per IP per 5 minutes; same-user email minimum interval 60 seconds. Other controls remain provider-configured; no limit was changed |
| SMTP | Custom SMTP enabled, `smtp-relay.brevo.com`, port 587, sender name Rivexis. Username/password values were excluded from inspection/output. This verifies configuration, not a new delivery/inbox test |
| Managed backups | Scheduled-backup view explicitly states Free does not include project backups; no paid upgrade selected. The protected historical logical recovery kit is a separate dated artifact |
| Access tokens | Account list showed no access tokens. After separate specific approval, a 24-hour single-project Database read-write token was created, used only to obtain a temporary read-only login, and revoked; final list again showed no tokens |

## Owner account protection

The sole listed owner account has no Supabase authenticator enrolled. This is a material administrative-access assurance gap. Enrollment requires the owner to register an authenticator and retain recovery material; no agent-generated seed or credential change was attempted. Do not confuse end-user application session protection with MFA on the infrastructure owner account. GitHub upstream protection was not re-certified from this page.

## Recovery preparation and limits

Production has 48 migration-ledger entries versus four tracked Supabase migrations. A metadata register is not an executable baseline. The supported temporary-login endpoint requires `database_write`, even for a requested read-only login; the prepared token therefore carries more capability than the intended read-only operation. Do not create it based on the sign-in approval, use a legacy full-account token, reset the database password or export browser credentials.

The separately approved [confidential capture and bounded reconstruction](SCHEMA_RECONSTRUCTION_20261104.md) verified read-only access, 300-second login expiry, certificate validation, token revocation and seven matching public-schema metadata groups. Portable tools were provisioned without a Windows service. Full matching managed-extension replay and user-data/service recovery remain unfinished; this was a schema-only test. No production schema migration or original password reset occurred.

Existing catalog/advisor results remain separately dated in [DATABASE.md](../../DATABASE.md) and [SECURITY.md](../../SECURITY.md). Cloudflare account-wide console inventory, independent operator recovery, key custody, transfer eligibility and broader security assurance remain outstanding. No user identities, password values, recovery keys or raw sensitive migration statements are included here.

Provider references: [temporary CLI login](https://supabase.com/docs/reference/api/v1-create-login-role), [scoped access tokens](https://supabase.com/docs/guides/platform/personal-access-tokens), [redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls), [sessions](https://supabase.com/docs/guides/auth/sessions), [database backups](https://supabase.com/docs/guides/platform/backups).
