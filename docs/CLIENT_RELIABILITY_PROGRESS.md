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
- Full local browser suite: 135 passed in 6.2 minutes, with no skips or retries. Vinext deployment build passes. CI and production deployment verification are pending at this checkpoint.

## Remaining public-launch gates

- Signup verification arrived in Gmail Spam; password recovery arrived in Inbox. Brevo's actual settings show one verified Gmail sender, a compliance warning, and no authenticated sending domain. This may contribute to unreliable inbox placement. Domain authentication requires an owned domain and DNS access; no purchase or sender change was made.
- Complete production PostgreSQL backup/restore and offered database maintenance remain blocked by unavailable PostgreSQL connection access and local restore tooling. CI fixture restore evidence does not certify production recovery.
- Native wallet extension approval, full fork/state-changing transaction simulation and comprehensive independent institutional financial/security certification remain unverified. Existing supported non-custodial preview boundaries must stay explicit.
- Public launch is not certified institution-ready by these tests. Preserve bounded beta quotas and unsupported states.

## Release / resume

Branch: `fix/bounded-client-requests`. Before release, complete the full browser suite, deployment build and CI. Use the existing native Cloudflare Git integration; independently check the public build marker and authenticated workflows afterward. Do not create a new deployment target or modify production data destructively.
