# Rivexis Current Build State

Last updated: 2026-09-25

This file is the compact resume point for the dedicated normal-ChatGPT production-build program. Runtime evidence and current `main` override older historical wording.

## Repository and certification

- Repository: public `rudras777/rivexis`; branch `main`. Repository visibility was not changed.
- Latest certified application head before this state sync: `d6f7f96d695fd6e388da7518f810f7e230e13487` (`Wire transactional email into API container runtime`).
- CI #363 (`36049102754`) passed the complete matrix on that head: API ruff/pytest/pip-audit; web edge/web typechecks, Next build, vinext build, npm audit and Playwright E2E; invariants/secret/migration checks; PostgreSQL migration, distributed runtime-control certification and migrated-schema verification.
- GitHub Pages deployment #34 (`36049101430`) also passed on the same head. Pages remains a fallback/navigation surface, not the authoritative application runtime.

## PostgreSQL migration 0012

Migration `0012_postgres_performance_hardening` is fully repository/CI certified. CI #361 failed only because the old migrated-schema verification step embedded fragile SQL inside nested shell quoting after the migration and distributed-control certification had already succeeded. The repair moved those assertions into `scripts/verify_postgres_migrated_schema.py`; CI #362 (`36046845220`) then passed all lanes, and CI #363 re-certified the same migration path.

Production Supabase project `ivszvufdonfgwjpfgwii` is `ACTIVE_HEALTHY` in `ap-south-1`, PostgreSQL 17.6.1. Production is still at Alembic head `0011_postgres_runtime_controls`; `0012` is **not** claimed applied.

Production preflight before 0012 established:

- 55 application tables;
- 72 foreign keys lacking a valid leading-column covering index;
- both intended redundant indexes still present: `ix_users_email` and `ix_workspaces_owner_user_id`;
- the four target tenant RLS policies still use uncached per-row `current_setting` evaluation;
- `anon`, `authenticated`, `PUBLIC` and `rivexis_app` have no public application-table grants;
- `rivexis_app` remains standalone, `NOINHERIT`, `NOBYPASSRLS`, without schema CREATE authority;
- tenant/application tables retain RLS/FORCE RLS as designed.

A controlled Supabase management migration attempt failed immediately on `CREATE INDEX` with PostgreSQL ownership enforcement (`must be owner of table alerts`). The transaction rolled back completely: Alembic remained at 0011 and the 72/2/4 preflight counts were unchanged.

The application tables and `alembic_version` are owned by the existing `rivexis_migrator` role. Supabase migration history confirms this role was deliberately created as a dedicated login owner for schema work and then switched to `NOLOGIN`. The restricted Supabase management executor cannot `SET ROLE rivexis_migrator` because role membership has `SET=false`. Rivexis will not broaden ownership/membership/grants to bypass this boundary. Production 0012 therefore requires the existing dedicated migration credential/path to be securely activated for one one-shot `alembic upgrade head`, then disabled again.

## Authoritative backend runtime

The free `rivexis-api` Worker remains an intentional degraded boundary, not the FastAPI application.

The repository already contains the approved authoritative Cloudflare runtime design:

- FastAPI Docker image in `apps/api/Dockerfile`;
- Cloudflare Container wrapper in `apps/api/cloudflare/src/index.ts`;
- `instance_type = "lite"` in the production Wrangler configuration;
- runtime `DATABASE_URL` is separate from migration credentials;
- runtime startup explicitly refuses `RIVEXIS_MIGRATION_DATABASE_URL`;
- production defaults force demo adapters off, PostgreSQL distributed auth/provider controls on, direct organization member add off, and schema auto-create off.

Current Cloudflare documentation confirms Containers require Workers Paid. Workers Free remains limited to 10 ms CPU/request, incompatible with Rivexis's deliberate scrypt authentication budget; Rivexis will not weaken scrypt/authentication to fit Free. The existing Container path is the preferred approved-stack backend deployment once the minimum Workers Paid authorization is granted.

