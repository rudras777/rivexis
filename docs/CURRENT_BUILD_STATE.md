# Rivexis Current Build State

Last updated: 2026-09-29

This file is the compact continuation point. Newer verified GitHub source, production Supabase state, and the authoritative Cloudflare Worker state override older notes.

## Certified source

- Repository: `rudras777/rivexis`; branch `main`.
- Latest fully certified product source: `38f3d866359f82dfeeacfd7ceb3ae9d67d6bbcdf` (`Keep workspace controls reachable`).
- Exact-head CI: `36465744408` — **SUCCESS**.
- Exact-head Pages: `36465743682` — **SUCCESS**.
- The full gate passed invariants, secret/migration checks, PostgreSQL migrations/runtime controls, API lint/tests/audit, Edge typecheck/tests, web typecheck/build, vinext build, npm audit and the complete Playwright browser suite.
- The browser suite certifies the signature visual system, accessibility, authentication/session lifecycle, workspace isolation, engine provenance, F1/F3/F5 structured inputs, organization membership, Decision Desk/reports, monitors and alert operations.
- The Edge helper test suite now also certifies alert-notification truth wording, HTML escaping, deterministic Brevo idempotency keys and duplicate-provider acceptance handling.
- Pages remains fallback/navigation/review only; it is not the authoritative application runtime.

## Signature visual system

The newer source deliberately moves away from generic AI/SaaS dashboard styling while preserving the Rivexis navy/blue/light identity:

- architectural off-white canvas with technical grid/radial linework rather than blank white;
- sharper 0–2px controls and inputs rather than pill-heavy UI;
- editorial/asymmetric public hero and decision instrument treatment;
- continuous engine architecture with hairline separators rather than repeated rounded cards;
- dark institutional methodology band with structural linework;
- split architectural authentication layout retaining the auth-orbit visual;
- workspace evidence field, deeper navy rail navigation, continuous panels, denser tables and terminal/editorial information hierarchy;
- contextual SVG graphics remain present on public, authentication and workspace surfaces;
- visual-contract Playwright and accessibility checks pass.

This source is certified and live on the authoritative Cloudflare Worker. Public HTML exposes the exact build SHA and `/health` returns HTTP 200/ready through the same-origin proxy.

The workspace rail now groups Command, Operations, Evidence and Infrastructure surfaces without removing any route. It scrolls independently when viewport height is constrained, so Workspaces and logout remain reachable. History resolves active and archived saved references, marks them as Saved and prevents duplicate persistence requests.

## Completed product workflows

### History

History supports search/filtering, canonical persisted provenance inspection, direct Save reference, workspace isolation and action-level browser coverage.

### F1 Portfolio & Exposure

Live F1 source has a bounded structured `manual_positions` builder with CoinGecko asset ID, symbol and quantity fields, add/remove/edit controls, canonical payload preservation and advanced JSON retained for integration-specific fields.

### F3 Position & Liquidation

Live F3 source exposes the actual required evidence inputs: collateral oracle feed, collateral/debt units, liquidation threshold, optional debt oracle/fallback, optional CoinGecko cross-check and price-conflict tolerance. Required-field gating, canonical request behavior, CSRF and UNKNOWN-safe results are browser-tested.

### F5 Treasury Allocation & Scenario

Live F5 source has a structured allocation ledger for asset ID, symbol, weight and stablecoin classification, bounded to 50 rows. Entered weight totals are explicit and Rivexis does not silently normalize user-entered allocations. The F5 provenance browser assertion waits for and validates the actual canonical request rather than racing an async route-handler side effect.

### Organization/member administration

Organization membership parity is implemented and certified:

- organization IDs are explicit and do not imply access;
- authenticated members can inspect the actual membership list;
- OWNER/ADMIN can manage permitted existing-member roles;
- OWNER-specific and last-owner safeguards remain enforced by the backend;
- new membership is claim-based rather than direct new-user email insertion;
- authenticated users can generate a short-lived organization membership claim;
- authorized organization administrators can accept that claim with a selected role;
- removals require explicit confirmation in Settings;
- action-level Playwright covers role update, claim-based admission, confirmed removal, claim generation, protected request payloads and CSRF.

### Decision Desk and decision reports

Decision/report parity is implemented and certified rather than simulated:

- Decision Desk is a first-class workspace surface;
- users select persisted specialist analyses, bounded to 10 references;
- duplicate specialist-engine weighting is blocked in the interface;
- the server rehydrates each submitted analysis reference from canonical persistence and re-evaluates current workspace authorization before decision scoring;
- canonical decisions are persisted before later retrieval/history use;
- decision output preserves methodology version, engine/framework versions, evidence provenance, missing data, source conflicts, confidence, canonical persistence state and demo state;
- demonstration input is explicitly labelled synthetic in the decision/report workflow;
- JSON, HTML and PDF report formats are supported;
- a report row is persisted before rendering any report output;
- report downloads are protected by the same browser session and CSRF model;
- action-level Playwright covers canonical decision creation, exact persisted analysis references, CSRF, provenance display and JSON/HTML/PDF download behavior.

### Alert operations

