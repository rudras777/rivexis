# Anonymous recovery document — 6 November 2026

**Implemented; release acceptance remains required.** [Prior failures and exact deployed baseline](POST_RELEASE_TRANSPORT_20261105.md). Preserve all failed runs. This mitigation removes request-time rendering from one identity-independent document; it does not establish the underlying framework/platform cause or certify all transport behavior.

## Evidence and decision

The original workers.dev origin twice passed36/37 actual-public checks, with a repeated navigation timeout opening /forgot-password. A separate request probe timed out on that document while the other four authentication documents returned200. Connected Chrome loaded and hydrated recovery normally. The matching Cloudflare recovery invocation at14:12:47.911UTC on5November was canceled after39,717ms wall time with1ms CPU, HTTP/3 and ray ID a55c74976c5be27d. The separate Network connection lost error belonged to /platform/, not this request. CPU exhaustion is not established as the cause.

The same unchanged five-page regression passed against the isolated compiled Worker in8.4seconds with external API forwarding blocked. Local reproduction therefore does not establish a general source-rendering defect. Rather than patch framework internals, disable protections or increase test timeouts, extend the existing accepted anonymous build-document path to this source page. Its component renders an empty client-side email form; it reads no server-side identity, cookie, account record or query-derived value.

## Resulting behavior

The existing Worker serves ordinary GET/HEAD /forgot-password from the same compiled, anonymous form captured at build time. Its referenced JavaScript, CSS, logo, background, typography, layout, labels and hydration remain the original source. The login page's recovery link becomes an ordinary same-origin anchor so it requests this document directly, without speculative Flight prefetch or client-router dependence for that link. Other links/navigation remain unchanged.

The form still waits for React Hook Form readiness and submits only to the existing password-reset POST API. No email, recovery token or credential is embedded in the artifact. Verification, delivery, enumeration-safe behavior, session/CSRF controls and server-side authentication remain in the existing API. No recovery request is sent merely by opening this page. Interactive recovery requests must be tested with isolated fixtures; do not send production email without its scoped authorization.

Writes, APIs, protected pages, login/reset-password documents and requests carrying Flight/router/prefetch signals retain their existing handlers. Missing/failed recovery assets return an honest503/no-store response without repeated request-time rendering or internal diagnostics. The recovery response adds no-referrer and no-store; visitor credentials, conditional headers and query strings are excluded from the internal artifact fetch. These are security headers, not visible UI labels.

## Build and preservation

The existing build-only loopback renderer captures landing and recovery from the same compiled Worker. Both require complete200 HTML, exact build identity, expected source heading, no Set-Cookie and valid referenced build assets; recovery additionally requires the POST form and reset-request label. Failure of either capture fails the build. The renderer flag remains local only and is rejected in deployment variables. Separate non-overlapping Static Assets rules protect each direct/extensionless artifact, keeping recovery no-store/no-referrer without merging a public cache directive into it. The existing manifest's landing fields remain compatible, with both documents listed explicitly.

Five before-change recovery routing assertions failed; all35 routing/security cases pass after the change, including12 recovery cases. Syntax, fresh route types and frontend AST passed. An initial local test configuration failed before running because of its module mode; it was corrected and is not an application failure. An incorrect local candidate build marker was caught and rejected as acceptance evidence; an exact-commit rebuild is required. Vinext regenerated incompatible temporary route declarations before a lint attempt; the normal type-generation command repaired generated output, without hand-editing declarations.

Remaining acceptance: exact committed build and both artifact hashes/headers; real compiled-Worker recovery hydration/link flow with external forwarding blocked; existing required source/Worker/three-browser gates; normal protected merge; existing automatic same-Worker deployment; both-host actual-public checks and normal-session acceptance when the owner's active browser/origin is identified. No timer or assertion is weakened. A rerun alone is not cause/fix evidence.

Rollback selects compatible Worker4717400b-85a5-4495-9f72-fb7226494bda / main60c00fa9a805751c59f4d4e8ef61378c6ce14d7f, leaving API40 and production data unchanged. There is no database migration, financial-model edit, new service, paid-plan change, password reset or automatic credential/signing action.
