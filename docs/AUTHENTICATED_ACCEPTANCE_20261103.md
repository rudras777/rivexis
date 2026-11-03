# Authenticated production acceptance — 3 November 2026

This records genuine interaction in the connected Chrome browser with an existing verified owner session on the original `rivexis-web.rudrasingh0718.workers.dev` production origin. No cookie, password or session token was extracted or transferred to another origin. The custom hostname has a separate sign-in boundary; its authenticated workflow was not repeated in this run.

Application baseline: commit `3c4ce864edf91d22d699ec3dcd43229eb66d944e`, PR123, existing API version39. This acceptance record changes documentation only.

## Verified workflows

- LiquidationGuard inspected the existing public reference wallet using real production API/RPC data at block26333656. WETH, WBTC, USDC and USDT had validated evidence; collateral displayed $67,262.29, debt $54,259.60, observed health1.053. Conditional WBTC distance was5.15%; the WETH-only downward trigger correctly remained inapplicable with other prices fixed.
- Ten consecutive WBTC stress inputs, -1% through -10%, changed displayed health from1.043 to0.949 on the same source position. These are explicit market assumptions, not observed price movements.
- Ten planner budgets ($5 through $25,000) produced responsive, balance-constrained comparisons. An assumed $25 fee reserve correctly withheld transaction alternatives because native ETH was insufficient. With an explicit $0.50 assumed reserve and $3,000 budget under the -10% WBTC scenario, repayment alternatives remained below the chosen1.50 target; the leading displayed outcome was1.005. Fees were assumptions, not execution promises.
- GasGuard blocked the USDT repayment needing separate allowance, with execution unverified. A read-only WETH withdrawal preview of0.000001 succeeded at block26333670:373,345 gas units and0.000057 ETH displayed reserve. No approval transaction, signature or transaction submission occurred. Network fee history visibly grew from4 to12 real observed points as blocks advanced.
- The actual installed MetaMask provider returned public-address access on Ethereum mainnet, chain1. No signing or submission was requested. This verifies a real provider connection using available permission; it does not certify a newly presented permission dialog, denial handling, account switching or network switching.
- All ten Settings sections rendered. A temporary Light theme was saved, confirmed and verified after reload. Dark was then saved and verified after another reload. Density/motion, security settings, identity and financial preferences were preserved.
- Reports initially returned an honest empty list. Exactly one private validation comparison was saved from the public reference position using fresh server evidence. After reload it was retrieved and reopened at its original block26333709, marked HISTORICAL COMPARISON / REFRESH REQUIRED, with new report saves/execution withheld. No existing report was removed. Raw receipt identifier is retained only in local evidence.
- Contract inspection observed the real Aave pool code and EIP1967 implementation at block26333714; the implementation matched the validated `0x728a138A4823392C2EFA55e028d434F526fE03CF`. Unsupported token metadata on that pool was explicitly unavailable. No contract identity was saved and no write was called.

## Evidence and remaining limits

Screenshots, ten-case stress/planner records, Settings section checks and sanitized result captures are retained in task outputs under `auth-live-20261103-*`. No credential, private key, session token or recovery material is included. The existing original-origin user session remains signed in.

The successful GasGuard result was captured on screen. Export-file delivery could not be independently confirmed: the connected browser download-event listener timed out, and browser policy denied `chrome://downloads` inspection. No workaround was attempted after that denial. Automated export tests and actual on-screen result acceptance are separate evidence.

Server-side continuous DeFi surveillance and automated risk email remain disabled. Bounded browser checks are disclosed as bounded; this run does not certify an SLA, sustained load, external operational staffing, independent security assurance or the full native wallet permission lifecycle. Existing Supabase extension/password advisories remain documented limitations; no schema, grant, password or paid-plan change was made.
