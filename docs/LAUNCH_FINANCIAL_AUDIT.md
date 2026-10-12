# RIVEXIS financial integrity audit — 2026-10-12

## Scope and evidence status

Source review covers Ethereum Aave V3 normal-mode accounting, the bounded Morpho WBTC/USDC 86% LLTV adapter, conditional liquidation boundaries, transaction preview orchestration and the capital-constrained frontier. No financial kernel, protocol threshold, logo or UI design was changed by this audit. This record is local engineering evidence; production deployment and live browser confirmation must be recorded separately by the release owner.

Added `supabase/functions/rivexis-api/defi-launch-scenarios.test.mjs`: **55 passed, 0 failed, 0 skipped**. It includes **13 LiquidationGuard scenarios, 15 GasGuard scenarios tested against each of two orchestration paths (30 tests), and 12 Defense Planner scenarios**. Several scenarios deliberately contain multiple invalid inputs or repeated operations. They are not counted as additional distinct scenarios. All RPC responses in this new file are explicitly synthetic fixtures, never presented as live on-chain holdings. Independent expected accounting is computed from raw quantities in the test reference function, not by importing the implementation's metrics function.

Retained and new financial/backend tests together: `node --test supabase/functions/rivexis-api/defi*.test.mjs` — initially **145 passed**; the final audit rerun, including the release team's concurrently added suites, reports **171 passed, 0 failed, 0 skipped**. Actual stdout is saved outside the repository in `outputs/launch-financial-scenarios.txt` and `outputs/launch-financial-suite.txt` in this chat's workspace.

## Defect corrected

Both `defi-rpc.mjs` and `defi-portfolio-rpc.mjs` previously allowed an empty fee response to produce `PREVIEW_ONLY` with an unknown fee reserve and no missing-fee blocker. They also trusted gas/fee RPC types without validating a positive bigint. They now require a positive bigint gas estimate and positive bigint max fee or legacy gas price. Missing, zero, negative or malformed evidence yields explicit blockers and a null modeled fee cost. A successful contract call may still be reported as successful **at the observed block**, while affordability remains blocked. It does not imply a signed transaction or future inclusion. Legacy gas-price providers remain supported and independently tested.

## Scenario matrix (all passed)

| ID | LiquidationGuard |
| --- | --- |
| LG01 | Independent baseline collateral/debt/health accounting |
| LG02 | 50% collateral crash crosses liquidation threshold |
| LG03 | Debt-token price increases 25% |
| LG04 | Simultaneous collateral decline and debt-price increase |
| LG05 | No debt has no finite health factor |
| LG06 | Exact health-factor 1 boundary |
| LG07 | One-unit debt dust valuation rounds up |
| LG08 | Invalid shock, non-finite shock, unknown asset, malformed input |
| LG09 | Stale and future snapshot rejection |
| LG10 | Twenty repeat operations preserve inputs and results |
| LG11 | Mixed liquidation thresholds preserve weighted numerator |
| LG12 | Provider outage fails without a fabricated snapshot |
| LG13 | Stale oracle is unsupported even with a fresh chain block |

| ID | GasGuard — each run against Aave and portfolio orchestration |
| --- | --- |
| GG01 | Successful withdrawal, exact health and fee reserve |
| GG02 | Repayment decreases debt with exact health effect |
| GG03 | Existing-collateral supply increases adjusted collateral |
| GG04 | Borrow increases debt without crediting collateral |
| GG05 | Missing token allowance produces blocker |
| GG06 | Insufficient token balance and native gas balance |
| GG07 | Over-withdrawal, over-repayment, zero and unsafe amounts |
| GG08 | Unsupported asset and action |
| GG09 | Contract-call and gas-estimate provider failures |
| GG10 | Wrong network, stale block and final-read reorganization |
| GG11 | Repeated preview preserves exact inputs and outputs |
| GG12 | Withdrawal crosses liquidation threshold and is blocked |
| GG13 | Missing, zero, negative and malformed fee responses |
| GG14 | Missing, zero, negative and malformed gas responses |
| GG15 | Legacy gas-price provider produces independently checked fee |

