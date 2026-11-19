# 0004: Keep DeFi monitoring opt-in, durable and separate from market display

Status: implemented candidate, not deployed or activated. 19 November 2026.

## Context

The active application has validated, block-consistent lending adapters and five bounded browser checks. The retained generic alert infrastructure does not continuously evaluate these DeFi positions. TradingView display data cannot become an input to machine-driven risk analysis. Browser/Edge background timers cannot provide durable protection.

## Decision

Use one optional official market widget for human display. Keep it isolated from application storage, calculations and exports. Retain the existing financial models and supported Aave/Morpho identities.

Prepare owner-private rules and an event/outbox lifecycle in the existing Supabase project, matching personal DeFi report ownership. Client RLS reads expose safe owner columns only; verified-session APIs supply the actor to service-only invoker RPCs. Do not repurpose legacy workspace monitors or enroll existing users.

Use supported Supabase Cron to invoke a short, authenticated Edge worker. Persist leases, versions, last successful evidence, consent, cooldowns and delivery state. Reserve the existing distributed quota **before any RPC read**, including reorg checks. Bound database, RPC and mail I/O under the invocation deadline. Treat unknown delivery/write outcomes conservatively and separate acceptance from actual delivery receipts.

Keep evaluation and email activation independently disabled until source review, schema/provider acceptance and specific production approvals. The migration does not install a schedule or enable sending. No paid service or infrastructure replacement is required by the source change.

## Consequences and rollback

Coverage is deliberately limited to three enabled rules globally and approximate 30-minute evaluations under the shared 300/day quota. Outages, rapid movements and missing provider rights can prevent protection; UI must show actual coverage and historical timestamps. The new function needs deployment, Vault/runtime token configuration and a reviewed Cron job before operating. Email additionally needs a confirmed template/sender and verified receipt/inbox acceptance; no public webhook is enabled here.

Disable email, disable evaluation and unschedule only the new named job before rolling back a function/frontend. Preserve the additive RLS tables and UNKNOWN outcomes for reconciliation. Never restore customer data or change DNS for this feature rollback. See [the implementation runbook](../MARKET_RISK_MONITORING_20261119.md) for configuration, licensing, costs and acceptance gates.