## Transactional email / Brevo

Brevo owner-side phone/account verification remains complete. Live sender inspection on 2026-09-25 found one active sender: `Rivexis` using the existing Gmail address. This is not evidence of a Rivexis-owned authenticated sending domain. Template enumeration hit a connector network error during this continuation, so template activation/state was not changed.

Repository transport remains fail closed and does not equate Brevo API acceptance with downstream delivery. On head `d6f7f96d...`, the Cloudflare Container runtime now forwards the complete transactional-email contract when configured:

- `RIVEXIS_EMAIL_PROVIDER`
- `BREVO_API_KEY`
- `RIVEXIS_BREVO_SENDER_EMAIL`
- `RIVEXIS_BREVO_SENDER_NAME`
- `RIVEXIS_BREVO_VERIFICATION_TEMPLATE_ID`
- `RIVEXIS_BREVO_PASSWORD_RESET_TEMPLATE_ID`
- `RIVEXIS_BREVO_TIMEOUT_SECONDS`
- `RIVEXIS_BREVO_SANDBOX`

CI invariants now require these bindings and prohibit `RIVEXIS_MIGRATION_DATABASE_URL` from entering the API runtime Container.

Authentication mail remains **not production activated**. Owned-domain sender authentication, production runtime secrets, sandbox certification, controlled real inbox receipt and delivered/bounced/failed lifecycle evidence remain gates. The current API has signup/login/cookie session/CSRF/logout/revocation, but verification/password-reset HTTP lifecycle wiring is not yet production complete.

## Frontend

The Cloudflare frontend remains the previously certified deployment:

`https://rivexis-web.rudrasingh0718.workers.dev/`

Known certified Worker version: `258a0507-177e-43ae-84da-ebc037d29d03` at 100% traffic. It uses `https://rivexis-api.rudrasingh0718.workers.dev` as API origin. Current source was not unnecessarily redeployed during this continuation. Previous live certification established protected workspace content is withheld while the authoritative API is unavailable and public/auth routes fail safely.

## Milestone F / engine integrity retained

All prior B1-B5/F1-F5 integrity hardening remains intact. In particular F1 remains engine contract `1.2.0`, calculation `f1-live-1.4.0`, with same-block direct `decimals()`/`balanceOf`, canonical ABI uint256 boundaries, caller/on-chain decimal conflict rejection, direct metadata evidence, uint256-bounded RPC quantities and fail-closed incomplete holdings semantics.

Milestone F remains active; evidence/capability depth is not declared complete.

## Current production gates

1. **Production migration 0012:** requires the existing dedicated `rivexis_migrator` one-shot owner connection. Do not grant the Supabase management executor new SET/ownership authority as a workaround.
2. **Authoritative FastAPI runtime:** requires Workers Paid for the repository's existing Cloudflare Container design; do not weaken scrypt/authentication for Workers Free.
3. **Authentication lifecycle:** verification/password-reset endpoint and lifecycle wiring remains incomplete; mail transport/runtime bindings alone are not auth completion.
4. **Brevo production identity/delivery:** Gmail sender is active but Rivexis-owned domain authentication and real delivery lifecycle remain uncertified.
5. **Custom domain:** not yet selected/verified.
6. **Provider licensing/credentials:** remain explicit where applicable; absent evidence stays UNKNOWN/unavailable.

## Next execution order

1. Continue repository-level authentication lifecycle hardening without requiring a new database migration where safe.
2. When the dedicated production migration credential/path is securely available, run the certified one-shot Alembic 0012 upgrade and repeat the full production postflight.
3. When Workers Paid is authorized, deploy the existing FastAPI Container with restricted runtime DB credentials and production secrets, then execute real browser/auth/provider/email certification.
4. Continue the highest-value unblocked Milestone F capability slice in parallel with external gates.