Alert-control parity is a real production-backed workspace surface:

- Alerts is a first-class workspace navigation surface separate from manual monitor definitions;
- alert list reads are server-authorized to the active workspace;
- alert states can be changed only by write-capable workspace roles;
- dead-letter requeue requires OWNER/ADMIN management access;
- 24-hour queue metrics expose total, pending/retry, delivered, dead-letter, oldest pending age and delivered-within-SLO percentage;
- runtime metrics now expose the actual scheduled processor state, delivery sink state, last run, last success/error, last cycle counts and recipient policy;
- requeue truthfully resets queue state and never claims provider or inbox delivery;
- the UI distinguishes provider acceptance from inbox delivery and still states that continuous threat ingestion is not configured;
- an empty alert list explicitly does not claim that threats are absent;
- action-level Playwright covers alert navigation, scheduled/no-sink and ready delivery truth, status mutation, requeue and CSRF.

### Monitor-result alert creation

Production compatibility parity is closed without weakening evidence integrity:

- the trigger consumes only the persisted canonical B3 analysis referenced by the monitor update;
- the analysis must belong to the same workspace and be a B3 `supabase-edge` result;
- `UNKNOWN` and `NO_VERIFIED_PROVIDER_EVIDENCE` results create zero alerts;
- materiality otherwise matches the provider-capable FastAPI contract: signals, hard blockers or moderate/high/critical severity;
- a canonical event key deduplicates repeat equivalent monitor events per workspace/monitor;
- a repeated event updates the same alert, increments `occurrence_count`, refreshes `last_seen_at` and retains the latest analysis ID;
- synthetic/demo material events are explicitly titled and described as synthetic, not live threat claims;
- cross-workspace analysis references cannot be promoted into an alert.

Rollback-only production verification passed: UNKNOWN produced zero alerts; a material synthetic event created exactly one truth-labelled alert; an equivalent repeat produced one row with occurrence count `2`; a cross-workspace analysis produced no alert; rollback left zero fixture users/workspaces/monitors/analyses/alerts.

### Scheduled alert delivery processor

The compatibility runtime now has a real scheduled queue processor while remaining fail-closed when no outbound sink is configured:

- Supabase `pg_cron` runs `rivexis-alert-dispatch` every minute through `pg_net`;
- the internal dispatch token is generated in production and stored in Supabase Vault; the raw token is not embedded in source or the Cron job;
- the dispatcher is protected by a dedicated internal token and unauthenticated POST requests fail with HTTP 401;
- the database dispatch bridge is SECURITY DEFINER under a dedicated `rivexis_alert_dispatcher` role that is NOLOGIN, NOINHERIT, BYPASSRLS, non-superuser and has no CREATEDB/CREATEROLE/REPLICATION authority;
- the role has no CREATE privilege on `public` or `extensions`, only schema USAGE plus the minimum queue read/update and owner-email lookup grants;
- the temporary migration-time SET ROLE path from `postgres` to the dispatcher is revoked before migration commit;
- queue claiming is lease-based and uses `FOR UPDATE SKIP LOCKED`, preventing concurrent duplicate claims during the lease;
- success marks provider acceptance as `delivered`; failures use bounded exponential retry and then dead-letter at the configured attempt limit;
- Brevo submissions use a stable alert-derived idempotency UUID and treat the provider duplicate-idempotency response as prior acceptance rather than resending;
- message copy truthfully labels synthetic evidence and never claims continuous provider surveillance;
- the current recipient policy is `WORKSPACE_OWNER_EMAIL`;
- when Brevo configuration is absent the processor reports `SCHEDULED_NO_SINK`, processes zero alerts and consumes zero delivery attempts.

Rollback-only production queue verification passed lease exclusivity, owner-email lookup, retry/backoff, dead-letter transition and successful provider-acceptance state, then rolled back with zero fixture residue.

## Production backend

Supabase production is the current compatibility backend.

