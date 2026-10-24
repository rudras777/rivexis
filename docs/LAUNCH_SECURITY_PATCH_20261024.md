# Launch-day dependency security patch — 24 October 2026

The fresh real npm audit of verified productionec8c7b4 now contains six affected package entries: two High, four Moderate, zero Critical. The unchanged strict audit gate rejects understated transitive severity before its High/Critical gate. Yesterday's zero-finding report remains historical; this detection is not evidence that production was exploited.

## Narrow correction

| Package | Existing | Candidate | Primary evidence |
|---|---|---|---|
| Zod |4.6.1|4.6.7|[Oversized collection resource consumption](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5); patched4.6.6 or later |
| Undici |7.29.1|7.30.1|[Excessive content-encoding unhandled-error denial of service](https://github.com/advisories/GHSA-xjj6-f33q-929c); patched7.30.1. The same patch covers the reported EventSource/SRI findings. |
| fast-uri |3.1.8|3.1.9|[Encoded-scheme confusion](https://github.com/advisories/GHSA-w74x-v6f9-j3xg); patched3.1.9. The same patch covers the remaining reported URI normalization findings. |

Zod is pinned directly; Undici and fast-uri use exact root overrides. Existing Next16.4.2, React19.3, Vite8.3.5, Wrangler4.148.0, Cloudflare plugin1.62.4 and Sharp0.35.5 remain. No audit exception, forced major downgrade, assertion removal or altered severity threshold is introduced.

An initial workspace install left the transitive pins unchanged. A named update also introduced unrelated lock churn, including nested older Sharp entries; it was discarded. A fresh manifest-only npm resolution in an isolated task-output directory produced the patched package records. Only those three records and the web Zod declaration were selected into the prior lock; their registry URLs/SRI and unchanged dependency/engine fields were checked. All unrelated package paths/records remain identical. Clean `npm ci`, installed-graph inspection and the real audit are required to validate this lock rather than trusting its text.

## Scope and release requirements

Only package manifests/lock and dated operating evidence are intended to change. Financial kernels, API/authentication handlers, database/schema, workflow definitions, UI/brand/layout/background and deployment configuration remain unchanged. Existing Cloudflare/Supabase/Brevo/URL and data are retained; no new recurring service or spending.

Run the unchanged strict real audit and its29 policy cases; financial/auth/API/market/wallet tests; type/AST checks; Next/Vinext builds and Worker dry runs; exact-head source/PR/main gates; the browser compatibility matrix and actual-public checks. Preserve intermediate failures. The final release PR/checkpoint records actual candidate/merge/Worker/CI identities and outcomes; this source document does not predeclare remote success or deployment from a dependency install.

The baseline native-wallet and six independently reconciled genuine financial receipts retain their original scope. After promotion, verify ordinary signed-in navigation/Settings/reports and the real installed wallet on the existing public URL. Same financial source is not a new live certification of every amount or protocol.

PR107/ec8c7b4 and earlier retained Workers remain availability rollback sources, but contain the newly detected affected versions. A rollback requires a patched roll-forward before permanent use. No database restore, account deletion, password reset or grant widening is part of this package patch. Broader institutional assurance limits remain in the [current handoff](LAUNCH_HANDOFF_20261024.md).
