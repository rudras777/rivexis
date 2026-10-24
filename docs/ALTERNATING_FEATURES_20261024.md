# Alternating landing features — 24 October 2026

Baseline: PR112, production `45e35d74c708a2139df2edf5dc6bb5d8007ea620`, existing Worker `rivexis-web` version prefix `11c11e2e` at 100%.

The owner requested an alternating sequence across the three existing landing features. At widths of at least 1200px, LiquidationGuard and Defense Planner retain copy on the left and portrait artwork on the right. GasGuard now places artwork on the left and copy on the right, with mirrored column proportions. Explicit grid placement preserves the original copy-first semantic source order. Smaller screens retain stacked copy before artwork. Fluid gutters, transparent figures, final example-data captions, existing hero, logo, colors, typography, controls and animated background are preserved.

The owner also requested removal of the GitHub source link at the end of the page. Only that landing footer link is removed. Existing internal resource/company/trust destinations and motion preferences remain. No replacement social destination is fabricated.

The existing fourteen viewport/theme checks now assert the alternating desktop sequence, column separation and copy-first smaller-screen order. They continue to check portrait geometry, no overflow, frameless surfaces, accessible figure descriptions, model-derived example values and footer resources. Actual-public checks assert the desktop sequence and absence of the source link, with new separately named desktop/mobile screenshots. No financial model, authentication, database, integration, dependency or deployment configuration changes.

Build, AST lint, targeted browser tests, exact-head CI/Worker/compatibility gates, same-Worker deployment, exact public commit and actual production inspection must pass. Record final results in this PR and the task release/active checkpoint without another runtime release solely to record its own identity. Previous evidence remains immutable. This scoped presentation change does not certify unrestricted institutional operations.
