# RIVEXIS brand system

RIVEXIS means **Risk · Value · Execution · Analysis**. No version suffix appears in the public identity.

The active brand is the approved royal obsidian/graphite palette, with ivory text, restrained teal and bronze accents. Earlier navy/cobalt PNG treatments are archived assets, not the current interface system.

## Vector master and placements
`apps/web/components/brand-geometry.ts` contains the outlined wordmark, woven X ribbons, bridge and outlined identity expansion. `Brand.tsx` renders those same paths inline, with theme tokens; there is no raster upscaling or runtime font substitution. Navigation, workspace rail, auth lockup, footer, compact icon and report identity share this geometry. The public SVG variants under `apps/web/public/brand` are retained for download/social/report uses. PNG variants remain only for consumers requiring raster icons or metadata.

The paths were created in the preceding identity release; this completion preserves and verifies that master rather than inventing another logo. Desktop and mobile visual review found crisp, coherent placements. Vector paths remain resolution-independent; a separate device-matrix/high-DPI screenshot certification has not been claimed.

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
