# RIVEXIS â€” Engineering Governance & Platform Readiness Report

Checkpoint: 3 November 2026, Asia/Calcutta. **Consolidation is partially complete.** This is an engineering evidence/status record, not a compliance certificate or an acquisition-ready declaration. PR125 is released at `1d309aebda7a67dd0b15e4a61d338412188d8af9`, Worker `fe82ed68-bc6f-4357-ab6f-d72e6c802285`, API version 40. The preceding discovery baseline was PR124 / `a5b8753`, Worker `d4fd53ce-a317-400b-9fb1-b47b1b4a8df6`, API 39. A subsequent dependency-security candidate remains separate until its own gates and deployment pass.

## 1. Executive summary

The bounded product is functioning on the existing infrastructure, with genuine authenticated financial acceptance recorded separately. The principal governance weaknesses are incomplete production migration reconstruction, stale current-entry documentation, competing/unsafe deployment shortcuts, incomplete independent environment isolation, dependency inventory limitations and founder-specific operational ownership.

Current work preserves the design, mathematical models, identities, customer records and personal Wix infrastructure. It adds canonical engineering guidance and makes narrow reproducible safety corrections. No production resource rename, database reset, ownership transfer, credential rotation or paid service is included.

## 2. Infrastructure inventory

[INFRASTRUCTURE.md](../../INFRASTRUCTURE.md) is the current inventory/dependency map. Authenticated discovery confirmed the public `rudras777/rivexis` repository and sole listed admin collaborator, one visible Rivexis Supabase project/Free organization, the existing Worker and one Pages gateway. The fifth Edge deployment is a retired fixed 410 recovery stub, not an active recovery service. The GitHub Pages site is a redirect, not a duplicate financial backend.

Cloudflare account-wide dashboard-only inventory remains pending sign-in; CLI account/deployment/Pages metadata is verified. Brevo browser access is verified after owner-confirmed Google sign-in despite connector errors. Current sender is verified freemail, no domain is configured, two transactional templates are active, and the dashboard shows the existing 300/day allowance. Delivery logs show confirmation/recovery Delivered events from 29 October; no new message was sent in this audit.

Develoop is specifically identified as the installed skills-only development bundle 0.1.3, publisher Changkyun Kim, repository `comfuture/agent-skills`. It supplies optional issue/PR/review/refactoring guidance. No Rivexis runtime import or deployment ownership was found; the project remains maintainable without it. Its own license does not assign a license to Rivexis.

## 3. Changes completed / under validation

| Change | Status at this checkpoint | Evidence |
|---|---|---|
| Native GitHub secret scanning and push protection | Verified | Repository API readback: enabled; no paid Advanced Security purchase |
| Private vulnerability reporting | Verified | Existing repository endpoint readback enabled |
| Malformed on-chain quota handling | Verified | Seven red regressions before fix; 14/14 focused tests pass; API40's 25 files exactly match the intended bundle; real authenticated contract inspection at block 26335554 |
| Tracked-source secret scanner | Verified locally | Four regressions: untracked recovery exclusion, safe findings, supported key formats, optimized-Python failure gate; CI hook added |
| Safe local web preview | Verified on Windows | Landing/login200; account GET/login POST503 from local block; loopback-only process stopped after test |
| Static landing retained in manual build | Verified | Raw rebuild reproduced artifact loss; corrected build retained matching static manifest; Worker dry-run and actual release passed; public artifact exposes the intended commit in Chrome |
| Main-only manual deployment; no duplicate feature push CI | Verified | Six required checks preserved; actual non-main run skipped the job with zero steps; main deployment passed |
| Retired relay source under version control | Verified source preservation | Exact observed 410 stub committed and Deno-checked; historical deployed function unchanged |
| Canonical docs, founder handbook and standards | Implemented, not yet verified as a full handover | Root entrypoints plus requested durable guide/standards paths |

## 4. Naming standardization

[Naming registry](NAMING_REGISTRY.md) records the conventions and justified compatibility exceptions. `rivexis-web`, the current gateway, immutable project IDs, historical branches/migrations and model/API versions are preserved. No aesthetic resource rename was attempted. There are161 observed remote branches and three pre-existing open PRs; merged/obsolete status requires content review, especially after squash merges. Nothing was deleted or closed based on a name.

## 5. Architecture assessment

[ARCHITECTURE.md](../../ARCHITECTURE.md) maps the existing modular monorepo to presentation, coordination, shared domain models, integrations and infrastructure. Wholesale directory movement/new services are not justified by the observed deployment. Retained Python/Alembic/Cloudflare API configurations are explicitly separated from the current Supabase-backed product. Full dead-code/style review and any behavior-preserving domain refactor remain scoped follow-up work, not assumed complete.

