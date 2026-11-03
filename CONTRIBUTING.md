# Contributing

Read [engineering standards](docs/architecture/ENGINEERING_STANDARDS.md), [architecture](ARCHITECTURE.md), and the [founder guide](docs/development/FOUNDER_DEVELOPMENT_GUIDE.md).

Start from current `main`, create a short feature/fix branch, make one reviewable change, run relevant tests and stage named files. Use normal pull requests and protected merge. Required checks: `api`, `web`, `invariants`, `postgres-migrations`, `validate-worker-bundle`, `validate-cloudflare-default-root`; strict up-to-date status and admin enforcement remain enabled. No approving-review count is currently required; that single-maintainer limitation is not independent review.

CI runs for pull requests and `main`, rather than duplicating every feature-branch push and PR. The verified frontend release path is the existing main-only `deploy-web.yml` workflow, used for PR125/126 after release gates passed. Historical Workers Builds configuration is retained; its current account-wide triggers remain unverified. Never use `--admin`, force-push shared history or treat a skipped job as application acceptance.

Use locked npm dependencies, preserve security overrides and generated type contracts, and update current documentation with code. Run `python scripts/secret_scan.py` after staging. It scans tracked working-tree files, not untracked local credentials or recovery outputs; it does not certify all possible secret formats or Git history. GitHub native protection supplements this bounded check.

Keep dated evidence and required license notices. Do not add new services, empty architectural folders or an AI-specific maintenance dependency. Releases must identify tested source, actual deployed source, relevant migrations, remaining risks and rollback.
