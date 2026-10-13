# Bounded Morpho defense sequence integration

Updated 2026-10-14, Asia/Calcutta. Preserve existing branding, landing layout, kernel, account, Worker, Supabase project, SMTP and free quotas.

## Scope

One Ethereum WBTC/USDC market, 86% LLTV, exact existing deployment/oracle identity. One or two partial USDC asset-budget repayments and/or WBTC collateral supplies, including exact aggregate allowances. Current native protocol state, observed shares and balances; no signing, submission, overrides or ownership claim. Full closure uses the existing individual share-based preview. Mixed Aave/Morpho sequences remain unsupported and keep their independent-preview disclosure.

Repayment asset amounts are preserved; burned shares can differ from an earlier planner. Current-state success does not certify the stressed target, future prices, fees or inclusion. Morpho health is explicitly labelled protocol-derived from observed shares/collateral/oracle rather than pretending the protocol stores an Aave health factor.

## Real validation

Bounded discovery used the official public indexer once (20 addresses), followed by direct same-block contract and token-balance validation. Only RPC-validated data enters the engine. Public reference 0xbdc3c47122d033ccd1Ad7b986071187Be597fF72 has genuine USDC/WBTC and native gas; ownership is not claimed. No balance override or funding transaction.

Initial real engine probe at parent 26186389: partial 0.01 USDC repayment + 0.001 WBTC supply; six approval/action steps succeeded. USDC 33425 -> 23425 raw; WBTC 3930000000 -> 3929900000 raw; derived health 1273153136109878281 -> 1273163622860287276. Full artifact: task outputs/morpho-sequence-initial-engine-probe.json (not yet deployed API evidence).

Final real certification at parent 26186403: eight actual simulations (partial repayment, collateral supply, repeated repayments, repeated supplies, both action orders, allowance failure yielding BLOCKED, repeated simulation from unchanged parent) and four local guards against that actual snapshot (wallet budget, full closure, samples, stale evidence). All twelve passed. This distinguishes actual RPC cases from local rejection checks. SHA256 f55cb018a472aca7227afd38dd49014707bca13db32296eb0b4e49da3c7596f2; artifact outputs/morpho-sequence-certification.json. Captured first replay in certification-reports/morpho-sequence-reference.json is explicitly historical, not current risk or ownership proof.

## Safety and checks

Shared envelope validation verifies canonical parent, one simulated next block/time, complete statuses, declared gas bounds and return data. Morpho observes actual child-time interest accrual before before/after reads. Successful results reconcile wallet debits, collateral additions, market debt reductions and both market/account share burns to actual repayment return values. Reverts remain BLOCKED; missing observers/accrual, false token/share/debt evidence or provider failures cannot certify success.

Fourteen new deterministic Morpho cases include independent native-unit health recomputation from the actual captured replay. All 218 financial/API/account cases pass. The new pre-quota precision regression initially found a missing early decimal filter; corrected to six USDC/eight WBTC places. Final targeted 29 browser tests pass, including ten Morpho cases for success/export, reverts, 422/429/503, repeated operations, changing inputs and sample withholding. TypeScript, AST, Next build and Deno check pass. Full CI, backend deployment, native Cloudflare deployment and genuine authenticated public-URL verification remain pending.

## Infrastructure gates and rollback

Read-only Brevo connector returned an internal error; the existing actual Domains browser page still has no configured sending domain. No PostgreSQL connection variables or configured local connection appeared in the task workspace. The secure connection location and existing owned domain/DNS account were requested asynchronously; passwords were not requested. Do not reset credentials, buy services, drop pg_net or treat partial exports as complete backups.

Existing API32 ACTIVE, all 22 source files retained in outputs/defense-sequence-api32-deployed.json, source artifact f9ffa0f3c3e2ac538c71bdafaf895107938afa8b6fa4ef2b00d27d785e84a2b8. Existing Worker main 0469f0280fb5cadc4d516b8d84389f2b93c9fe67 / a135662d rollback retained. Authentication, CSRF, quota, RLS, DB data and financial-kernel files remain unchanged. Added recurring cost zero; no new paid dependency/project.

Primary references: https://docs.morpho.org/developers/api/morpho/ ; https://github.com/morpho-org/morpho-blue/blob/main/src/Morpho.sol ; https://github.com/morpho-org/morpho-blue/blob/main/src/libraries/SharesMathLib.sol . Existing runtime identity hashes remain authoritative; current main documentation alone does not whitelist an upgraded contract.
