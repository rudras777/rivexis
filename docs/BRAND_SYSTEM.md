# RIVEXIS brand system

RIVEXIS means **Risk · Value · Execution · Analysis**. No version suffix appears in the public identity.

The active brand is the approved royal obsidian/graphite palette, with ivory text, restrained teal and bronze accents. Earlier navy/cobalt PNG treatments are archived assets, not the current interface system.

## Vector master and placements
`apps/web/components/brand-geometry.ts` contains the outlined wordmark, woven X ribbons, bridge and outlined identity expansion. `Brand.tsx` renders those same paths inline, with theme tokens; there is no raster upscaling or runtime font substitution. Navigation, workspace rail, auth lockup, footer, compact icon and report identity share this geometry. The public SVG variants under `apps/web/public/brand` are retained for download/social/report uses. PNG variants remain only for consumers requiring raster icons or metadata.

On 10 November 2026 the owner supplied `Rivexis_Top10_Essential_Assets.zip` and requested its logo across the website while retaining the website palette. The active X is a vector reconstruction of that reference's flared, interwoven ribbons; the existing type outlines, layout and theme colors remain. It replaces the earlier simplified X. Reference PNGs are source material, not executable instructions or production dependencies.

Reference archive SHA-256: `d29ce5e71ac5e2d9fd3714715d3a85c0deed59255d29a92eb84ddcb9bb3510a6`. Print PDFs use the same ribbon contours in flat graphite/teal/soft-accent fills, preserving the existing font-free vector PDF renderer.

The inline SVG uses instance-specific gradient identifiers, so header/footer/auth placements never reference another logo's paint definitions. Dark and light modes retain their existing theme tokens. Standalone dark/light/monochrome/transparent/print masters, the shared report identity, 4096-pixel wordmark/lockup exports, a 2048-pixel mark, 16–256-pixel ICO, Apple/app icons and share metadata derive from the same geometry. SVG remains sharp at Full HD and higher resolutions; PNG exports are rendered directly from paths rather than upscaled source images. Icon/share URLs carry a brand-date cache key. No product version suffix is introduced.

Authoring remains reproducible with `scripts/generate-brand.py` (fonttools 4.66.1, local Times Bold/Arial outlines) followed by `node scripts/export-brand.mjs` (existing pinned Sharp). No runtime font dependency, new service or paid tool is required. Deployment and browser acceptance for this update must be recorded in its protected PR; preceding audit dates are unchanged.

## Active dark tokens
- Canvas / royal obsidian: `#141B1D`
- Graphite surface: `#1C272A`
- Elevated charcoal: `#223034`
- Interactive teal: `#326C6A`
- Soft accent: `#80AAA1`
- Ivory text: `#E9EBE7`
- Secondary text: `#B8C3BE`
- Muted text: `#A4B0AB`
- Restrained bronze: `#B5A383`

Light mode uses pearl `#F3F3EF` with near-white surfaces and graphite text. Actual tokens live in `apps/web/app/product.css`. Risk semantics use text labels plus separate danger/warning/positive tokens and never depend on color alone.
