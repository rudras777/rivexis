# RIVEXIS supported-beta operations

This runbook covers the existing authenticated Ethereum application. It is an operator procedure, not evidence of an on-call team, automatic alerts, an uptime SLA or an independently completed institutional review. Keep the current root checkpoint and exact release report beside this document.

## Establish the incident scope

Record UTC time, exact deployed commit/Worker allocation, route without query/fragment, expected behavior and observed status. Use connected provider dashboards and existing authenticated tools. Never copy cookies, tokens, recovery material, private account exports, user identifiers or full request URLs into public issues or CI. Preserve failed evidence before retrying; distinguish fixtures, public checks and actual signed-in observations.

Check the existing Worker Metrics using the actively deployed-version filter and stated time window. Record invocation/runtime-error/client-cancellation counters separately. Zero Worker exceptions do not prove zero HTTP failures; cancellations do not by themselves prove a server defect. Treat asset metrics as a separate scope. Supabase log queries should select aggregate status, route, gateway error and latency rather than raw identities/messages. Do not enable a paid observability tier or export private logs to a new service.

## Recovery by failure class

| Observation | Safe action | Evidence before closing |
| --- | --- | --- |
|401 or expired session|Use normal login; verify the signed-in account and authorized workspace. Do not weaken the gate or widen grants.|Authenticated navigation works; guest endpoints still deny private access.|
|403 authorization or verification denial|Verify email/workspace entitlement through existing flows. Never grant access merely to make a test pass.|Correct owner/member can access; unauthorized actor remains denied.|
|503/provider-degraded read|Preserve gateway code/time, inspect provider health and use the explicit Retry control after availability returns.|A fresh read completes; unavailable/stale evidence is not represented as current.|
|Malformed200 account response|Withhold invalid account data; show Settings recovery. Inspect the response contract without publishing personal data.|Valid response restores controls; invalid data causes no client exception or success notice.|
|Lost or invalid save confirmation|Keep the draft and disclose that the outcome is unconfirmed. Check current saved state before an explicit repeat.|The confirmed server record matches the intended change; no automatic write retry.|
|RPC timeout, stale oracle/block or reorg|Stop the affected calculation/preview, retain its receipt and refresh supported evidence explicitly.|Fresh block/hash/oracle provenance and model invariants pass; never override source prices or supported-mode checks.|
|Unachievable planner target|Keep the unmet result and budget/token/fee constraints visible.|Independent receipt math matches; no safety/execution/global-optimum claim.|
|Deployment regression|Compare exact source/tree/build/HTTP/authenticated markers; retain old/new evidence and roll back the application version when appropriate.|Same existing URL, restored supported workflows, authenticated/guest checks and financial-source identity.|

No incident response step requests a private key, signs/submits a transaction or transfers funds. Native-wallet permission testing requires the owner's actual test wallet; fixture coverage is separately labeled.

## Application release and rollback

Use an isolated development branch in the existing repository. Keep financial/reference checks, API/security/database gates and the full browser matrix passing on the exact candidate. Promote only the tested head; verify main/Worker/native build and configured traffic allocation, public no-cache build marker and genuine signed-in UI. Keep actual-public checks independent of controlled fixtures. Retain failing runs, timeouts and successful bounded recovery without claiming a continuous SLA.

For application-only rollback, select a retained previously verified Worker version on the same existing service and restore its traffic allocation. Record the version/commit and repeat identity, authentication and relevant workflow checks. Keep source/data intact. No client-only deployment here changes the schema; never turn an application rollback into a production database restore, destructive migration, password reset or account deletion.

## Financial and monitoring boundaries

Coverage is validated Ethereum Aave V3 normal mode and the pinned Morpho WBTC/USDC86%LLTV market. Other markets/modes/chains and arbitrary/cross-protocol sequences remain unsupported. Defense Planner searches a bounded5% grid with at most two actions and explicit budget, token and assumed fee constraints. A current-price preview does not execute market stress or certify future safety/inclusion/fees. Reports include reproducible JSON receipts; keep account exports private.

Visible-tab market polling, historical oracle observations and bounded browser monitoring do not create continuous server tick storage or automatic alert-delivery guarantees. Keep freshness, observed coverage gaps and offline/backoff states visible. Respect current application/RPC quotas; do not run unbounded polling/load tests, add paid providers or silently upgrade plans. Added service cost is distinct from account-wide billing.

## Recovery and maintenance gates

Use the dated production logical recovery and encrypted off-device copy reports for the scope they actually tested. Preserve the separate recovery key; never publish/upload it or place it with the archive. Independent key custody, second-machine/full-service restore, retention and RPO/RTO need their own evidence.

A production database upgrade requires a fresh protected production archive and isolated restore, plus specific approval for privileged temporary access and the offered outage/no-downgrade maintenance. Revoke temporary access after its approved task. The old token's authorization does not create a new privileged token. Do not remove pg_net or widen policies merely to silence an advisor. Preserve deny-by-default RLS and inspect dependency advisories without forced breaking fixes.

Owned sender-domain/DNS verification and a real native test wallet are owner-resource gates. Independent security/operating review and sustained field/load/provider assurance remain external gates. Do not mark them complete from this runbook, a short probe or a green CI run.
