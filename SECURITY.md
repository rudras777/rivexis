# Security

Report vulnerabilities privately through this repository's **Security → Report a vulnerability** control. Private vulnerability reporting was enabled and read back on3 November 2026. Do not post passwords, tokens, customer data, wallet keys or recovery material in public issues. No bug-bounty or response-time SLA is promised.

## Verified controls and boundaries

- Mandatory verified-session and owner/tenant authorization in the active APIs; RLS on all 61 public tables at the3 November catalog checkpoint; zero client-callable public security-definer functions.
- Same-origin write checks, bounded bodies, no-store private responses, secure cookies and explicit unsupported/provider-failure states. Tests cover CSRF/origin, malformed confirmations, stale state and quota failures.
- Fixed-point financial models, pinned chain/block/oracle identities, read-only simulations and no custody, automatic signing or transaction submission.
- Six strict protected-branch checks, admin enforcement, no force pushes/deletions, native GitHub secret scanning and push protection enabled. These settings are controls, not a security certification.
- Credentials remain in existing provider stores. Public browser configuration must never contain service-role/SMTP/Cloudflare keys. Local preview blocks external API forwarding.

## Known limitations

The nonrelocatable `pg_net` extension remains registered in public; the generic relocation advice is not a safe verified fix. See [the exposure review](docs/NET_EXTENSION_EXPOSURE_REVIEW_20261020.md) and [official advisor](https://supabase.com/docs/guides/database/database-linter?lint=0014_extension_in_public). Leaked-password protection remains disabled on the existing Free project; no paid upgrade was authorized ([provider guidance](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection)).

Production migration history is not fully reconstructible from the tracked Supabase directory. One historical migration matched a credential-related review pattern; its statements were not exported. This does not establish a currently usable leaked credential. Rotation requires dependency assessment and specific approval.

Full wallet consent/denial/account-switch lifecycle, sustained load/operating assurance, independent recovery-key custody and current sender-domain/inbox assurance remain separate acceptance items. No institutional, regulatory or third-party audit certification is asserted.

The released [dependency-security follow-up](docs/governance/DEPENDENCY_SECURITY_20261103.md) records the patched SVG/compression graph, actual registry-audit scope and the unsupported direct Node ESM image-rendering path. [Production acceptance](docs/governance/RELEASE_ACCEPTANCE_20261103.md) includes startup-safe account forms. A zero-finding registry scan is not a blanket security certification or authorization to expose a new rendering endpoint.

The 4 November console audit found no authenticator enrolled on the sole Supabase owner account. Cloudflare account-wide MFA enforcement was unchecked/disabled with a current-user enrollment warning. These require owner-controlled enrollment and recovery custody; existing application Auth/RLS checks do not close infrastructure-owner MFA assurance. See the [Supabase](docs/governance/SUPABASE_CONSOLE_AUDIT_20261104.md) and [Cloudflare](docs/governance/CLOUDFLARE_CONSOLE_AUDIT_20261104.md) findings.
