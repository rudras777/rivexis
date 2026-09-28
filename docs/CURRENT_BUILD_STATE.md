# Rivexis Current Build State

Last updated: 2026-09-28

This file is the compact continuation point. Newer verified GitHub source, production Supabase state, and the authoritative Cloudflare Worker state override older notes.

## Certified source

- Repository: `rudras777/rivexis`; branch `main`.
- Latest fully certified product source: `86a833426f6f6c84f73838417ec4837792b2cada` (`Add truthful alert operations parity`).
- Exact-head CI: `36441192677` — **SUCCESS**.
- Exact-head GitHub Pages: `36441191415` — **SUCCESS**.
- The full gate passed invariants, secret/migration checks, PostgreSQL migrations/runtime controls, API lint/tests/audit, Edge typecheck/tests, web typecheck/build, vinext build, npm audit and the complete Playwright browser suite including Decision Desk/report workflows and alert list/status/requeue truth contracts.
- Pages remains fallback/navigation only; it is not the authoritative application runtime.

## Completed product workflows

### History

History supports search/filtering, canonical persisted provenance inspection, direct Save reference, workspace isolation and action-level browser coverage.

### F1 Portfolio & Exposure

Live F1 has a bounded structured `manual_positions` builder with CoinGecko asset ID, symbol and quantity fields, add/remove/edit controls, canonical payload preservation and advanced JSON retained for integration-specific fields.

### F3 Position & Liquidation

Live F3 exposes the actual required evidence inputs: collateral oracle feed, collateral/debt units, liquidation threshold, optional debt oracle/fallback, optional CoinGecko cross-check and price-conflict tolerance. Required-field gating, canonical request behavior, CSRF and UNKNOWN-safe results are browser-tested.

### F5 Treasury Allocation & Scenario

Live F5 has a structured allocation ledger for asset ID, symbol, weight and stablecoin classification, bounded to 50 rows. Entered weight totals are explicit and Rivexis does not silently normalize user-entered allocations.

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

Alert-control parity is now a real production-backed workspace surface:

- Alerts is a first-class workspace navigation surface separate from manual monitor definitions;
- alert list reads are server-authorized to the active workspace;
- alert states can be changed only by write-capable workspace roles;
- dead-letter requeue requires OWNER/ADMIN management access;
- 24-hour queue metrics expose total, pending/retry, delivered, dead-letter, oldest pending age and delivered-within-SLO percentage;
- requeue truthfully resets queue state but does not claim that delivery will occur;
- the UI explicitly states that continuous threat ingestion and automatic delivery processing are not configured in the compatibility runtime;
- an empty alert list explicitly does not claim that threats are absent;
- action-level Playwright covers alert navigation, durable-state messaging, status mutation, requeue and CSRF.

Production currently contained zero alert rows when this slice was verified, consistent with the UNKNOWN-safe free runtime and absence of continuous live provider ingestion.

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
- `public.rivexis_edge_decision_report(text,text,jsonb)` and `public.rivexis_edge_alerts(text,text,jsonb)` are owned by `rivexis_migrator`, run as SECURITY DEFINER with pinned search paths, grant execute only to `service_role`, and grant no execute capability to `anon`, `authenticated` or `PUBLIC`.
- The decision/report and alert Edge runtimes retain HttpOnly/Secure/SameSite=Lax browser sessions and CSRF on state-changing operations.
- Direct decision/report Edge `/health` was verified HTTP 200; unauthenticated report access was verified HTTP 401.
- Direct alert Edge `/health` was verified HTTP 200 with `ready`, `supabase-edge`, API `v1`, `production`, `durable-records-only`, and delivery processor `not-configured`.
- Unauthenticated alert access was verified HTTP 401.

No provider evidence was fabricated. Live compatibility analysis remains UNKNOWN-safe when verified provider evidence is unavailable.

## Authoritative frontend truth

Authoritative public frontend:

`https://rivexis-web.rudrasingh0718.workers.dev/`

The Cloudflare web Worker still serves previously certified manual Worker version `e8922aac-cb84-435b-bd0c-38fbb886be57`.

**Do not claim the newer institutional UI, History/Saved actions, F1/F3/F5 builders, organization-member Settings UI, Decision Desk/report UI or Alerts UI are live on that Worker yet.** GitHub/CI/Pages source is materially ahead of Cloudflare production.

Cloudflare frontend deployment remains blocked because Wrangler is unauthenticated and the dashboard remained behind human verification after the permitted safe attempt. Do not bypass verification, deploy to an alternate host, create a temporary account or make an unapproved billing change.

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

## Current gates

1. Cloudflare frontend source drift — requires legitimate authenticated Cloudflare access.
2. Full provider-capable FastAPI runtime — Cloudflare Container path remains Workers Paid gated.
3. Provider credentials/contracts/licenses — unavailable evidence remains UNKNOWN/unavailable.
4. Owned sender domain — Supabase/Brevo delivery works, but Rivexis does not yet have an authenticated owned sending domain.
5. Automatic alert delivery/continuous ingestion — the compatibility runtime currently provides durable alert queue control only; it must not be presented as continuous threat streaming or as an active delivery processor.

## Immediate next execution target

Close **monitor-result alert creation parity** without weakening UNKNOWN-safe behavior. The provider-capable FastAPI monitor check can create a durable alert after a material B3 result, while the current Supabase compatibility monitor check only persists the B3 analysis/result. Add a narrow server-authorized compatibility path that creates an alert only from the persisted normalized monitor result when the same materiality conditions are genuinely met, deduplicates safely, and never treats `UNKNOWN`/missing provider evidence as a threat event. Then add action-level coverage proving no alert is manufactured for UNKNOWN results and that a genuinely material synthetic/demo or future live normalized result can persist exactly one authorized alert.
