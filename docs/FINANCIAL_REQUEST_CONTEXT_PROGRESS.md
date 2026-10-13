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

Live verification exposed one additional context defect: client route changes preserved the snapshot but left its address field empty. Follow-up branch `fix/analysis-address-continuity` initializes that field from the retained live/historical snapshot before saved defaults or connected addresses. Two route regressions pending; no financial logic changes.

Previous production commit: `d0bc374256697d00c71955705fa2e0ee4db8f5b6`; API31 remains unchanged. Keep its Worker rollback version and API bundle archives.

Existing unresolved institutional launch gates: complete production PostgreSQL backup/restore access, authenticated email sending domain, native-wallet approval testing and combined-action fork certification. Supported live Aave snapshots, individual GasGuard withdrawal simulations and financial reconciliation were verified in `ANALYSIS_RECOVERY_PROGRESS.md`; this frontend fix does not broaden protocol coverage or execution assurances.
