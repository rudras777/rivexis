# Footer motion control — 25 October 2026

The owner requested removal of Motion preferences from the end of the site after the alternating layout release. Baseline production is `40f2483eac246bdfd1e318eb8c52d956d49a4f3b`, existing Worker `rivexis-web`, version prefix `6552821d` at100%.

Only the shared public-footer Motion preferences component is no longer rendered. The landing footer heading becomes Trust, matching its remaining Security & privacy destination. Resource links and About remain; the previously removed GitHub source link stays absent. No replacement floating pause button is added.

Existing Settings → Appearance → Motion Preferences and Accessibility → Motion remain available after login. Existing secure account preference persistence, local appearance cache, device reduced-motion handling, forced-colors/data-saving/limited-CPU fallbacks and animated background implementation are unchanged. The alternating feature sequence, brand, hero, diagrams, financial models, authentication, data and infrastructure remain unchanged.

Existing tests replace obsolete footer-button interactions with checks for absent public controls, device reduced-motion transitions, server-rendered/no-JavaScript footers and persisted Settings motion choices. The Settings test saves reduce, checks pause across public navigation/reload, restores system and checks animation/device behavior. Fixture writes remain in isolated mocked account routes; no production account preference changes are needed for this presentation-only release. Browser coverage remains336 fixture cases per engine and30 actual-public cases per engine.

Build/types/AST, focused tests, all exact-head CI/Worker/compatibility gates, same-Worker rollout and actual-public checks must pass. Capture final footer proof and preserve earlier evidence separately. Record exact final source/merge identities, gate outcomes and screenshots in this PR and the task checkpoints; do not add a runtime release merely to record its own identity. This change does not broaden institutional operating certification.
