# Financial request context integrity

## Scope and implementation

Branch: `fix/financial-request-context`. Continue the existing product and deployment without changing branding, layout, financial kernels, database, authentication or infrastructure.

Wallet address edits and explicit wallet selection clear the previous analysis. Sample selection, historical-report restoration, coverage changes and transaction input changes invalidate pending work. Each snapshot, refresh, transaction, report load and report save carries an operation generation. Success, error and loading completion callbacks can update the interface only while the component remains mounted and that generation is current.

An obsolete report save can still complete on the server; suppressing its obsolete interface callback does not cancel or roll back that mutation. There is no automatic mutation retry. Saved reports remain available through an explicit reload.

## Validation

- Production Next build and TypeScript: passed.
- Frontend AST/lint: passed (156 source files).
- Financial/account model suite: 187 passed.
- Added 13 browser regressions holding and releasing network responses: overlapping wallet inspections, sample replacement, eight transaction success/error cases across amount/action/asset/position edits, late refresh errors, overlapping report loads and replaced-comparison saves. These use explicit browser fixtures, not claims of live-chain execution.
- Focused browser suite: 13 passed. Complete 148-test suite passed with zero retries. Branch CI 38425454921, PR CI 38425557607 and Worker 38425557593 all passed.

## Release and remaining gates

PR74 merged: source b2a3d28a3a217e7aab1ca84454b7192c9423fe48; deployed main a6cd48990333bf5e2200126215e6ae6dd3e0f24b. Cloudflare build bd9abe9b-5ca1-47f8-8b76-14294351acd9, version a35b6346, Ready and authoritative traffic meter 100. Independent HTTP and real browser build markers match. Actual production suite: 13 passed with no retries. Genuine authenticated Aave snapshot at block 26184619 showed fresh oracle evidence, collateral $29,567.72, debt $14,988.06 and health 1.637.

Live verification exposed one additional context defect: client route changes preserved the snapshot but left its address field empty. Follow-up branch `fix/analysis-address-continuity` initializes that field from the retained live/historical snapshot before saved defaults or connected addresses. Both route regressions passed, even with a different saved default address; no financial logic changes.

Previous production commit: `d0bc374256697d00c71955705fa2e0ee4db8f5b6`; API31 remains unchanged. Keep its Worker rollback version and API bundle archives.

Existing unresolved institutional launch gates: complete production PostgreSQL backup/restore access, authenticated email sending domain, native-wallet approval testing and combined-action fork certification. Supported live Aave snapshots, individual GasGuard withdrawal simulations and financial reconciliation were verified in `ANALYSIS_RECOVERY_PROGRESS.md`; this frontend fix does not broaden protocol coverage or execution assurances.


## Final verified follow-up release

