# Landing diagrams and resources — 24 October 2026

This is a scoped enhancement to the existing landing page. The baseline is deployed PR109, commit `1cb02574bdbfb10a393249812de7248ee5a69941`, on the existing `rivexis-web` Worker. Branch: `design/landing-diagrams-footer-20261024`. Production promotion is conditional on the existing CI, Worker and browser gates; actual final identities/results are recorded in this PR and the local `outputs/ACTIVE_RELEASE_CHECKPOINT.json` and `outputs/LANDING_REFINEMENT_RELEASE_20261024.json`.

## Research and original direction

Public primary pages were reviewed on 24 October, using web retrieval and host-managed browser inspection. The seven requested core sites were also inspected as rendered pages. Some initial animated views were incomplete; no performance or product-certification claims about these third parties are inferred. No competitor artwork, logos, code, text or screenshots are shipped as RIVEXIS assets.

| Reference | Relevant presentation principle |
| --- | --- |
| [Chainalysis](https://www.chainalysis.com/) | Distinguish product evidence, company resources and trust information. The supplied product screenshot uses legible, clearly separated evidence objects. |
| [Tenderly](https://tenderly.co/) | Place transaction context next to its technical effect; label observations and execution boundaries. |
| [Nansen](https://nansen.ai/) | Use one focal product visual and strong separation between explanation and detailed data. |
| [Dune](https://dune.com/home) | Group capabilities by the task they support; keep dense analytics out of introductory copy. |
| [Glassnode](https://glassnode.com/) | Explain analytical coverage and sources alongside financial interpretation. |
| [Messari](https://messari.io/) | Present a small number of coherent research/evaluation/monitoring workflows. |
| [Token Terminal](https://tokenterminal.com/) | Use familiar financial concepts and explicit labels to make blockchain information interpretable. |
| [DefiLlama](https://defillama.com/) | Make data categories explicit; its dense application navigation is unsuitable for this small footer. |
| [Stripe](https://stripe.com/) | Give diagrams breathing room and a clear reading order rather than ornamental complexity. |
| [Plaid](https://plaid.com/) | Connect product purpose to a comprehensible financial flow. |
| [Linear](https://linear.app/) | Restrained dark surfaces and grouped, quiet footer columns. Rendered footer inspected. |
| [Datadog](https://www.datadoghq.com/) | Organize substantial product/resource information into meaningful groups; avoid importing that scale into RIVEXIS. |

These are design observations, not endorsements or integration claims. RIVEXIS uses its own fine teal/bronze strokes, sparse nodes, short labels and existing obsidian/ivory palette. There are exactly three new image assets and no new landing section.

## Three diagrams

All are original static SVGs in `apps/web/public/diagrams/`. Together they are under 5 KB uncompressed. There are no raster layers, scripts, event handlers, external resources, new fonts, dependencies, animation or canvas. Explicit intrinsic dimensions reserve space; images are lazy-loaded and asynchronously decoded below the hero. Each has an embedded title/description and a meaningful HTML alternative description. Text is 26 SVG units, giving approximately 14.7 CSS pixels at the narrowest tested 272-pixel rendering. An opaque brand-colored ground preserves contrast in both existing themes. Meaning is conveyed by labels and connections, not color alone.

- `liquidation-inputs.svg`: collateral weighted by liquidation threshold and debt converge on a health factor. Its Aave-specific interpretation is explicit in alternative text. The existing canonical hypothetical example, proportional health axis, threshold and rounding remain unchanged. This is neither a liquidation forecast nor observed account data.
- `transaction-assessment.svg`: a proposed call branches into balance, allowance and fee checks, then converges on modeled position effects. No success checkmark, wallet signature, transaction submission or universal-contract simulation is implied. The existing four explanatory steps and uncertainty disclosure remain.
- `defense-branches.svg`: a capital budget branches into repayment, collateral addition and combined alternatives. The existing model-calculated comparison, target, allocation, assumed fees and bounded-search limitations remain. The branches do not claim feasibility for every wallet, guaranteed safety or a global optimum.

The diagrams occupy the existing feature sections. They supplement, rather than flatten into a static graphic, the existing model-derived accessible text. Hero, logo, navigation, buttons, typography system, background, section order, financial kernels and authenticated workspace are preserved.

## Footer and link integrity

Only the landing page opts into the enhanced footer. Other public pages retain their existing footer. Resources: Methodology, Documentation, existing account-gated Educational demo. Company: About RIVEXIS and the real public [GitHub repository](https://github.com/rudras777/rivexis). Trust & preferences: Security & privacy and the existing functional motion disclosure/control. The non-custody/automatic-execution disclosure remains; the lower line clarifies supported Ethereum coverage and input limitations. No compliance badge, customer count, external trust-center, email address or company claim was invented.

Repository/authorized source search and public LinkedIn search did not establish an official RIVEXIS company page. A personal profile mentioning RIVEXIS is insufficient verification. Accordingly, LinkedIn is deliberately omitted. Add it only after the actual company URL is supplied or independently verified; this is not a blocker for the rest of the release.

The linked security page's obsolete fixed dependency-advisory sentence is corrected to point to dated release evidence. Its disclosed Supabase findings remain. This prevents a newly emphasized resource from contradicting the completed PR108 audit; no security control or backend changes are included.

## Validation and release procedure

New browser checks verify exactly three loaded SVGs, source safety/size, descriptive alternatives, footer destinations and preserved example values in ten viewport/theme combinations (320, 390, 768, 1024 and 1440 pixels in dark/light). A second check exercises actual footer URLs, keyboard motion pause, persistence, resume and device reduced-motion precedence. Existing financial, auth, report, navigation, background, accessibility and provider-failure suites remain authoritative. Dedicated public production tests require the exact deployed SHA and reject guest access to private workflows.

Before screenshots are retained outside Git in the task's `outputs/landing-before-*-20261024.png`. Final live desktop/mobile screenshots, public asset/HTTP verification and completed workflow logs use the `landing-refinement-` prefix. Final evidence must identify the tested candidate, identical-tree merged commit, native Cloudflare build, traffic allocation and exact public build. No production data, credentials or private recovery material belong in these evidence files.

No migration, user deletion, integration replacement, paid service or account configuration change is required. Added recurring infrastructure cost: $0. This frontend enhancement does not upgrade the supported bounded beta into independent institutional assurance, prove sustained provider availability or resolve owned-domain email/inbox placement. Unverified LinkedIn remains the only missing requested footer destination.
