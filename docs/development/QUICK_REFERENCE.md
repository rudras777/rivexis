# Development quick reference

| Task | Command / location | Scope |
|---|---|---|
| Install | `npm ci` | Local locked dependencies |
| Safe UI preview | `npm run dev:web` | Local; production API forwarding blocked |
| Financial regressions | `npm run test:defi` | Deterministic fixtures |
| API regressions | `npm run test:api-edge` | Local contracts/authorization |
| Types / syntax | `npm run typecheck:web`, `npm run lint:web` | Local |
| Browser fixtures | `npm run build:web`, `npm run test:e2e` | Isolated local server |
| Worker artifact | `npm run build` | Local build; not deployment |
| Scan staged/tracked source | `python scripts/secret_scan.py` | No untracked recovery traversal |
| Review | `git diff`, `git diff --check`, `gh pr checks <number>` | Read/review |
| Release | Protected PR merge; existing Workers Builds | Production changes |
| Manual frontend recovery release | `gh workflow run deploy-web.yml --ref main` | Production; inspect source/checks first |
| API / database | DEPLOYMENT.md / DATABASE.md | Separate controlled operation |
| Incident | OPERATIONS.md | Layer-specific diagnosis and rollback |

Do not run the archived API deployment configurations, raw framework deploy/rebuild shortcuts, database resets or credential/DNS changes as routine setup. Current guides and engineering standards take precedence over dated experimental notes; preserve the notes as history.
