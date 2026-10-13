# RIVEXIS client reliability and fresh live authentication

Updated 2026-10-13. Continue the existing Worker, database and design.

## Implemented

- A 35-second client deadline now covers session/CSRF recovery, response headers and JSON or export bodies. Caller cancellation remains supported; shorter caller deadlines still apply.
- Timed-out mutations never retry automatically and explicitly disclose that their outcome is unknown. Users must check the saved record or current settings before retrying.
- Empty or malformed CSRF confirmation fails closed before any mutation.
- No financial formulas, protocol coverage, appearance, database policies or existing users changed.

## Verification

- Twelve direct client tests pass: successful authenticated write, stalled read/write/CSRF/JSON/export, shared deadline, cancellation, malformed CSRF, server errors and empty/binary responses.
- Two actual browser regressions pass: stalled workspace access and stalled report loading both exit their loading states and recover after an explicit retry. Requests use fixtures; no production outages were induced.
- Fresh live production authentication certification: 32 checks passed using one clearly labelled QA identity, including signup, verification, login, CSRF rejection, explicit workspace onboarding, preference persistence, input/actor validation, owner export, actual Aave evidence, saving/reloading a genuine financial report, password recovery/replay rejection, retained data, logout and real-browser report restoration.
- Live Aave snapshot block 26183474; server-recomputed saved report block 26183475. The retained report is financial modeling, not execution or a safety guarantee.
- Test passwords, verification/recovery tokens and session cookies stayed in test-process memory and are excluded from repository/evidence artifacts. The QA account and its workspace/report are retained; no existing account password was changed.
- The first post-reset API probe mistakenly reused the test client's pre-reset cookie. Repeating with the new session and the real browser passed; this was a test-client issue.
- Type checking passes after regenerating stale local Next.js route types. Next production build and frontend AST lint pass.
- Full local browser suite: 135 passed in 6.2 minutes, with no skips or retries. Vinext deployment build passes. PR and main CI, including financial/account/retained API checks and the PostgreSQL fixture restore, passed.
- Final existing-production browser suite: 13 passed in 1.3 minutes with no retries or skips. Exact public build marker independently matched the deployment commit.
- Actual browser on the new deployment: Settings theme saved, persisted after reload and restored to Dark; fresh LiquidationGuard showed collateral $29,398.00, debt $14,990.50, health 1.6277 at block 26183637. Ten hypothetical WETH stress scenarios from -50% to +10% on this genuine snapshot matched the independently expected single-collateral sensitivity at displayed precision (tolerance 0.00021). This is not a protocol audit.
- Fresh Defense Planner comparison under -20% WETH, $3,000 capital, $25 assumed fees and target 1.50 found repayment of 2,000 USDT, modeled capital/fee cost $2,022.81 and minimum stressed health 1.5024. Existing bounded-grid/approval/execution limitations remained visible.
- The linked genuine GasGuard preview at block 26183642 returned BLOCKED with insufficient allowance and failed RPC call/gas estimate. It preserved modeled before/after health (1.6277 / 1.8780), disclosed unknown gas fees and did not claim successful execution or sign/submit anything. This proves a real fail-closed workflow, not a successful transaction simulation.

## Remaining public-launch gates

- Signup verification arrived in Gmail Spam; password recovery arrived in Inbox. Brevo's actual settings show one verified Gmail sender, a compliance warning, and no authenticated sending domain. This may contribute to unreliable inbox placement. Domain authentication requires an owned domain and DNS access; no purchase or sender change was made.
- Complete production PostgreSQL backup/restore and offered database maintenance remain blocked by unavailable PostgreSQL connection access and local restore tooling. CI fixture restore evidence does not certify production recovery.
- Native wallet extension approval, full fork/state-changing transaction simulation and comprehensive independent institutional financial/security certification remain unverified. Existing supported non-custodial preview boundaries must stay explicit.
- Public launch is not certified institution-ready by these tests. Preserve bounded beta quotas and unsupported states.

## Release / resume

Implementation PR: https://github.com/rudras777/rivexis/pull/72 (merged).

Source commit: `a5953b1f9eb4a4b091131c3913b020b4c5d9d975`.

Verified production commit: `6a3bf12543af05c1030da6c057a0c0c93f05606d`.

Existing Cloudflare Worker `rivexis-web`: native build `1b2efa70-aca2-4ea3-b5f6-99b38a30f191`, version prefix `b139276c`, Ready in 42 seconds, active at 100% traffic. Public URL unchanged: https://rivexis-web.rudrasingh0718.workers.dev/ . Supabase API remains version 30; no additional backend deployment/schema changes were needed.

GitHub CI: PR `38398277075`, branch `38398202313`, Worker validation `38398276954`, main `38398808775`, main Worker `38398808693`: all success.

Evidence outside repository, in the task's `outputs` directory: `live-auth-recovery-20261013.json`, `client-reliability-browser-results.json`, `client-reliability-final-production-results.json`, `client-reliability-live-scenarios.json`, `client-reliability-cloudflare.txt`, actual live public/portfolio/planner/GasGuard screenshots. Credentials and tokens are excluded.

This final evidence record is on `docs/client-reliability-release-evidence`. No added recurring services or paid upgrades. Previous Worker version `0607c845` and the API29 source rollback archive remain available. No existing production users/data were removed.

Next resume priorities: obtain safe production database backup/restore capability; authenticate an existing owned sending domain if available; complete native wallet/provider and successful fork simulation certification before changing launch status. Do not purchase infrastructure or weaken security to bypass these gates.
