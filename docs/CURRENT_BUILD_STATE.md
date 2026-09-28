# Rivexis Current Build State

Last updated: 2026-09-28

This file is the compact continuation point. Newer verified GitHub source, production Supabase state, and the authoritative Cloudflare Worker state override older notes.

## Certified source

- Repository: `rudras777/rivexis`; branch `main`.
- Latest fully certified product source: `6bf117154a958688697cc998530a65c9726e820f` (`Stabilize guided F3 browser contract`).
- Exact-head CI: `36429614693` — **SUCCESS**.
- Exact-head GitHub Pages: `36429614899` — **SUCCESS**.
- The full gate passed invariants, secret/migration checks, PostgreSQL migrations/runtime controls, API lint/tests/audit, Edge typecheck/tests, web typecheck/build, vinext build, npm audit and the complete Playwright browser suite.
- Pages remains fallback/navigation only; it is not the authoritative application runtime.

## Newly completed source workflows

### History

History is now operational rather than passive:

- search by reference/engine/type;
- analysis/decision type filter;
- demo/non-demo analysis filter;
- canonical persisted analysis/decision provenance inspection;
- direct **Save reference** action backed by the real Saved Analyses API;
- workspace-switch isolation and action-level browser coverage.

History was first certified at `55f14c1711dd0de62f8ecf689dbd1822e447c7d8` with CI `36424000229` and Pages `36423999702`; the behavior is included in the newer certified head.

### F1 Portfolio & Exposure input builder

Live F1 no longer requires ordinary users to edit raw JSON for portfolio positions:

- bounded structured `manual_positions` builder, maximum 50 rows;
- CoinGecko asset ID, symbol and quantity fields;
- add/remove/edit controls;
- exact canonical payload preserved;
- advanced JSON remains available for integration-specific fields;
- CSRF, request payload and UNKNOWN-safe result behavior are browser-tested.

The F1 slice was certified at `af4a9bacf06b76427094333433712a10a8e3e79a` with CI `36424620457` and is retained in the latest certified head.

### F5 Treasury Allocation & Scenario builder

Live F5 now exposes a structured allocation ledger:

- CoinGecko asset ID, symbol, weight %, stablecoin flag;
- add/remove/edit controls, bounded to 50 rows;
- explicit entered-weight total review cue;
- no silent weight normalization;
- canonical `allocations` payload preserved;
- advanced JSON retained for integration-specific fields.

The F5 slice was certified at `7313b48ddfbdea13015b0d37646089057e7e12b7`, CI `36425394932`, Pages `36425394525`, and is retained in the latest certified head.

### F3 Position & Liquidation guided live inputs

The UI now matches the real FastAPI F3 evidence contract instead of hiding required fields in JSON:

- required collateral oracle feed is visible and blocks execution until supplied;
- collateral units, debt units and liquidation threshold are first-class fields;
- liquidation-threshold UI ceiling now matches the backend's accepted `<= 1.5` contract;
- optional debt oracle feed and explicit USD fallback are visible;
- optional CoinGecko collateral cross-check is visible;
- price-conflict tolerance is visible;
- exact canonical request, required-field gating, CSRF and UNKNOWN-safe result are browser-tested.

## Production backend

Supabase project: `ivszvufdonfgwjpfgwii`.

- PostgreSQL 17.6.1; hardened production posture retained.
- Core Alembic application schema remains through `0013_auth_email_lifecycle`.
- Supabase Edge `rivexis-api` is **version 7 ACTIVE**.
- Browser sessions remain HttpOnly/Secure/SameSite=Lax with CSRF on state-changing requests.
- `public.rivexis_edge_bridge(text,text,jsonb)` remains the narrow compatibility-runtime bridge.
- `public.rivexis_edge_saved_analysis(text,text,jsonb)` remains deployed for Saved Analyses create/list/archive/restore/delete.
- Saved-analysis bridge owner is `rivexis_migrator`, with SECURITY DEFINER, pinned search path, service-role-only execution, no anon/authenticated/PUBLIC execution, and migrator NOLOGIN posture retained.
- Direct Edge `/health` was verified HTTP 200/ready after version 7 deployment; unauthenticated Saved Analyses was verified HTTP 401.

No Supabase redeploy was required for the History/F1/F3/F5 UI slices because they consume already-existing compatibility contracts and preserve UNKNOWN-safe live behavior.

## Authoritative frontend truth

Authoritative public frontend:

`https://rivexis-web.rudrasingh0718.workers.dev/`

The Cloudflare web Worker still serves previously certified manual Worker version `e8922aac-cb84-435b-bd0c-38fbb886be57`.

**Do not claim the newer History, institutional UI, Saved Analyses actions or F1/F3/F5 builders are live on that Worker yet.** GitHub/CI/Pages source is materially ahead of Cloudflare production.

Deployment remains blocked because Wrangler is unauthenticated and the Cloudflare dashboard remained behind human verification after the permitted safe attempt. Do not bypass verification, deploy to an alternate host, create a temporary account or make an unapproved billing change.

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

Close **organization/member administration parity**. Full FastAPI already supports organization member list/add/claim/remove, while the current Supabase Edge compatibility runtime exposes only organization list/create. Implement a narrow, server-authorized Edge/database contract first, preserving OWNER/ADMIN boundaries and safe membership-claim semantics; only then expose member administration in Settings. If parity cannot be made secure without weakening the current role model, leave the UI unavailable rather than simulate it.