| ID | Defense Planner |
| --- | --- |
| DP01 | Target feasible within real wallet/budget constraints |
| DP02 | Already-satisfied target selects zero-cost no-action baseline |
| DP03 | Zero capital cannot meet a higher target |
| DP04 | Fee reserve exceeding budget rejects |
| DP05 | Insufficient native ETH withholds actions |
| DP06 | Empty token wallets cannot create capital |
| DP07 | Invalid target, budget and unsupported objective |
| DP08 | Severe market stress truthfully leaves target unachievable |
| DP09 | Two independent positions share token balances without netting |
| DP10 | Ten repeated comparisons are deterministic and non-mutating |
| DP11 | Stale and unvalidated oracle evidence fails closed |
| DP12 | Every displayed alternative reconciles against independent raw-action accounting |

## Protocol math and retained validation

Aave normal-mode collateral base amounts floor and debt base amounts ceil. The health numerator retains the per-reserve liquidation-threshold weighting, uses half-up wad division, then divides by 10000. This matches the reviewed [Aave Origin GenericLogic](https://github.com/aave-dao/aave-v3-origin/blob/main/src/contracts/protocol/libraries/logic/GenericLogic.sol). Current source references can evolve; runtime modeling also validates the observed Pool implementation and reconciles reserve totals with same-block Pool account data.

Morpho uses virtual borrow shares of 1,000,000 and one virtual asset, upward-rounded debt share conversion, accrued market interest, and two separate floors in native-loan liquidation health. This follows reviewed [Morpho SharesMathLib](https://github.com/morpho-org/morpho-blue/blob/main/src/libraries/SharesMathLib.sol). Retained tests check actual captured EVM accrual states, adjacent-unit withdrawal boundaries, oracle component identities/bytecode/timestamps, repayment share costs and mixed-protocol shared-token constraints. These are replayed captured references, not a claim of fresh current live data.

All financial arithmetic uses bigint. Pinned-block RPC evidence includes a final hash check. Snapshot modeling expires after three minutes; validated oracle heartbeat limits remain asset-specific. eMode, isolation, stable debt, unvalidated oracle sources and Pool upgrades remain unsupported instead of being silently approximated.

## Chart findings for the release owner

At initial audit, the existing frontier and liquidation graphics were model/scenario visualizations, not continuously updating market history. The workspace had a freshness clock and manual refresh; charts should never imply that these values are live streaming prices. The release owner is implementing market-feed and bounded monitoring changes separately. Any added time series must preserve source, timestamp, block identity where applicable, stale/error states and the distinction between executable market price and protocol-oracle valuation. Historical receipts are point-in-time account evidence; they are not a continuous market-price database.

The new chart scenario investigation found a per-position selection defect in `PositionCharts`: selecting the first collateral globally could label Morpho sensitivity with another protocol's token. The release owner corrected it to select eligible collateral within each position. The captured-reference browser test now verifies Morpho **WBTC** sensitivity and explains why captured Aave WETH, which is not enabled as collateral, has no eligible sensitivity curve.

`apps/web/e2e/launch-charts.spec.ts` adds **13 distinct Chromium end-to-end chart scenarios**, all passing against the coordinated owned local Next build in **50.8 seconds**. Scenarios cover captured Aave/Morpho replay, no debt, no collateral, stale evidence, unsupported oracle evidence, educational labeling, debt-price stress/reset with exact displayed values, zero-capital planner, debt-free planner, keyboard scatter selection, same-block deduplication/distinct-block history, wallet-history reset, and mobile overflow/accessible data-table checks including an axe scan. Initial run passed 12/13; the remaining failure was an incorrect test assumption that the captured Aave WETH was enabled as collateral. After correcting that assertion, the complete rerun passed 13/13. Initial failure evidence is retained, not hidden.

Browser result artifacts: `outputs/launch-chart-results-final.json` and `outputs/launch-chart-artifacts-final`. These browser responses are synthetic fixtures or captured evidence replay, never fresh production feeds. Live production certification remains the release owner's separate gate.

## Launch limits and readiness

This audit supports a **bounded beta** for validated Ethereum/Aave normal mode and the single validated Morpho market. It does not certify unrestricted public production across arbitrary chains, tokens, protocols or transactions. GasGuard performs independent `eth_call` and gas estimation, not a combined multi-action state fork. The frontier enumerates 5% budget increments and at most two actions, not a global optimum; future interest, liquidity, caps, approval costs and governance can change feasibility. Unknown ETH price retains explicit gas-affordability uncertainty. Contract inspection does not verify arbitrary source or ABI. No signing or custody is added.

The 55 new tests establish realistic **fixture** coverage. Fresh live RPC, authenticated browser workflows, deployed API parity, vendor wallet permission UX, launch quotas and performance must be evaluated separately before a final public-launch decision. Do not label this source audit alone as full live certification.
