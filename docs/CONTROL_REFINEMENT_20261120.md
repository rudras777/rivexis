# Control and copy refinement — 20 November 2026

Implemented on `feature/control-refinement`; not merged or deployed. The owner requested Hypurrscan-like button layout and smoothness, plus removal of unnecessary wording and lines. This is a presentation change on top of frontend release `f1da438a`; inactive API44 and the database/worker/email activation holds are unaffected.

## Design and scope

The public [Hypurrscan dashboard](https://hypurrscan.io/dashboard) was inspected through the bundled Browser. Its flat controls, 4px corners, compact action groups, selected fills and restrained transitions informed the design. No reference-site code, assets, market data or branding is copied into Rivexis.

`apps/web/app/controls.css`, imported after existing page styles in the root layout, defines the shared control geometry: 40px desktop actions, 44px mobile actions, 4px corners, flat primary/secondary/quiet/destructive states, 160ms color/border transitions and visible keyboard focus. OS and account reduced-motion preferences, larger text and forced colors remain supported. Layout dimensions do not animate. Existing theme colors, logo, typeface, destinations, disabled states, request handling and financial calculations remain intact.

Coverage, address and wallet inspection now share a row on desktop; secondary actions sit beneath. Mobile stacks the inputs and keeps actions usable. Public/workspace navigation, settings and analysis tabs use the same selection vocabulary. Workspace category labels are shorter while their descriptive accessible names and destinations remain unchanged. The redundant sticky workspace strip separator and repeated decorative labels are removed. No new interaction library or runtime state machine is introduced; the decorative cursor listener is removed.

Landing, product, account-entry and financial-workspace copy is shorter. Repeated slogans and explanatory filler are removed. Financial source/coverage labels, hypothetical-data labels, unavailable/stale states, consent/permission messages, calculation assumptions and execution limitations remain explicit. Existing copy-dependent test assertions are updated without weakening their behavior checks.

## Verification and rollout

Run the existing frontend AST check, type check, production build and browser suites. Verify the actual compiled CSS, desktop/mobile geometry, both themes, grouped-menu click/Escape behavior, settings keyboard tabs, sample workflow, disabled/loading controls and reduced motion using synthetic local fixtures. Preview blocks production API forwarding and contains no production accounts or records. Record exact-head CI and screenshots in the implementation PR/delivery evidence; earlier release results do not certify this candidate.

Local AST/type checks and a production build passed during implementation. An intermediate build rejected a dangling selector left during removal of cursor CSS; that selector was corrected, and the next build passed. The final source/CI and visual results are recorded in the PR. No new tests are added solely to mirror CSS declarations.

Existing axe checks caught a light selected-label contrast regression, and the market-view checks caught lost sticky workspace context; both are corrected with their original assertions retained. A primary-hover contrast check now covers the darker existing hover shade. Firefox also exposed a health-fixture navigation stall: the document was complete with HTTP200, but the driver's DOMContentLoaded wait outlasted an intentionally held health reply. Those clock-driven fixtures now require one HTTP200 document commit and retain all hydration/response/counter/banner/deadline checks. They do not reload the page or loosen the navigation guard.

Use the existing protected PR and automatic frontend release workflow after specific merge authorization. Rollback is a normal revert of this presentation commit through the same protected workflow. No API/function redeploy, migration, credential, DNS, plan, email or wallet action is needed.
