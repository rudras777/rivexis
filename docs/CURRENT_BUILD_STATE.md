# Rivexis Current Build State

Last updated: 2026-09-28

This file is the compact continuation point. Newer verified GitHub source, production Supabase state, and the authoritative Cloudflare Worker state override older notes.

## Certified source

- Repository: `rudras777/rivexis`; branch `main`.
- Latest fully certified product source: `5db08682178d630045a9689cd345d0c0422eaa14` (`Stabilize F5 provenance request assertion`).
- Exact-head CI: `36448110030` — **SUCCESS**.
- The full gate passed invariants, secret/migration checks, PostgreSQL migrations/runtime controls, API lint/tests/audit, Edge typecheck/tests, web typecheck/build, vinext build, npm audit and the complete Playwright browser suite.
- The browser suite certifies the signature visual system, accessibility, authentication/session lifecycle, workspace isolation, engine provenance, F1/F3/F5 structured inputs, organization membership, Decision Desk/reports, monitors and alert operations.
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

This source is certified but must not be described as live on the authoritative Cloudflare Worker until deployment verification succeeds.

## Completed product workflows

### History

History supports search/filtering, canonical persisted provenance inspection, direct Save reference, workspace isolation and action-level browser coverage.

### F1 Portfolio & Exposure

Live F1 source has a bounded structured `manual_positions` builder with CoinGecko asset ID, symbol and quantity fields, add/remove/edit controls, canonical payload preservation and advanced JSON retained for integration-specific fields.

### F3 Position & Liquidation

Live F3 source exposes the actual required evidence inputs: collateral oracle feed, collateral/debt units, liquidation threshold, optional debt oracle/fallback, optional CoinGecko cross-check and price-conflict tolerance. Required-field gating, canonical request behavior, CSRF and UNKNOWN-safe results are browser-tested.

### F5 Treasury Allocation & Scenario

Live F5 source has a structured allocation ledger for asset ID, symbol, weight and stablecoin classification, bounded to 50 rows. Entered weight totals are explicit and Rivexis does not silently normalize user-entered allocations. The F5 provenance browser assertion now waits for and validates the actual canonical request rather than racing an async route-handler side effect.

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
- requeue truthfully resets queue state but does not claim that delivery will occur;
- the UI explicitly states that continuous threat ingestion and automatic delivery processing are not configured in the compatibility runtime;
- an empty alert list explicitly does not claim that threats are absent;
- action-level Playwright covers alert navigation, durable-state messaging, status mutation, requeue and CSRF.

### Monitor-result alert creation

Production compatibility parity is now closed without weakening evidence integrity:

- the trigger consumes only the persisted canonical B3 analysis referenced by the monitor update;
- the analysis must belong to the same workspace and be a B3 `supabase-edge` result;
- `UNKNOWN` and `NO_VERIFIED_PROVIDER_EVIDENCE` results create zero alerts;
- materiality otherwise matches the provider-capable FastAPI contract: signals, hard blockers or moderate/high/critical severity;
- a canonical event key deduplicates repeat equivalent monitor events per workspace/monitor;
- a repeated event updates the same alert, increments `occurrence_count`, refreshes `last_seen_at` and retains the latest analysis ID;
- synthetic/demo material events are explicitly titled and described as synthetic, not live threat claims;
- cross-workspace analysis references cannot be promoted into an alert.

Rollback-only production verification passed: UNKNOWN produced zero alerts; a material synthetic event created exactly one truth-labelled alert; an equivalent repeat produced one row with occurrence count `2`; a cross-workspace analysis produced no alert; rollback left zero fixture users/workspaces/monitors/analyses/alerts.

## Production backend

Supabase production is the current compatibility backend.

- PostgreSQL 17.6.1; hardened posture retained.
- Core Alembic application schema remains through `0013_auth_email_lifecycle`.
- Supabase Edge `rivexis-api` is **version 8 ACTIVE**.
- Supabase Edge `rivexis-decision-reports` is **version 1 ACTIVE**.
- Supabase Edge `rivexis-alerts` is **version 1 ACTIVE**.
- Existing general, Saved Analyses and organization-membership compatibility bridges remain deployed.
- Production membership migrations 008 and 009 are live.
- Production migration `010_edge_decision_reports` is live.
- Production migration `011_edge_alert_lifecycle` is live.
- Production migration `012_edge_monitor_alert_creation` is live (Supabase migration version `20260928160516`).
- `public.rivexis_edge_decision_report(text,text,jsonb)` and `public.rivexis_edge_alerts(text,text,jsonb)` retain their previously certified SECURITY DEFINER/service-role-only contracts.
- `public.rivexis_edge_monitor_alert_from_analysis()` is owned by `rivexis_migrator`, is SECURITY DEFINER with pinned `search_path=pg_catalog, public`, and grants no direct execute capability to `PUBLIC`, `anon`, `authenticated` or `service_role`; it is invoked only by the enabled monitor trigger.
- The decision/report and alert Edge runtimes retain HttpOnly/Secure/SameSite=Lax browser sessions and CSRF on state-changing operations.
- Direct decision/report Edge `/health` was verified HTTP 200; unauthenticated report access was verified HTTP 401.
- Direct alert Edge `/health` was verified HTTP 200 with `ready`, `supabase-edge`, API `v1`, `production`, `durable-records-only`, and delivery processor `not-configured`.
- Unauthenticated alert access was verified HTTP 401.

No provider evidence was fabricated. Compatibility analysis remains UNKNOWN-safe when verified provider evidence is unavailable.

## Authoritative frontend truth

Authoritative public frontend:

`https://rivexis-web.rudrasingh0718.workers.dev/`

The Cloudflare web Worker still serves the previously certified manual Worker build unless a later deploy is explicitly verified by the build-SHA marker.

**Do not claim the signature UI, newer History/Saved actions, F1/F3/F5 builders, organization-member Settings UI, Decision Desk/report UI or Alerts UI are live on that Worker yet.** GitHub source/CI is materially ahead of Cloudflare production.

A verified deployment workflow now exists at `.github/workflows/deploy-web.yml`. It deploys only after successful CI, targets the existing `rivexis-web` Worker, stamps `NEXT_PUBLIC_RIVEXIS_BUILD_SHA`, and verifies that exact SHA from the public site after deployment. The deployment currently stops before contacting Cloudflare because the GitHub Actions secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` are not configured. The browser Cloudflare session is also unauthenticated. Do not bypass authentication, create an alternate host/account, or expose credentials in source/chat.

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

1. Cloudflare frontend source drift — deployment pipeline is ready, but legitimate Cloudflare credentials are not available to GitHub Actions/browser session.
2. Full provider-capable FastAPI runtime — Cloudflare Container path remains Workers Paid gated.
3. Provider credentials/contracts/licenses — unavailable evidence remains UNKNOWN/unavailable.
4. Owned sender domain — Supabase/Brevo delivery works, but Rivexis does not yet have an authenticated owned sending domain.
5. Automatic alert delivery/continuous ingestion — the compatibility runtime provides durable alert creation/queue controls but no always-running threat ingestion or delivery processor; it must not be presented as continuous threat streaming.

## Immediate next execution target

Continue only with unblocked production work. The most visible remaining gap is authoritative Cloudflare frontend deployment: once legitimate deployment credentials become available to the existing workflow, deploy the exact certified source and verify the public build-SHA marker before claiming the signature UI is live. Until then, preserve the green source and continue backend/product hardening without weakening evidence, authorization or security controls.
