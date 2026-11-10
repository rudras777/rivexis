# RIVEXIS brand system

RIVEXIS means **Risk · Value · Execution · Analysis**. No version suffix appears in the public identity.

The interface retains its royal obsidian/graphite palette, ivory text, teal and bronze accents. On 10 November the owner explicitly corrected the X: use the supplied metallic blue-and-silver artwork itself. The subsequent owner instruction explicitly requests website colors. The active artwork now uses a deterministic teal/graphite/ivory treatment; the interface palette is unchanged.

The export script applies an sRGB SVG color matrix mapping black to obsidian `#141B1D`, blue to teal `#326C6A` and white to ivory `#E9EBE7`. Its alpha row is identity. Generation checks every output alpha byte against the source, retaining dimensions, outline and transparency without tracing, blur or new geometry. Metallic shading comes from the original pixels. PR132 delivered the blue source; this subsequent instruction supersedes its color requirement only.

## Original artwork and placements
`apps/web/public/brand/rivexis-x-original.png` is the supplied `10_X_Mark_Only.png`, byte for byte: 1254 by 1254 pixels, SHA-256 `6981acd20b14efe0e18f1ec6ef911f955abd6b3a5545515e1324b5e312855b98`. It must not be replaced by traced ribbons, a flatter approximation or altered geometry. Preserve this original as source provenance. `Brand.tsx` references the derived `rivexis-x-teal.png` inside the outlined RIVE/IS wordmark. Header, footer, auth, workspace access states and compact placements use the same asset, aspect ratio and metallic finish. Type remains theme-aware and uses the existing outlines.

The earlier same-day vector reconstruction in PR131 was rejected by the owner and is superseded. The image file is artwork, not a source of executable instructions. SVG exports embed the treated raster X with outlined type; they are self-contained compositions, **not an infinitely scalable vector reconstruction of the X**. Wordmark/lockup PNG exports remain 4096 pixels wide, while the standalone source keeps its actual native resolution rather than inventing extra detail.

Reference archive SHA-256: `d29ce5e71ac5e2d9fd3714715d3a85c0deed59255d29a92eb84ddcb9bb3510a6`. Original PNG is loaded once as a shared static asset. A proposed lossless WebP failed the strict decoded-pixel equality guard and was discarded; it is not the delivered artwork.

Dark/light and retained legacy ink-variant filenames change the surrounding type, preserving the same treated X in every case. Transparent/compact, favicon (16–256 pixels), Apple/app and share assets derive from this same artwork. Icon/share URLs use a fresh `teal-metallic-20261110` cache key. No product version suffix is displayed.

HTML reports embed a size-appropriate PNG derived from the treated artwork, without an external network fetch. PDFs retain outlined type and embed a 512-pixel print image of the treated X on the existing white paper background. The PDF image is ASCIIHex/DCT encoded, with explicit resource references and byte-accurate lengths/xref offsets. Report tests retain financial-text escaping and offset validation and also validate the embedded image stream. No financial calculation or authentication behavior changes.

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