- PostgreSQL 17.6.1; hardened posture retained.
- Core Alembic application schema remains through `0013_auth_email_lifecycle`.
- Supabase Edge `rivexis-api` is **version 8 ACTIVE**.
- Supabase Edge `rivexis-decision-reports` is **version 1 ACTIVE**.
- Supabase Edge `rivexis-alerts` is **version 2 ACTIVE**.
- Supabase Edge `rivexis-alert-dispatch` is **version 1 ACTIVE**.
- Existing general, Saved Analyses and organization-membership compatibility bridges remain deployed.
- Production membership migrations 008 and 009 are live.
- Production migration `010_edge_decision_reports` is live.
- Production migration `011_edge_alert_lifecycle` is live.
- Production migration `012_edge_monitor_alert_creation` is live.
- Production migrations `013_edge_alert_delivery_scheduler`, `014_alert_dispatcher_extensions_usage` and `015_alert_dispatcher_object_grants` are live.
- `pg_cron` and `pg_net` are enabled for the scheduled alert processor; Supabase Vault retains the internal dispatch credential.
- `public.rivexis_edge_decision_report(text,text,jsonb)` and `public.rivexis_edge_alerts(text,text,jsonb)` retain their previously certified SECURITY DEFINER/service-role-only contracts.
- `public.rivexis_edge_monitor_alert_from_analysis()` remains owned by `rivexis_migrator`, SECURITY DEFINER with pinned `search_path=pg_catalog, public`, and exposes no direct execute capability to `PUBLIC`, `anon`, `authenticated` or `service_role`; it is invoked only by the enabled monitor trigger.
- `public.rivexis_edge_alert_dispatch(text,text,jsonb)` is owned by `rivexis_alert_dispatcher`, SECURITY DEFINER with pinned `search_path=pg_catalog, public, extensions`; direct execute is service-role-only and every action additionally requires the Vault-backed internal token.
- `public.rivexis_edge_alert_delivery_runtime()` is owned by `rivexis_migrator`, SECURITY DEFINER with pinned `search_path=pg_catalog, public`, and direct execute is service-role-only.
- Direct dispatcher `/health` is HTTP 200 and reports `ready`, `supabase-edge`, `supabase-cron`, `SCHEDULED_NO_SINK`, `NOT_CONFIGURED`, recipient policy `WORKSPACE_OWNER_EMAIL`, and `continuous_threat_ingestion=false`.
- Direct Alerts `/health` is HTTP 200 and reports `ready`, `supabase-edge`, durable-record-only ingestion, `SCHEDULED_NO_SINK`, `NOT_CONFIGURED`, the same recipient policy, and the last delivery cycle timestamp.
- Unauthenticated dispatcher POST fails HTTP 401 `Dispatch authentication required`.
- Unauthenticated alert list access fails HTTP 401 `Authentication required`.
- Cron run records are succeeding every minute and automatically advance the delivery runtime heartbeat.
- Production currently contains zero durable alerts, so scheduler promotion emitted no backlog.

No provider evidence was fabricated. Compatibility analysis remains UNKNOWN-safe when verified provider evidence is unavailable.

## Authoritative frontend truth

Authoritative public frontend:

`https://rivexis-web.rudrasingh0718.workers.dev/`

The Cloudflare web Worker serves exact source `38f3d866359f82dfeeacfd7ceb3ae9d67d6bbcdf` as Worker version `4fc4e9f1-ab93-420c-a02c-041ad9860057`. The build marker, same-origin Edge health response, authenticated grouped navigation, saved-state guard and clean browser console were verified after deployment.

A verified deployment workflow exists at `.github/workflows/deploy-web.yml`. It deploys only after successful CI, targets the existing `rivexis-web` Worker, stamps `NEXT_PUBLIC_RIVEXIS_BUILD_SHA`, and verifies that exact SHA from the public site after deployment. Automatic runs currently stop before contacting Cloudflare because GitHub Actions secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` are not configured. Manual deployment uses the legitimate authenticated local Wrangler OAuth session; do not expose that session or substitute unrelated credentials.

## Evidence integrity retained

- B1 `1.3.0` / `b1-live-1.8.0`
- B2 `1.1.0` / `b2-live-1.3.0`
- B3 `1.1.0` / `b3-live-1.3.0`
- B4 `1.0.0` / `b4-live-1.1.0`
- B5 `1.2.0` / `b5-live-1.4.0`
- F1 `1.2.0` / `f1-live-1.4.0`
- F2 `1.2.0` / `f2-live-1.4.0`
- F3 `1.3.0` / `f3-live-1.3.0`
- F4 `1.2.0` / `f4-live-1.3.0`
- F5 `1.2.0` / `f5-live-1.3.0`

Without verified live provider evidence, the compatibility runtime returns UNKNOWN rather than inventing evidence. Demonstration outputs remain explicitly synthetic.

## Current external gates

1. Cloudflare deployment automation — production is exact-source, but GitHub Actions still lacks the two Cloudflare deployment secrets and therefore cannot promote future commits automatically.
2. Full provider-capable FastAPI runtime — Cloudflare Container path remains Workers Paid gated.
3. Provider credentials/contracts/licenses — unavailable evidence remains UNKNOWN/unavailable.
4. Owned sender domain — Rivexis does not yet have an authenticated owned sending domain for production-branded email.
5. Alert outbound sink — the scheduler and queue processor are live, but `BREVO_API_KEY` plus a configured/verified `RIVEXIS_BREVO_SENDER_EMAIL` are not present in the Supabase Edge runtime, so production correctly reports `SCHEDULED_NO_SINK` and consumes no queued attempts.
6. Continuous threat ingestion — scheduled alert delivery does not create evidence. The compatibility runtime still has no always-running provider threat stream and must never be presented as continuous surveillance.

## Immediate next execution target

Preserve the certified scheduled-delivery source. If legitimate Brevo Edge secrets and a verified sender become available, configure them through secure project secrets, keep the raw API key out of source/chat, verify the dispatcher becomes `SCHEDULED_READY`, and certify one explicitly controlled notification path before claiming production email delivery.

Until then, continue unblocked production hardening. Preserve exact-SHA manual promotion and verification for every source change; when narrowly scoped Cloudflare deployment credentials become available to GitHub Actions, certify the existing workflow before treating deployment as automatic.