- PR75 merged. Source `5a23dc034a724ac3451133f8af2e25a6cf441a91`; final deployed main `388ff8fd9780d61e60ea63c160da496a4a68fddc` (includes PR74).
- Existing Cloudflare Worker `rivexis-web`: build `5a7ae2a2-616f-4e3c-b1ce-c6faf8afbeda`, version prefix `6cc941f5`, Ready. Refreshed authoritative traffic meter `aria-valuenow=100`. Independent HTTP and real-browser build markers matched the exact main commit. Existing URL remains https://rivexis-web.rudrasingh0718.workers.dev/ . Previous Worker `a35b6346` remains available for rollback; no overlapping manual deployment.
- Branch CI `38427341118`, PR CI `38427460169`, Worker gates `38427459850`, main CI `38428076964` and main Worker `38428076876` passed. Full CI browser suite: 150 passed. Local focused request-context suite: 15 passed; earlier full local suite: 148 passed. Financial/account suite: 187 passed. Builds, TypeScript, AST/lint, API/Deno checks, dependency/security checks and migration/restore fixtures passed.
- Final actual-production browser suite: 13 passed in 1.5 minutes, no retries or skips. These public/guest tests are separate from browser fixtures and authenticated live verification.
- Used the existing signed-in browser session and existing Production QA Workspace. No credentials requested, session imported, password changed, user deleted or new account created. User's session was preserved.
- Final live Aave snapshot at block 26184686. Started a 0.001 WETH preview, edited the amount while pending, then explicitly requested 0.002 WETH. The exported final result contains amountRaw `2000000000000000`, `SUCCEEDED_AT_BLOCK`, no blockers, block 26184688 and gas 261285. Displayed health 1.640 -> 1.639. No signature or submission. Older results did not reappear under the edited input.
- Navigated transactions -> Risk Scenario Lab -> Defense Frontier through real controls. The inspected address remained visible on both destination pages. Three-minute-old evidence correctly disabled new calculation; explicit refresh restored fresh calculation access.
- Refreshed snapshot block 26184704: keyboard-controlled 20% WETH stress showed health 1.640 -> 1.312. Planner with budget $3000, target 1.50 and assumed fees $25 found five displayed alternatives; the leading repayment was 1936.212668 USDT, total raw modeled budget 195874999910 (display $1958.74), health raw 1506460190965458475 (display 1.506). Separate approval remains required. Independently recomputed all five exported alternatives using integer arithmetic: wallet balances, raw capital, fees, budget constraints, stressed debt/collateral, Aave weighted health and target classifications all matched exactly. This certifies the receipt's modeled arithmetic, not execution or global optimality.
- Genuine network-fee observations advanced while the visible page remained open: four, eight and sixteen actual observed points were shown at successive blocks. Sensitivity curves remained explicitly modeled; historical observations were not fabricated or interpolated.
- Independent earlier 0.001 WETH preview reconciliation at block 26184630/hash 0x43788f6647be03b0dd27f901bc8591b83e44df77ee24bd5494cb4fdce61db6af: oracle priceRaw 251388680000, liquidation threshold 8300 bps. Collateral decreased exactly 251388680 raw USD units; debt unchanged. Both health values matched Aave's retained weighted numerator and wadDiv half-up before basis-point division. Rounded adjusted USD cannot be substituted as the exact health numerator. Fees were at least gas times fee cap and within observed native balance. Reads used the existing ethereum.publicnode.com endpoint with normal TLS validation. An initial probe of a different hostname failed certificate validation and was not bypassed; an initial verification formula using truncated adjusted USD was corrected before reporting successful reconciliation.

## Final artifacts, costs and launch decision

Outside repository in task `outputs`: `request-context-local-browser-results.json`, `request-context-first-production-results.json`, `request-context-cloudflare.txt`, `request-context-live-portfolio.txt`, `request-context-live-gasguard.json`, `request-context-financial-reconciliation.json`, `address-continuity-focused-results.json`, `address-continuity-final-production-results.json`, `address-continuity-cloudflare.txt`, `address-continuity-live-gasguard.json`, `address-continuity-live-gasguard.txt`, `address-continuity-live-gasguard.jpg`, `address-continuity-live-scenario.txt`, `address-continuity-live-planner.txt`, `address-continuity-live-planner.json`, `address-continuity-planner-reconciliation.json`, `address-continuity-public-live.jpg`.

Added recurring cost: $0; no plan upgrade or service added. Existing total account billing is not independently certified. No schema, RLS, authentication, Brevo, API31, financial-kernel, branding or landing-layout changes. The demonstrated frontend integrity defects are fixed; this does not certify an exhaustive independent institutional security audit.

Supported workflows above are live and verified. Institutional public-launch certification remains blocked by complete production PostgreSQL backup/restore access, authenticated email sending-domain/DNS access, actual native-wallet approval testing, and combined-action state-fork certification. Existing Aave normal-mode and bounded Morpho coverage, quotas, bounded planner search and browser-only monitoring limits remain in effect. Do not certify unsupported chains/modes, continuous monitoring, future execution or guaranteed liquidation safety.

Final evidence branch: `docs/financial-context-release-evidence`; docs-only evidence does not require another production deployment.
