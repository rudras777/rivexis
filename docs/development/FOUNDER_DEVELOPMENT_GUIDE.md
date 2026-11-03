# Founder development guide

Start with ordinary Git, a text editor and Node 24/npm 11, matching the current CI and observed local toolchain. Python 3.13 is used by CI for the retained Python/backend checks. The source does not require an AI service. macOS/Linux commands below are standard workflows; fresh macOS execution has not been certified in this Windows session.

## Clone, install and preview

```sh
git clone https://github.com/rudras777/rivexis.git
cd rivexis
npm ci
npm run dev:web
```

Open `http://localhost:3000` (or your selected port). The server binds to loopback only; the current Next development route handler normalizes its request origin to localhost. The wrapper forces same-origin API calls and disables external upstream forwarding. This permits landing/UI work without production user data. Authentication and financial requests intentionally return unavailable unless isolated test fixtures handle them; this is not a complete local Supabase environment. `apps/web/.env.example` documents safe web defaults. The root `.env.example` describes the retained Python backend, not the web quick start.

For another port: `npm run dev:web -- --port 3016`. Stop the process with Ctrl+C. Do not copy a production `.env`, customer database, session cookie or service-role key into this preview.

For retained Python/backend checks, use an isolated environment with Python 3.13, matching CI. On Windows, create it with `py -3.13 -m venv .venv` and activate `.venv\Scripts\Activate.ps1`; on macOS/Linux use `python3.13 -m venv .venv` and `source .venv/bin/activate`. Then run `python -m pip install -e "./apps/api[dev,full]"`, `python scripts/check_migrations.py` and `npm run test:api`. These commands install ranged Python dependencies and validate the retained backend; they do not reconstruct the current Supabase project or migrate production. The default Python 3.11 on the audited Windows host lacked Alembic/SQLAlchemy; the dependency-installed Python 3.13 CI migration/API checks passed. Fresh macOS installation remains unverified.

## Find the right file

| Change | Start here |
|---|---|
| Page text / routing | `apps/web/app` and the component imported by that page |
| Navigation | Existing workspace/public navigation components in `apps/web/components`; search the visible label before editing |
| Colors / layout | Existing `apps/web/app/globals.css` and brand components; preserve approved identity |
| Settings | Existing Settings components, preference schema and `account-preferences.mjs` |
| Client API / request handling | `apps/web/lib/api.ts`, `edge-api-proxy.ts` and existing hooks/providers |
| Financial mathematics | `supabase/functions/rivexis-api/defi-*` canonical modules and their adjacent tests |
| On-chain evidence | Existing RPC/oracle adapters and `onchain-http.mjs` |
| Database | DATABASE.md, Supabase migration register and retained `apps/api/alembic`; do not guess a production baseline |
| Email | Supabase Auth templates/SMTP configuration; Brevo is the existing transport and delivery-log source |

Use `rg` or your editor's search to follow imports and callers. Editing a similar-looking legacy file may not change the live product. Keep domain math out of duplicated UI formulas.

## Work on a branch

```sh
git switch main
git pull --ff-only
git switch -c feature/clear-description
# Edit the relevant source and tests.
npm run test:defi
npm run test:api-edge
npm run typecheck:web
npm run lint:web
git diff --check
git add <specific-files>
python3 scripts/secret_scan.py
git commit -m "fix: describe the actual behavior change"
git push -u origin HEAD
gh pr create --base main
```

On Windows use `python` if that is the installed command. Never stage a whole output/recovery directory. A failed check is evidence to inspect, not an instruction to weaken an assertion.

## Browser and Worker checks

```sh
npm run build:web
npm --workspace @rivexis/web exec -- playwright install chromium
npm run test:e2e
npm run build
```

The browser suite starts its isolated local server with external upstream blocked. Fixture data must remain labeled hypothetical. The Worker build generates the static landing artifact/manifest; do not replace it with a raw framework rebuild before deployment. Firefox/WebKit compatibility uses the existing `test:compatibility` workspace command and pinned Playwright browsers. Linux browser system packages may require the supported Playwright installation step used in CI.

`npm run typecheck:web` regenerates Next route declarations and runs a fresh compiler check, avoiding stale incremental diagnostics after dependency/compiler changes. Keep custom framework declarations in `apps/web/types/vinext.d.ts`; `next-env.d.ts` and `.next` are generated outputs. Do not hand-edit or commit them to repair a stale cache. Dependency-security scope and the unused Node image-rendering limitation are recorded in [the dependency follow-up](../governance/DEPENDENCY_SECURITY_20261103.md).

## Database and email administration

A simple database edit still requires a reviewed migration, disposable validation, recovery planning and authorized production application. Current production history is not fully replayable from this checkout; follow DATABASE.md instead of resetting production to match local files.

For verification/recovery issues, check Supabase Auth origin/callback/template configuration and actual Brevo delivery events. Do not create a second verification service, expose tokens, change the sender, resend repeatedly or reset another user's credentials. A delivered-provider status is not inbox-placement proof.

## Deployment and mistakes

Normal release is protected merge followed by the existing Cloudflare integration. Manual release and exact-SHA verification are in DEPLOYMENT.md. Commands that deploy, migrate, change DNS or credentials affect production and require their documented authorization/gates. There is no safe instruction to deploy every directory in this repository.

Before undoing work, inspect `git status` and the diff. Preserve uncommitted work; prefer a new corrective commit or revert of an identified change over force-push/reset. Incident rollback selects one compatible provider layer, preserving customer data. See OPERATIONS.md for diagnosis and recovery.

Troubleshoot the first failing layer: dependency/Node version and lockfile; syntax/types; local server; origin/auth; quota service; provider evidence; deployment identity. Never substitute invented data to make an error disappear.
