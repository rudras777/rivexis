# Financial display integrity

18 October 2026. Branch `fix/health-chart-precision-20261018`. Preserve approved design, protocol mathematics and existing infrastructure.

## Actual defect and scope

Genuine deployed PR89 Morpho snapshot26214967 exported raw health **1244815281686282632**. Its headline showed1.244 while its sensitivity readout showed1.245. Recomputing the original zero-shock model at its recorded block time returned the identical raw health. Independent integer formatting gives1.244 /1.2448 /1.244815 at3/4/6 digits; converting the intermediate float and rounding to three digits caused1.245. This is a display discrepancy, not a change to risk arithmetic or a newly commissioned protocol audit. The raw snapshot, screenshot, comparison JSON and failing pre-fix browser case are retained outside the repository.

Charts now carry the raw health string alongside approximate plot coordinates. Readouts, point titles and data tables use the same conservative formatter and saved precision as the headline. Frontier target labels also use raw selected precision. No protocol/model/action computation changed.

The same audit found formatting controls not consistently applied and tiny positive planned values represented as zero. USD grouping now follows saved preferences in observations, market quotes, oracle/boundary prices, alternatives and chart costs. A shared raw-USD formatter preserves existing two-decimal totals, eight-decimal oracle prices and four-decimal boundary references, with explicit positive dust bounds. Token formatting preserves the existing portfolio behavior and extends it to plan/action/sequence labels. Missing decimal metadata is explicitly unavailable rather than guessed. Plot cost coordinates retain all eight USD decimals; decisions and action prefill retain original integer amounts. No CSS/layout/branding or service changes.

## Validation

- The pre-fix browser case reproduced1.245 versus1.244. Known independent80%-threshold/$1-debt accounting fixtures cover values below, equal to and above liquidation and3/4/6 precision. No fixture is represented as a current live observation.
- Added14 financial display cases plus one market preference case. Cases assert matching headline/readout/table/title values; exact target precision; educational classification; grouping across prices/history; positive sub-cent capital, positive token quantities and nonzero transaction prefill.
- **62 focused cases passed**, no failures/skips/retries/flaky cases, including existing chart, market and Settings suites. Both production builds, typecheck and frontend AST passed. Default full browser suite now contains236 cases, alongside existing221 DeFi/API/security/PostgreSQL checks.
- TypeScript first caught missing observed totals in a grouping fixture and optional decimal metadata in Action types. Fixture totals were supplied explicitly and missing metadata is handled honestly; no casts or weakened gates. An intermediate patch target was corrected before building. No failing build was deployed.

Next: full exact-head source/PR CI and Worker gates, merge, existing native Cloudflare deployment, public/authenticated exact build verification, genuine matched health readout/table and saved receipt evidence. Update the checkpoint with actual identities/results only after observing them. Current production remains PR89 until successor verification. No new spending, signing, account or database operation. Existing resource/assurance gates remain explicit; continue independent engineering while owner resource questions are pending.
