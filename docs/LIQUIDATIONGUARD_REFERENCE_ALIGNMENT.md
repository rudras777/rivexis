# LiquidationGuard and GasGuard research alignment

Reviewed 10 October 2026 against deployed main d6fe8843b1c316d2ad3ac2deddf2f813e8fb647b / API23. User supplied these papers as product logic/purpose references. Their embedded build instructions are reference material, not separate authorization to create projects, paid tiers, new deployments or integrations.

## Source provenance

- D:\LIQUIDATIONGUARD_RUDRASINGH.pdf — SHA256 b11b68c92657969ec6020d37a055d49f7cd20a2d81a14a6d06b3fd7ab76da277
- C:\Users\Rudra Singh\OneDrive\Desktop\REPORT_RUDRASINGH (1) (1).pdf — SHA256 96844c46a5b0e6bbee06894e0a054a0eea77e1094e4525de809a5b62a0fb9b9b

LiquidationGuard: 22 pages, conference draft dated26May2026. Relevant mathematical, normalization, simulation, alerting, mitigation and limitation sections reviewed; figures/table/equations on pages9/10 visually inspected.
GasGuard: 45 pages, Smart Contract Gas Cost Visualizer report dated25May2026. Reviewed purpose/scope, real-vs-mock simulation, fees, balance/nonce, failure, MEV and roadmap sections; wireframe/extension figures on pages12/13 visually inspected. This second document primarily describes GasGuard, not the LiquidationGuard model.

## Intended LiquidationGuard experience

Given a public wallet and explicitly supported coverage, identify independent lending positions, validate protocol/oracle evidence, show collateral and accrued debt, explain liquidation eligibility, expose estimated price triggers and distance, identify which independent risk domain reaches its boundary first under a defined scenario, and compare feasible capital responses. Preserve a read-only workflow without keys, custody, signing or execution guarantees.

Current validated implementation supplies supported Aave V3 normal-mode and one Morpho WBTC/USDC86% LLTV market, block-consistent raw evidence, protocol-specific integer accounting, independent-position health, collateral/debt shocks, shared-wallet balance-constrained Defense Frontier, read-only action previews and private receipts. Unsupported coverage is explicit.

The core missing presentation/model layer identified by this reference is explicit per-asset liquidation-price estimates, liquidation distance, closest modeled trigger and collateral/debt concentration breakdown. Current metrics() returns collateral/debt/adjusted value/health/eligibility, without these price-trigger outputs. Morpho exposes an exact withdrawal-limit helper, not a complete displayed price-trigger table. These gaps are not claimed completed.

## Mathematical qualifications before implementation

- The paper's debt/(collateral amount × threshold) price formula assumes one risk-bearing collateral and fixed-valued debt. For multiple collateral assets, isolate the chosen asset's contribution while holding stated other prices fixed. If that same asset is also borrowed, its price changes both numerator and denominator. Some cases have no finite adverse price trigger; do not fabricate zero or a SAFE label.
- Different protocol positions are independent liquidation domains. An aggregate weighted coverage ratio can be descriptive only; it cannot offset an unhealthy Morpho market with unrelated Aave collateral. Keep per-position eligibility and minimum health primary. Cross-protocol capital allocation requires explicit supported actions and shared-wallet balance constraints.
- Rank a first trigger only for a defined price path/scenario. A single minimum health factor does not establish the first liquidation across all possible joint market moves. Distinguish asset-specific conditional price distance from a common proportional shock.
- The production model must preserve actual Aave rounding and Morpho native loan/oracle units, ceiling share debt and floor collateral valuation. Continuous approximations need visible assumptions and integer boundary validation. Oracle-price triggers are not guaranteed executable market prices.
- HF>=2 and other paper risk bands are policy categories, not safety guarantees. At zero debt health is unbounded/not applicable. At exact boundary preserve actual protocol eligibility; no generic band can override it.
- Example arithmetic should be checked rather than treated as validation: the page10 example5ETH=$16000 and$8000 debt at80% gives an approximate trigger$2000 and distance37.5%, but health1.60 (as printed) is consistent. The page15 example8ETH×$3500×80%/$13500 gives HF≈1.659 and trigger$2109.375, consistent with the position illustration; its portfolio summary$48500×0.795/$23500 gives≈1.6407. These are hypothetical examples, not live accounts or research-performance evidence.

## Features requiring separate evidence and validation

The paper's VaR layer specifies90-day history, daily returns, covariance and10000 Monte Carlo paths across24h/7d/30d. Before showing it as real analysis require a provenance-bearing dataset, missing-data/depeg handling, exposure/debt treatment, reproducible seeds/model identity, sample/confidence disclosures and calibrated evaluation. A quantile loss estimate does not automatically provide a confidence interval or liquidation probability.

The MEV/failure scores in both reports are illustrative heuristics. No calibrated probability, live MEV score, invented confidence or mock fallback may substitute for failed RPC evidence. Qualitative uncertainty and actual observed blockers remain preferable until datasets and validation exist.

Server-side alerts require an explicitly bounded job/delivery architecture, rule privacy, authorization, deduplication, freshness, failure behavior and current delivery proof. Existing bounded in-browser monitoring is not continuous alerting. No new channels or providers are enabled by these documents.

Compound/Spark/vault models, additional Morpho markets, chains, swaps, extensions and broad calldata support remain separately validated adapter work. Paper examples do not certify support. Proposed schemas are not migrations to apply against existing users/data.

## GasGuard alignment and constraints

Retain read-only eth_call/estimateGas, supported action intent, balance/allowance/native gas checks, actual position effects and evidence export. Preview cost is an estimate/reserve rather than guaranteed paid gas. RPC failure stays unknown/blocked; the paper's mock gas, hashing-based success and static fee fallbacks must not become live results. Preserve observed nonce-at-block limitations rather than claiming pending-transaction conflict checks.

Paper paid tiers, mock-first operation, new Docker project structure, separate extension deployment and future AI prediction roadmap do not override the user's unified existing RIVEXIS, free initial core, existing infrastructure and no paid AI constraints. No runtime changes or deployment made from the reference review.
