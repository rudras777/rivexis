# Browser storage resilience — 19 October 2026

Candidate branch: `fix/browser-storage-resilience-20261019`. Production remains PR93 until exact-head release gates and live verification pass.

## Reproduced failures and change

Optional workspace/session browser hints were accessed without handling denied storage getters/methods or quota errors. On the prior build, a controlled browser regression reproduced a workspace crash when local storage was denied, and successful server verification was shown as an invalid code when removal of its email hint failed. The original three-probe run retained two failures and one passing explicit-login case; this does not claim every path failed in the baseline.

`browser-storage.mjs` now reads/writes/removes only these optional hints on a best-effort basis, including failures while obtaining the storage object. Workspace loading/switching, onboarding, login/signup, verification and confirmed logout use the helper. It has no memory fallback, credentials, server state or authorization role. Verified sessions still depend on server cookies; blocking cookies themselves is outside this fix. The requested allowlisted destination continues through URL parameters. When an email hint cannot be saved, verification accepts manual email entry. No automatic write retries or duplicate account/workspace creation is introduced.

No financial arithmetic, supported protocol coverage, API34/backend, database, CSS, logo, colors, layout, approved animation or infrastructure changes. The existing safe appearance-cache handlers remain unchanged. A failed optional cache clear is distinct from server logout/revocation evidence; private queries, analysis memory and wallet context must still clear.

## Validation checkpoint

- Original baseline: two reproduced failures / one passing control, with screenshots, video, traces and log preserved outside Git.
- First corrected run: all14 storage fault scenarios passed without retries/skips/failures,14.5seconds. Extended cases cover financial-memory clearing after logout/relogin and rejection of external redirects.
- Both Next and Vinext builds passed. Official Next route generation, TypeScript and final AST167 source checks passed after removal of the temporary probe config. Existing12 API client/deadline cases passed. The initial extensionless helper import failed the Node client test loader; the helper now uses the existing explicit `.mjs`/`.d.mts` pattern and the rerun passed.
- Final focused suite:59 passed in83,228.973milliseconds, including all16 storage scenarios, existing auth/session/Settings/entry checks and responsive accessibility. Zero failures, retries, skips or flaky results. Logs and JSON remain outside Git.
- Full source/PR/main release gates, deployment and actual-public checks remain pending at this checkpoint. Controlled API/browser fault fixtures are not production outage evidence or native-wallet certification.

Existing owner resource/assurance gates remain: sending domain/DNS, actual native wallet permission UI, independent recovery key/full-service recovery, pending privileged backup-token authorization, separately authorized database maintenance and sustained operational assurance. Do not create credentials, upgrade services, transmit recovery keys or spend based on an unanswered question.
