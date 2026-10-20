# Account-response recovery — 20 October 2026

## Problem and change

A read-only operational review found one actual Supabase Edge503 on GET account/settings in the provider's last24-hour window. Its gateway error was SUPABASE_EDGE_RUNTIME_SERVICE_DEGRADED, not evidence of a Rivexis exception. Successful Edge Function responses numbered2091 and authentication denials548 in the aggregate query; no identities, tokens, IPs or raw user messages were selected. Execution p50/p95 for successful function responses were852/1574ms. The zeros in the separate edge_logs execution-time result mean that attribute was absent, not zero-latency requests.

Separately, a controlled HTTP200 Settings response with missing profile reproduced a TypeError reading emailVerified instead of the explicit recovery UI. The original failed test, trace and extracted page error remain outside Git. This malformed response was fault-injected locally; it was not observed in production or inferred to be the cause of the provider503.

Shared account GET and PATCH responses now pass through one decoder before publication into the query cache or confirmation of a save. It checks profile types, optional dates, all expected preference fields and the existing preference validator. It rejects malformed financial defaults instead of silently filling missing values. Authentication, CSRF, request deadlines and the existing explicit retry behavior are retained. Invalid save confirmation leaves the draft intact and shows no success notice; writes are not automatically retried.

Only the account response boundary and its consumers change. Financial models/handlers, API34, backend, database, dependencies, logo, public layout/colors and approved background are preserved. No migration, production account write, new credential, signing, provider configuration or paid service is required.

## Operational evidence and limits

Cloudflare's actively deployed-version filter showed Worker6824855c at100% allocation,644 invocations and zero runtime errors in the displayed24-hour window. Memory/CPU-limit/internal/load-shed/uncaught-exception counters were zero. It also reported74 client cancellations and zero response-stream disconnections. Those cancellations are retained and are not diagnosed as either application crashes or harmless test traffic without request-level evidence. Asset counters displayed zero4xx/5xx, with97.61% cache hits; asset metrics are not asserted to be version-filtered. The active table showed medianCPU7.45ms. Provider observations are not field browser Core Web Vitals, sustained load testing or an SLA.

The existing High braces advisory GHSA-vfj7-8cjw-p6xm still has no patched release in the checked [GitHub advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm); npm's current version remained3.0.3. No force downgrade or undocumented patch was applied. The scoped audit exception remains disclosed.

## Validation and release status

- Before fix: missing-profile recovery regression failed; trace contains Cannot read properties of undefined (reading emailVerified).
- Next production build, TypeScript and AST checks pass locally.
- Chromium Settings31/31 pass with no retries: ten malformed account cases, three provider/transport/JSON recovery cases, invalid save confirmation with explicit retry, and the retained17 Settings cases.
- WebKit Settings31/31 also pass with no skipped/flaky/unexpected cases or test retries. Worker build and subsequent official Next typegen/types pass. AST174 passes.
- Full default count is305 per engine; actual-public suite remains30. Exact-head full release gates, deployment and final actual-public verification remain pending. Existing production remains4849a626 until promotion is verified.

Raw operational aggregate/screenshot and local proof files are in the task outputs directory. The [current checkpoint](../RIVEXIS_PRODUCTION_COMPLETION_TRACKER.md) records the active branch and subsequent gate status. Owned sending-domain information was requested asynchronously; native-wallet, independent recovery, privileged maintenance approvals and institutional assurance limits remain unchanged. No protected recovery key was accessed.
