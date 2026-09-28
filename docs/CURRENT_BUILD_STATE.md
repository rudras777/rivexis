# Rivexis Current Build State

Last updated: 2026-09-28

This file is the compact continuation point. Newer verified GitHub source, production Supabase state, and the authoritative Cloudflare Worker state override older notes.

## Certified source

- Repository: `rudras777/rivexis`; branch `main`.
- Latest fully certified product source: `9dad09ed574911d19d7d2f593445ee0e273a80c7` (`Enforce claim-only organization admission`).
- Exact-head CI: `36434551867` — **SUCCESS**.
- Exact-head GitHub Pages: `36434549905` — **SUCCESS**.
- The full gate passed invariants, secret/migration checks, PostgreSQL migrations/runtime controls, API lint/tests/audit, Edge typecheck/tests, web typecheck/build, vinext build, npm audit and the complete Playwright browser suite.
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

Organization membership parity is now implemented and certified:

- organization IDs are explicit and do not imply access;
- authenticated members can inspect the actual membership list;
- OWNER/ADMIN can manage permitted existing-member roles;
- OWNER-specific and last-owner safeguards remain enforced by the backend;
- new membership is claim-based rather than direct new-user email insertion;
- authenticated users can generate a short-lived organization membership claim;
- authorized organization administrators can accept that claim with a selected role;
- removals require explicit confirmation in Settings;
- action-level Playwright covers role update, claim-based admission, confirmed removal, claim generation, protected request payloads and CSRF.

Key source milestones: `8f101aeeb413e7ac87bcf9c9bff6fe1f4341929f`, `a23183660d5a906cf72c0703250e9809e48796d6`, `55d3a6b6d182caceeb41909c9a3e228f034c6132`, `c32f6ec566d4b91929c547a077160ceaed9804f7`, with certified product head `9dad09ed574911d19d7d2f593445ee0e273a80c7`.

## Production backend

Supabase production is the current compatibility backend.

- PostgreSQL 17.6.1; hardened posture retained.
- Core Alembic application schema remains through `0013_auth_email_lifecycle`.
- Supabase Edge `rivexis-api` is **version 8 ACTIVE**.
- Version 8 includes organization membership routes while retaining the existing HttpOnly/Secure/SameSite=Lax cookie session and CSRF model.
- Existing general and Saved Analyses compatibility bridges remain deployed.
- The organization-membership compatibility bridge is deployed with RLS-backed claim storage, restricted service-role execution and OWNER/ADMIN/last-owner safeguards.
- Production membership migrations 008 and 009 are live.
- Direct Edge `/health` was verified HTTP 200 with `ready`, `supabase-edge`, `v1`, `production` after the version 8 deployment.
- Unauthenticated organization-member access was verified HTTP 401 after version 8 deployment.

No provider evidence was fabricated. Live compatibility analysis remains UNKNOWN-safe when verified provider evidence is unavailable.

## Authoritative frontend truth

Authoritative public frontend:

`https://rivexis-web.rudrasingh0718.workers.dev/`

The Cloudflare web Worker still serves previously certified manual Worker version `e8922aac-cb84-435b-bd0c-38fbb886be57`.

**Do not claim the newer History, institutional UI, Saved Analyses actions, F1/F3/F5 builders or organization-member Settings UI are live on that Worker yet.** GitHub/CI/Pages source is materially ahead of Cloudflare production.

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
5. General analysis-report parity — do not expose report buttons until FastAPI + Edge persistence/rendering contracts are genuinely aligned.

## Immediate next execution target

Close **general analysis-report parity**. Audit FastAPI report persistence/rendering against Supabase Edge, add only a real production-compatible contract with workspace authorization and truthful evidence/demo labeling, and expose web report actions only after backend parity and action-level coverage exist. Otherwise keep the action unavailable rather than simulate it.
