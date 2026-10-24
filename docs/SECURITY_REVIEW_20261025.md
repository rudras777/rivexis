# Security completion review — 25 October 2026

Baseline production:2b1bfcdcb54df97e0123ae3453879999ae24672d (PR114), existing Cloudflare Worker/URL and Supabase/Brevo. Review is first-party engineering validation, not independent certification. This source record states local observations; final exact-head workflow, promotion, native Worker and public acceptance belong to the release PR and resumable evidence checkpoint.

## Reproduced gap and correction

An isolated execution of the actual baseline proxy with stubbed fetch accepted a foreign-origin cross-site POST to the login route and called upstream once. No real login, email or account change occurred; this demonstrates a missing explicit request-boundary check, not proof of account compromise. CORS is a response-reading control, and the existing session CSRF check cannot protect the initial login before a session exists.

The proxy now rejects foreign/null origins and cross-site fetch metadata for POST/PUT/PATCH/DELETE before forwarding. Exact current origin supports production and local development. Non-browser calls without Origin retain the unchanged upstream auth/verification/CSRF responsibility. Session cookies, auth providers and backend implementation are unchanged.

The proxy previously parsed a cloned legacy-analysis body without a byte cap and streamed other request bodies upstream without a proxy cap. It now enforces128KiB against both Content-Length and actual streamed bytes, cancels oversize reads, reports unreadable streams honestly and preserves supported payload bytes. Existing smaller backend limits remain. No timeout or unrestricted DoS certification is claimed.

## Fresh evidence

- Actual25October Supabase read-only metadata: ACTIVE_HEALTHY17.11.0.003;61 public ordinary tables/zero without RLS; zero public client-callable security definers; six sensitive/owner tables deny anon and authenticated SELECT; no public views. Edge versions unchanged36/4/5/3/3.
- Fresh real npm audit: zero info/low/moderate/high/critical findings. Strict audit policy29/29, financial/auth295/295 and source pattern scan PASS.
- Proxy25/25 named scenarios: four write methods, foreign/null/lookalike/downgrade/port origins, fetch-metadata mismatch, normal same-origin bytes/headers/cookies, no-origin clients, safe GET, local dev, declared/streamed/understated/UTF-8 oversize, exact boundary, failed/empty body, sample rejection, malformed JSON, isolated upstream blockade and report routing.
- Six local HTTP/browser regressions pass, including three new cases for actual HTTP acceptance for cross-site login403, foreign-origin Settings403 and oversize413; no credentials are submitted and no email/save action is triggered.
- Initial unit tests passed but TypeScript correctly rejected an overly broad typed-array buffer type. The return now explicitly owns an ArrayBuffer; final unit/type/AST checks pass. The initial diagnostic remains in local evidence.
- Reviewed current Supabase changelog: modern supported clients require no TLS downgrade for the announced obsolete TLS1.2 cipher retirement. Leaked-password protection remains Pro-only per current official documentation.

## Unresolved platform and assurance scope

Two existing Supabase WARNs remain: nonrelocatable pg_net extension namespace and paid leaked-password protection. Its12 extension routines are in net and both client roles have schema usage/execute there; this is not a claim those routines are reachable through the configured Data API. No public routine or client grant was widened. No destructive relocation, credentials reset, plan upgrade or database mutation was performed. Nineteen deny-default RLS INFO findings remain intentional. Existing net exposure boundaries must remain restricted.

Current sender is the owner's explicit limited-beta choice. Independent recovery/key custody, full native wallet consent/events, sustained performance/load/provider service and independent security/operating review remain unverified. Supported protocol/planner/fee/monitoring limits remain in the handoff. Re-running fixtures does not close these external assurance gates.

## Preservation and release

Only the proxy, its tests/CI invocation and dated security/readiness records change. The actual-public suite now includes security-header/request-boundary checks, and screenshots are stored per deployed commit to preserve earlier immutable evidence. No landing/brand/style/SVG, financial model, API handler, database, Settings, Supabase/Brevo configuration, package/lock or Worker configuration change. Added recurring service costUSD0; account billing is not certified. Preserve all earlier immutable release evidence and use a new security-launch-20261025 prefix for this release. Do not overwrite prior screenshots or protected recovery files.

Candidate status: locally validated; release gates and actual-public verification are required before calling this patch deployed. Baseline2b1 is the source rollback, but lacks this proxy hardening; prefer patched roll-forward for permanent use.
