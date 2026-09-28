# Rivexis Current Build State

Last updated: 2026-09-28

This file is the compact continuation point. Newer verified GitHub source, production Supabase state, and the authoritative Cloudflare Worker state override older notes.

## Certified source

- Repository: `rudras777/rivexis`; branch `main`.
- Latest fully certified product source: `cadb6838f1ec55a1f3021ec65bc8b81408e30a67` (`Stabilize Decision Desk request capture`).
- Exact-head CI: `36439141743` — **SUCCESS**.
- Exact-head GitHub Pages: `36439139051` — **SUCCESS**.
- The full gate passed invariants, secret/migration checks, PostgreSQL migrations/runtime controls, API lint/tests/audit, Edge typecheck/tests, web typecheck/build, vinext build, npm audit and the complete Playwright browser suite including the canonical Decision Desk and JSON/HTML/PDF report workflow.
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

Decision/report parity is now implemented and certified rather than simulated:

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

Key report milestones include `310005ea826479c52b10771de3d454c0277f6477`, `2567f032dae1fd0fa40d905471807caa74b6bc42`, `246cf753d3fcd76a6153d341b475b0848c2f8527`, `af115e622cf703ed7dc803bc3b1757b3019c18b3`, `7fe6c7e997084f7b3db83e7a71afdc704a96c9b8`, `1391cb022f2a7cfdf90b9f7ea8a96394df682463` and certified head `cadb6838f1ec55a1f3021ec65bc8b81408e30a67`.

## Production backend

Supabase production is the current compatibility backend.

- PostgreSQL 17.6.1; hardened posture retained.
- Core Alembic application schema remains through `0013_auth_email_lifecycle`.
- Supabase Edge `rivexis-api` is **version 8 ACTIVE**.
- Supabase Edge `rivexis-decision-reports` is **version 1 ACTIVE**.
- Existing general, Saved Analyses and organization-membership compatibility bridges remain deployed.
- Production membership migrations 008 and 009 are live.
- Production migration `010_edge_decision_reports` is live.
- `public.rivexis_edge_decision_report(text,text,jsonb)` is owned by `rivexis_migrator`, runs as SECURITY DEFINER with pinned search path, grants execute only to `service_role`, and grants no execute capability to `anon`, `authenticated` or `PUBLIC`.
- The decision/report Edge runtime retains HttpOnly/Secure/SameSite=Lax browser sessions and CSRF on state-changing operations.
- Direct decision/report Edge `/health` was verified HTTP 200 with `ready`, `supabase-edge`, API `v1`, `production`.
- Unauthenticated report access was verified HTTP 401.

No provider evidence was fabricated. Live compatibility analysis remains UNKNOWN-safe when verified provider evidence is unavailable.

## Authoritative frontend truth

Authoritative public frontend:

`https://rivexis-web.rudrasingh0718.workers.dev/`

The Cloudflare web Worker still serves previously certified manual Worker version `e8922aac-cb84-435b-bd0c-38fbb886be57`.

**Do not claim the newer institutional UI, History/Saved actions, F1/F3/F5 builders, organization-member Settings UI, Decision Desk or decision-report UI are live on that Worker yet.** GitHub/CI/Pages source is materially ahead of Cloudflare production.

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

## Immediate next execution target

Close the next unblocked **monitoring/alerts operational parity** gap. Audit the existing FastAPI alert lifecycle against the Supabase compatibility runtime before exposing any alert-management UI. Prioritize durable authorized alert list/status, retry/requeue/delivery-state semantics and truthful service availability. Add backend parity first where required; expose UI only after the production contract exists and action-level coverage proves workspace isolation, permissions and CSRF. Do not imply continuous provider threat streaming unless a real configured provider contract exists.
