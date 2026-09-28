# Rivexis brand system

The production interface uses the official September 2026 asset package. Its identity expansion is **Risk · Value · Execution · Analysis**.

## Production assets

| File | Role |
| --- | --- |
| `rivexis-wordmark.png` | Public navigation, light-surface footer and white-treated workspace rail |
| `rivexis-lockup.png` | Authentication, verification, recovery and onboarding |
| `rivexis-icon.png` | Favicon, application icon, Open Graph and social metadata |

The deployed files are losslessly resized and transparent-padding-trimmed derivatives of the supplied official PNGs. The supplied favicon and app-icon files were byte-identical, so only one production payload is retained. Standalone X-mark artwork is not used in the interface, backgrounds, workspace rail or metadata. Dark surfaces use a crisp white treatment of the full Rivexis wordmark; light surfaces retain the official navy-and-blue wordmark. Large background-baked logo exports are intentionally not shipped to the application bundle.

## Core tokens

- Brand ink / deep navy: `#081838`
- Structural navy-blue: `#103878`
- Interactive cobalt: `#0b4fcb`
- Interactive cobalt hover: `#073b9a`
- Ice-blue tint: `#eaf2fb`
- Institutional canvas: `#f4f7fa`
- Pearl paper: `#f7f6f2`
- Border: `#d8e2ec`

Semantic decision colors remain independent of the logo palette so `PROCEED`, `MODIFY`, `WAIT`, `AVOID` and `UNKNOWN` retain their meaning.
