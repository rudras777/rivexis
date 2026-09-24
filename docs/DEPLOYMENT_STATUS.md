# Rivexis Deployment Status

Last updated: 2026-09-25

| Environment | Status | Evidence / meaning |
|---|---|---|
| GitHub repository | PUBLIC / MAIN ACTIVE | `rudras777/rivexis` remains public. Visibility was not changed. |
| GitHub CI | PASS FOR CURRENT APPLICATION HEAD | `d6f7f96d695fd6e388da7518f810f7e230e13487` passed CI #363 (`36049102754`): API ruff/pytest/pip-audit; web typechecks/build/vinext/npm-audit/Playwright; invariants/secret/migration checks; PostgreSQL migration/runtime-control/schema certification. |
| GitHub Pages fallback | PASSING / NOT APP RUNTIME | Pages #34 (`36049101430`) passed on the same head. |
| Cloudflare web | LIVE / PREVIOUSLY CERTIFIED | `rivexis-web.rudrasingh0718.workers.dev`, Worker version `258a0507-177e-43ae-84da-ebc037d29d03`, 100% traffic; current source was not unnecessarily redeployed in this continuation. |
| Cloudflare API Free | LIVE / DEGRADED BY DESIGN | `rivexis-api.rudrasingh0718.workers.dev` remains the honest degraded placeholder; it is not FastAPI. |
| Cloudflare authoritative API design | SOURCE READY / BILLING GATED | Repository contains the FastAPI Docker image and Cloudflare Container `lite` wrapper. Current Cloudflare docs require Workers Paid for Containers. Do not weaken scrypt/authentication for Free. |
| Supabase PostgreSQL | ACTIVE_HEALTHY / PRODUCTION AT 0011 | Project `ivszvufdonfgwjpfgwii`, `ap-south-1`, PostgreSQL 17.6.1. Alembic production head remains `0011_postgres_runtime_controls`; 0012 is CI-certified but not production-applied. |
| Brevo transactional layer | TRANSPORT IMPLEMENTED / NOT ACTIVATED | One active Gmail sender was re-verified. Cloudflare Container now forwards the complete Brevo runtime contract when configured. Owned-domain identity, auth-flow wiring and delivery lifecycle remain uncertified. |
| Production | PARTIAL / BLOCKED ON OWNER MIGRATION PATH + PAID API RUNTIME | Frontend is live, but production DB is one certified migration behind and authoritative FastAPI is not deployed. |

## PostgreSQL migration 0012 production gate

Migration `0012_postgres_performance_hardening` is fully certified in CI. CI #361's failure was only shell parsing in the old verification command; `scripts/verify_postgres_migrated_schema.py` replaced that path and CI #362 (`36046845220`) passed. CI #363 re-certified it.

Production preflight while still on 0011 found 55 application tables, 72 uncovered foreign keys, 2 intended redundant indexes, and 4 target RLS policies still using uncached session-setting evaluation. Public application-table grants for `anon`, `authenticated`, `PUBLIC` and `rivexis_app` were absent; RLS/FORCE RLS and `rivexis_app` NOBYPASSRLS posture were preserved.

A transactional management-API attempt to apply 0012 stopped immediately because PostgreSQL requires the table owner for `CREATE INDEX`. All relevant Rivexis tables are owned by `rivexis_migrator`; the Supabase management executor cannot assume that role because role membership has `SET=false`. The failed transaction rolled back completely and production remains at 0011 with the same preflight counts.

This is an intentional privilege boundary. Do not solve it by broadening ownership, table grants, or SET authority. The repository's intended path is a one-shot Alembic migration through the dedicated migration connection, followed by keeping that credential out of runtime containers.

## Authoritative FastAPI production runtime

The repository's production Cloudflare design is a Container around the existing FastAPI Docker image, not a rewrite into a minimal Worker. The wrapper uses a `lite` container, requires restricted runtime `DATABASE_URL`, `RIVEXIS_AUTH_SECRET` and exact allowed origins, disables demo behavior and schema auto-create, and uses PostgreSQL distributed auth/provider controls.

Current Cloudflare documentation establishes that Containers require Workers Paid; Workers Free remains limited to 10 ms CPU/request. This is incompatible with the existing deliberate scrypt workload before normal database/application work. The application will not reduce password-hashing security to fit Free.

## Transactional email runtime

Head `d6f7f96d...` adds Cloudflare Container pass-through for all existing transactional-email settings while keeping them optional/disabled until production gates are satisfied. CI invariants require the full binding list and explicitly require the migration connection variable to remain absent from the runtime wrapper.

Live Brevo sender inspection returned one active `Rivexis` sender using Gmail. That is not a Rivexis-owned authenticated sending domain. No real email was sent and no template was activated in this continuation; template listing encountered a connector network error.

## Frontend

The live frontend remains on the previously certified Cloudflare Worker version. Previous certification established `/`, `/login`, `/signup`, `/workspace` and key public routes work, unknown routes return 404, and unauthenticated protected workspace content is withheld while the API is unavailable. No frontend production setting was changed during the database/backend work described here.

## Activation gates

- **Migration 0012:** secure owner-capable `rivexis_migrator` one-shot Alembic connection required.
- **FastAPI runtime:** minimum Workers Paid authorization required for the existing Container path.
- **Auth lifecycle:** signup/login/session/CSRF/logout exist; verification and password-reset production lifecycle remains incomplete.
- **Brevo:** owned-domain sender authentication, production secrets, controlled send/inbox receipt and lifecycle evidence remain outstanding.
- **Custom domain:** unresolved.
- **Provider contracts:** credentials/licensing/customer contracts remain required where applicable; unavailable paths stay explicit UNKNOWN/unavailable.
