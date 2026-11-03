# Engineering standards

These requirements apply to human and automated development. They are independent of any editor or AI service.

1. Inspect the existing implementation and authoritative resource registry before changing it. Reuse working modules; introduce packages/services only for a demonstrated need.
2. Keep presentation in `apps/web/components` and `apps/web/app`; coordinate workflows in existing providers/hooks; keep financial mathematics and protocol evidence in the existing `supabase/functions/rivexis-api/defi-*` modules. The browser imports the same deterministic models rather than maintaining a second formula.
3. Monetary quantities use fixed-point integers and explicit decimals. Preserve protocol rounding, independent liquidation domains, oracle freshness, block identity, source validation, fee assumptions and unsupported states. A modeled target is never a safety or execution guarantee.
4. RIVEXIS never holds private keys, signs, approves allowances or submits transactions. Read-only simulations remain explicitly separate from execution.
5. Enforce authorization on the server. Service credentials remain server-side. Public keys do not replace RLS. Account/tenant ownership is checked for every private operation.
6. Validate input before quotas/provider calls where possible. An unavailable quota acknowledgment is not an exhausted quota. Never invent results, reflect provider credentials/errors or retry a write with an unknown outcome.
7. Use `main` with short `feature/…` and `fix/…` branches. Require the existing six strict checks and normal protected merge. Do not bypass protections or create `develop` without a real integration need.
8. Use descriptive camelCase variables, PascalCase components, snake_case SQL and UPPER_SNAKE_CASE environment variables. Preserve historical migration versions and deployed resource identifiers. Naming exceptions belong in [the registry](../governance/NAMING_REGISTRY.md).
9. Separate development, isolated acceptance and production. Local preview must block external API forwarding. Do not copy production users, sessions or recovery secrets into fixtures.
10. Preserve the lockfile and security overrides. Document graph/optional-platform limitations instead of downgrading patched packages to make an inventory tool pass.
11. Reproduce confirmed defects, add meaningful regressions and run appropriate model, security, integration and browser checks. Tests must distinguish fixtures from genuine provider observations. Record skips, failures and unavailable capabilities honestly.
12. Update the relevant authoritative document with behavior, configuration, ownership and limitations. Preserve dated audit/recovery evidence; an index should identify current guidance rather than duplicate every historical note.
13. Changes to schema, deployment, security boundaries or significant state ownership need a rationale, dependency impact and rollback/forward-repair plan. Use existing `docs/adr` for significant architectural decisions.
14. Never print or commit credential values. Stage named files; run the tracked-source secret scanner. Do not scan or upload arbitrary local output/recovery directories.
15. Production DNS, destructive operations, ownership transfer, credential rotation, incompatible APIs and spending require the specific approval described in the task. Public repository visibility is not evidence of an IP license or permission to transfer customer data.

Status vocabulary: **Verified**, **Implemented, not yet verified**, **Partially complete**, **Blocked**, **Not applicable**. Evidence must state scope and date. No self-issued compliance or institutional-security certification.
