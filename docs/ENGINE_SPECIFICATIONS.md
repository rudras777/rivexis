# Engine Specifications

| ID | Engine | Domain | MVP responsibility |
|---|---|---|---|
| B1 | Transaction Simulation | Blockchain | Expected execution, transfers, approvals, state changes, trace/gas/revert evidence |
| B2 | Transaction & Contract Security | Blockchain | Malicious behavior, approval, privilege, exploit and contract-control signals |
| B3 | Real-Time Threat & Monitoring | Blockchain | Emerging transaction, oracle, liquidity, bridge, governance and protocol incidents |
| B4 | Entity & Fund Flow Intelligence | Blockchain | Balances, counterparties, inflows/outflows, labels, clusters and fund-flow context |
| B5 | Cross-Chain Route & Bridge Intelligence | Blockchain | Safety, cost, liquidity, dependency, route complexity and safer alternatives |
| F1 | Portfolio & Exposure | Finance/DeFi | NAV/exposure, concentration, liquidity, PnL and risk contributors |
| F2 | Protocol Risk | Finance/DeFi | Smart-contract, economic, oracle, governance, market and dependency/contagion risk |
| F3 | Position & Liquidation Risk | Finance/DeFi | LTV, health factor, liquidation distance, leverage and stress scenarios |
| F4 | Yield & Strategy Risk | Finance/DeFi | Sustainable vs incentive yield, liquidity, lockup, principal and dependency risks |
| F5 | Treasury Allocation & Scenario | Finance/DeFi | Allocation, liquidity, concentration, policy violations and stressed losses |

Every engine emits the same normalized contract: identifiers/version, status, risk score, data/engine confidence, severity, summary, metrics/signals/warnings, hard blockers, mitigations, safer alternatives, evidence, provider consensus/conflicts, freshness, missing data, provider status and assumptions.

The current engine logic is deterministic demonstration logic unless normalized live-provider evidence is supplied. Non-demo calls without provider evidence fail safely with INSUFFICIENT_DATA rather than inventing a result.
