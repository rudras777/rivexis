# RIVEXIS security boundaries

Current deployed architecture: the existing Cloudflare website proxies to the existing Supabase Edge functions, Supabase Auth and private database. Brevo delivers authentication mail. The optional Python API and its scrypt, Redis, commercial-provider and legacy-engine controls are separate repository components; they are not evidence that those services are deployed on the current website.

## Supported website controls

- Identity is verified server-side with Supabase Auth. User-editable metadata cannot substitute for confirmed email ownership or organization membership. Browser access/refresh credentials stay in HttpOnly, Secure, SameSite=Lax cookies; private API responses use no-store. Logout discloses unconfirmed provider revocation and access-token expiry limits truthfully.
- Authenticated writes require a matching session CSRF header. The 25 October proxy patch additionally rejects explicit foreign/null origins and cross-site browser metadata before forwarding any write, including login/signup/recovery before a session exists. Origin-less non-browser clients still face upstream identity, verification and CSRF checks. This is a browser request-boundary control, not authentication by Origin.
- The proxy buffers at most128KiB per request, checks declared and streamed bytes and rejects unreadable bodies without forwarding. Existing endpoint-specific smaller limits remain. This size cap is not a network timeout or unlimited denial-of-service protection.
- Workspaces, organization membership, Settings and private reports derive their actor from the verified identity. Owner filters and database routines enforce access; client-selected actor IDs cannot grant access. All61 live public tables have RLS enabled. Legacy/server-only tables deny direct client reads, and no live public SECURITY DEFINER routine is executable by anon/authenticated roles as of the dated audit.
- RPC endpoints and supported chains/protocols are server-selected. Address/calldata/ABI and return sizes are bounded. Block identity, reorg, stale oracle and unsupported-mode checks remain explicit. Wallet integration never requests a private key or silently signs/submits a transaction. Contract inspection does not certify source or ABI verification.
- Shared analysis quotas are300/day globally and four per wallet/minute; reports are capped at20/account. Browser monitoring and history are bounded. These limits support a small beta and are not an availability SLA.
- Browser security headers include framing/object/base/form restrictions, nosniff, HSTS and recovery/login no-referrer behavior. This is a baseline CSP, not a claim of nonce-based script isolation. Stronger CSP needs separate framework/Worker compatibility validation.
- Exact pinned dependencies, lockfile, strict npm audit validation, Python dependency audit, financial/auth tests, migration/RLS checks, browser checks and source secret-pattern scanning run in CI. Pattern scanning is not complete secret detection or independent penetration testing.

## Live platform findings and operating limits

The25October read-only audit reconfirms Supabase ACTIVE_HEALTHY/PostgreSQL17.11.0.003 and unchanged API36/reports4/alerts5/dispatch3/recovery-relay3. Npm reports zero findings. Supabase retains two WARN findings:

- [pg_net extension in public](https://supabase.com/docs/guides/database/database-linter?lint=0014_extension_in_public): installed0.20.4 is nonrelocatable; its12 routines live in net, not public. Do not drop/recreate or edit extension catalogs to silence the advisor. Preserve the current Data API exposure boundary and review dependencies before an approved platform migration.
- [Leaked-password protection](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection) is disabled and requires Pro or above. No plan upgrade is authorized. Existing password/session controls remain; this paid platform warning is not resolved by local validation.

Nineteen RLS-without-policy INFO findings intentionally deny client access. Do not add policies merely to clear notices. Native wallet existing-grant/chain-change acceptance is dated24October; fresh native permission/rejection/account-change/disconnect paths remain uncertified. The owner accepts the current verified email sender for a limited beta; owned-domain authentication/inbox placement remains uncertified.

## Recovery and incident handling

Retain tested patched Worker versions for application rollback. A frontend failure does not authorize database restoration, deleting users, widening grants or resetting credentials. The20October logical backup/local restore and approved23October owner-only encrypted off-device copy are dated recovery evidence. Keep the decryption key separate; independent key custody, second-machine and full-service recovery/RPO/RTO remain unverified.

Use [supported-beta operations](SUPPORTED_BETA_OPERATIONS_20261020.md) and the [current readiness record](PRODUCTION_READINESS.md). Sustained load/field availability and independent security/operating review remain open. The supported site has bounded-beta acceptance; no document certifies absolute security, arbitrary protocol support or unrestricted institutional operation.