## 6. Security assessment

Fresh catalog evidence: 61 public tables, zero without RLS, zero client-callable public security definers, client roles cannot log in directly. Existing strict six-check branch protection/admin enforcement and no force push/deletion were preserved. Native repository secret protection and private reporting were enabled/read back. Current local scanner does not traverse untracked laptop/recovery artifacts and cannot be disabled by Python optimization.

Inherited Supabase warnings remain: nonrelocatable `pg_net` registration and Free-plan leaked-password protection. The [security policy](../../SECURITY.md) gives reporting and limitations. No active credential exposure is inferred from a historical sensitive-statement pattern. No credential value, user row, recovery key or migration SQL containing potential credentials is published.

## 7. Deployment verification

PR125 passed all six required checks, plus 343 isolated fixture tests each in Chromium, Firefox and WebKit, with zero skipped, unexpected or flaky outcomes. Firefox used one documented driver-navigation release attempt; this is recorded separately from test retries. Local checks also passed: 320 financial/adapter tests, 42 API tests, four secret-scanner regressions, web build/types/lint/AST checks, API types, Deno checks for all five functions, static manifest and Worker dry-run. Required CI independently passed the retained Python/API audit and real PostgreSQL migration/fixture-restore gates; these do not constitute full Supabase production reconstruction.

