# RIVEXIS reference atmosphere — verified production release

Date: October 12, 2026 (Asia/Kolkata).
Live website: https://rivexis-web.rudrasingh0718.workers.dev/
Deployed GitHub/main commit: 9d203a1951a00d1f1493d85ed385e9a78bbf7fe2.
Implementation PR61: https://github.com/rudras777/rivexis/pull/61 . Mobile correction PR62: https://github.com/rudras777/rivexis/pull/62 . Both normally merged after all required checks passed.

## Delivered visual behavior

Reworked the existing shared background around the supplied reference: layered flowing teal/champagne threads, illuminated connections, transparent glass-like cubes, ambient light and dimensional motion below the central hero copy. SVG/CSS3D implementation has36 deterministic strands, three slow signals,28 luminous connections,72 small depth points and five cubes; mobile shows two cubes. No old Risk Atlas grid, WebGL renderer, new raster asset, rendering library or animation frame loop. Existing pause/resume, keyboard access, reduced motion, forced colors, SaveData, low CPU and hidden-tab behavior retained.

The hero has space for the reference composition while preserving all original public words, typography, logo geometry and palette. Authentication, workspace navigation, financial logic and integrations are unchanged. Workspace/authentication/Settings use quieter intensity. Cube face names avoid a navigation-style collision; vector motion icons avoid encoding artifacts. Actual390px production screenshot review found a mobile cutoff after PR61: the global SVG max-width rule clipped the wider responsive scene. PR62 fixes that limit and adds real viewport-coverage assertions. Final live screenshot was visually inspected and the cutoff is gone.

## Production proof

Same existing account/Worker rivexis-web and production URL. Final native Cloudflare build be371a94-b265-41ac-83c3-52f7ef2358c3 succeeded. Rollout history independently shows version6d1feae6 at100% traffic. The host browser independently retrieved exact public meta SHA9d203a1951a00d1f1493d85ed385e9a78bbf7fe2 and computed decorative SVG max-width:none. Previous release a873386 and versionf0b492d1 remain in recoverable history.

Final PR CI38234658815 and push CI38234651589, Worker38234658833 succeeded. Main CI38235074578, Worker38235074572, deployment workflow38235074159 and native Cloudflare deployment all succeeded. All ten exact-main check runs reported success. Gates include both production builders, TypeScript/Deno, frontend AST, financial/API/account tests, retained backend tests, security/invariants, migrations, dependency audit and the full90-test browser suite.

Final local Chromium/Edge background suite:16/16 passed, including real traveling-signal movement, cube dimensions, narrow-screen coverage, pause/resume, device accessibility fallbacks, Axe serious/critical checks, no overflow and no accidental financial requests. CI90 browser tests,90 financial/API/account tests and30 retained backend/report/email tests passed. Financial models have no source changes relative to e734af2.

Thirteen real production browser tests passed without mocked API requests and with the exact final commit gate: desktop/mobile rendering, no legacy structure, mobile SVG coverage, motion preferences, public entry/recovery forms, mandatory verified login and protected workspace/API behavior. Two final production4xCPU measurements also passed error/rendering/overflow checks. Authenticated host browser verified retained owner workspace navigation and functional Profile/Appearance Settings UI; no preferences or production identities were changed. Brevo/Supabase configuration and API28 were retained, rather than generating another verification email or redeploying an unchanged backend.

## Performance evidence and practical limits

One synthetic production sample per viewport at4xCPU, no network throttle: desktop LCP2228ms, CLS0, startup long-task time1457ms; mobile LCP2240ms, CLS0, long-task time2294ms. Both LCP elements are H1; zero WebGL draws, page errors and horizontal overflow. TTFB desktop701.8ms/mobile655.1ms. Earlier samples varied substantially with cache/load. These figures do not certify Lighthouse, field Core Web Vitals, all devices or a causal speed improvement. Startup/hydration work remains a performance optimization opportunity.

Background QA verdict for tested Chromium/Edge flows:4/5. Observed controls, accessibility and responsive rendering passed; wider browser/device certification and field performance are outstanding. Actual wallet vendor permission approval remains unverified because no provider is installed in the host browser; fixtures cover provider lifecycle and no-signing behavior. Safari/Firefox not certified. Financial beta remains Ethereum/Aave V3 normal mode plus the single validated Morpho WBTC/USDC86%LLTV market, bounded5%/two-action planning and independent-call GasGuard previews. No universal coverage, global optimum, execution/safety guarantee or automatic transactions.

Retained security findings: public-schema pg_net, leaked-password protection disabled and existing unpatched build-tool braces advisory GHSA-vfj7-8cjw-p6xm. No security setting was weakened or exception expanded. Previous exact33-check real financial reconciliation and actual position/transaction receipts remain valid evidence for the unchanged model sources, rather than new block-current financial results.

## Costs, data and rollback

No new paid service, permanent project, library, texture download, plan upgrade or recurring infrastructure charge introduced. Existing Cloudflare/Supabase/Brevo/RPC configuration retained. Core functionality remains available without payment within existing bounded quotas; no unlimited-free-service promise. No database/API migration, credential change, user deletion, account permission change or production data removal.

Revert the frontend changes through retained Git history or choose the retained Cloudflare version to roll back; API28 remains compatible and unchanged. The prior source/API rollback records remain intact. This evidence-only branch does not trigger another production deployment.

## Saved evidence

Task outputs: cinematic-atmosphere-live-desktop.jpg (actual host browser), cinematic-atmosphere-live-mobile.png (actual production Playwright390px capture), cinematic-atmosphere-live-settings.jpg, cinematic-atmosphere-before-mobile-cutoff.png, cinematic-atmosphere-production-final-results.json, cinematic-atmosphere-performance-final-results.json, cinematic-atmosphere-mobile-correction-background-results.json, cinematic-atmosphere-mobile-correction-ci-web.log and CINEMATIC_ATMOSPHERE_DESKTOP/MOBILE_MEASUREMENTS.json. The host viewport override did not change the page DOM width during mobile capture; its scaled image is deliberately labeled host-viewport-unapplied and is not mobile QA evidence. Use the verified Playwright mobile artifact.

Status: reference-background release completed and verified. Remaining broader product/certification limits are listed above; do not claim every DeFi protocol or financial execution is supported.