Actual main deployment run [41677909822](https://github.com/rudras777/rivexis/actions/runs/41677909822) published Worker `fe82ed68-bc6f-4357-ab6f-d72e6c802285`. Chrome read the exact merged SHA on the custom domain and original-origin public artifact; 37 live custom-domain browser checks passed without submitting real credentials. The plain Python HTTP probe was denied with Cloudflare error 1010 and is retained as a failed verification method, not a product outage or a pass. No protection was disabled. API40 readback matched all 25 intended files, changing only `onchain-http.mjs`; real Aave pool inspection returned code/proxy evidence at block 26335554 without saving an identity or signing. Non-main probe [41677165366](https://github.com/rudras777/rivexis/actions/runs/41677165366) skipped the deployment job with zero steps. See [DEPLOYMENT.md](../../DEPLOYMENT.md).

## 8. Database and authentication

[DATABASE.md](../../DATABASE.md) records actual ownership, role/RLS boundaries and migration divergence. The production ledger has 48 entries versus four tracked Supabase migrations plus Alembic history. Two local timestamp identities differ from their production entries; preserve both. A metadata/digest register excludes the digest of the one sensitive-statement candidate. This is not executable baseline SQL. No live migration history or data was changed.

Current authenticated owner/session, preference save/reload, report persistence and read-only financial workflows were verified in [the acceptance record](../AUTHENTICATED_ACCEPTANCE_20261103.md). Brevo/Supabase verification and recovery evidence remains dated 29 October; a fresh full email/token round trip was not repeated here. Settings Dark was restored after testing; one private public-reference validation report was retained.

## 9. Product engines

| Engine | Implemented contract / dependencies | Observed validation / limits |
|---|---|---|
| LiquidationGuard | Pinned Ethereum Aave normal-mode/four validated assets and bounded Morpho market; protocol math/oracles/RPC | Genuine four-asset acceptance and fixed-point regressions; eMode/isolation/other markets unsupported |
| GasGuard | Supported read-only call/estimate, fee reserve, nonce, balance/allowance and modeled positions | Actual succeeded-at-block withdrawal and correctly blocked approval-dependent repayment; no signing/execution, MEV/slippage guarantees or advisory execution labels |
| Defense Planner | Bounded repayment/collateral alternatives, budget/fee/wallet constraints and explicit shocks | Ten real-position stress inputs and ten budget cases; retained unmet-target evidence; no global optimality or safety promise |
| Shared data | Genuine block/oracle observations, provenance, bounded retries/history and failure states | Live observation growth plus provider/reorg/freshness fixture tests; no provider uptime SLA or fabricated fallback |

[API.md](../../API.md) identifies input/output/validation sources; existing adjacent model/adapter tests, methodology and scenario matrix remain authoritative for numerical details. Financial source is not rewritten for architectural appearance.

## 10. Developer handover

[Founder development guide](../development/FOUNDER_DEVELOPMENT_GUIDE.md) and [quick reference](../development/QUICK_REFERENCE.md) show ordinary setup, source locations, local isolation, tests, controlled deployment and troubleshooting. [Engineering standards](../architecture/ENGINEERING_STANDARDS.md) and root AGENTS provide a tool-independent maintenance contract. Fresh macOS execution and a complete independent Supabase local integration environment remain unverified.

## 11. Organizational transfer readiness

[HANDOVER.md](../../HANDOVER.md) separates source, IP, user data, domains, provider IAM and billing transitions. Personal apex/Wix, email accounts and unrelated products are excluded. Provider-specific transfer eligibility, a named incoming operator, independent key custody, legal/license clearance and full-service recovery require further verification/approval. No transfer occurred.

## 12. Outstanding work / risk order

| Priority | Finding / impact | Required remediation and acceptance |
|---|---|---|
| High | Production database not fully reproducible from repository | Supported confidential schema capture, role/managed-service reconciliation, sanitized baseline and disposable full restore; never reset production to fit source |
| Resolved | Latent manual build could lose CPU-saving public artifact | Correct wrapper, matching manifest, dry-run, protected release and actual public artifact verified; no prior outage inferred |
| Resolved | Manual workflow previously accepted arbitrary branches | Main-only condition, actual non-main zero-step skipped run and successful main release verified |
| Medium | Dependency-security follow-up | Initial npm audit had three moderate entries from one Satori SVG-escaping advisory. A compatible stable Vinext/renderer upgrade and patched compression dependency are under validation; production findings are not declared resolved until its release passes |
| Medium | Native npm SBOM generation fails on intentional security overrides and missing optional-platform graph edges | Preserve patched pins; publish honest lock metadata inventory; independently validate a standard SBOM/license review before transfer |
| Medium | Python dependencies are ranged, and full cross-platform backend bootstrap is unverified | Reproducible reviewed constraints/environment validation without silently changing current production |
| Medium | Full account IAM, subscriptions, settings and current complete recovery remain unverified | Finish authenticated provider inventory, separate access transition and fresh full-service recovery drill |
| Medium | Freemail sender/no authenticated sending domain | Preserve owner-approved beta sender; separate approved domain/sender/DNS decision and real deliverability acceptance |
| Medium | Existing Supabase warnings / independent assurance | Keep bounded beta limitations explicit; no unsafe extension relocation, paid upgrade or self-issued certification |
| Low | Historical branch/document sprawl and retained deployment shortcuts | Content/reference review, archive index and approved cleanup; preserve audit history and unmerged work |

## 13. Readiness scorecard

Scores measure equal-weight **evidence coverage**, not software quality, safety, compliance or marketing readiness. Each row lists four criteria in order; Verified earns25, Partially complete12.5, Blocked/unverified0. Round half-points up. These provisional scores must be revised after current-release validation.

| Dimension | Four criteria and current status | Score /100 |
|---|---|---|
| Architecture | System map V; shared models V; layer ownership V; full isolated bootstrap B |75|
| Code Maintainability | Source map V; focused defect regressions V; complete unused-code review P; all dependency reproducibility P |75|
| Security | Auth/RLS evidence V; repository protections V; all known risks closed B; independent assurance B |50|
| Infrastructure Governance | Critical identities V; deployment traceability V; full account inventory P; independent IAM/billing verification B |63|
| Testing | Deterministic financial coverage V; genuine core acceptance V; PR125 release checks V; all-service recovery B |75|
| Documentation | Canonical index V; founder guide/local workflow V; incident/handover procedures P; provider-transfer detail P |75|
| Operational Reliability | Actual deployed baseline V; fail-closed provider tests V; full recovery/RPO B; sustained operations B |50|
| Founder Maintainability | Windows safe preview V; source/task map V; fresh macOS B; full local backend B |50|
| Organizational Transfer Readiness | Asset boundary V; access procedure P; legal/license clearance B; independent operator recovery B |38|

V=Verified, P=Partially complete, B=Blocked. Other implemented-but-unverified work earns zero until evidenced. Underlying evidence/status, rather than a rounded number, governs release decisions.

## 14. Change register

Baseline: PR123 oracle fix/API39 and PR124 authenticated evidence. [PR125](https://github.com/rudras777/rivexis/pull/125) merged to `1d309aebda7a67dd0b15e4a61d338412188d8af9`; required CI run `41674510705`, browser compatibility run `41674510621`, main deployment and skip-only probe are linked above. API40 bundle SHA-256: `d4c768cd2260380b4c5f355a1f4a117614baad6b826a206f92cbb017a17d0238`. The API39 source remains captured outside Git for rollback. A follow-up dependency-security branch is not yet a production claim. Local logs are preserved under task outputs `governance-*`; confidential recovery material is excluded. Safe changes and remaining phases are recorded in [the completion checkpoint](../../RIVEXIS_PRODUCTION_COMPLETION_TRACKER.md).
