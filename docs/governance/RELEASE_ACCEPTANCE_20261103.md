# Governance release acceptance — 3 November 2026

The existing application is released at **`e4a23c1e528ff053ba10f443d9ffe34f7461fc64`**, [PR126](https://github.com/rudras777/rivexis/pull/126). The reviewed head `967576af926ccf820c8584d73599604643c0a518` and merged commit have identical source tree `bedb10facec6879a331fd5fe309a7628e631281c`.

## Actual release and checks

| Evidence | Verified result |
|---|---|
| Protected source checks | All six required checks passed; [CI](https://github.com/rudras777/rivexis/actions/runs/41689064869), [Worker validation](https://github.com/rudras777/rivexis/actions/runs/41689064711) |
| Browser fixtures | 349 cases each in Chromium, Firefox and WebKit; zero skipped, unexpected or flaky results. Firefox recorded zero driver-navigation release attempts. [Compatibility run](https://github.com/rudras777/rivexis/actions/runs/41689064647) |
| Compiled Worker | 98 controlled cases passed, retries disabled, zero skips/failures/flakes; external API forwarding verified blocked; owned server stopped |
| Production deployment | Existing `rivexis-web`, version `02442078-81d5-45f5-a4c7-5f3d5f936c42`; [main-only deployment](https://github.com/rudras777/rivexis/actions/runs/41691268003) succeeded |
| Canonical public application | `https://rivexis.rvea.info`: 37 actual guest browser checks passed against the exact intended SHA |
| Original production URL | `https://rivexis-web.rudrasingh0718.workers.dev`: 37 actual guest browser checks passed against the same SHA |
| Authenticated acceptance | Existing owner session restored on the updated frontend; genuine Aave pool inspection returned block 26336010, 2400 code bytes and the expected EIP-1967 implementation. Source/ABI remained explicitly unverified. No identity save, signature or transaction submission |
| Existing API | Version 40, 25 files, accepted bundle SHA-256 `d4c768cd2260380b4c5f355a1f4a117614baad6b826a206f92cbb017a17d0238`; unchanged during this frontend release |
| Dependency checks | Actual locked installation and full npm audit returned zero known findings; Python CI audit passed. These are scoped registry results, not all-service security certification |

[Sanitized structured evidence](../evidence/governance-release-20261103.json) records counts, timestamps, source and deployment identities. Exact named `governance-*` logs and screenshots remain in task outputs; protected recovery material is excluded from source and public artifacts.

The dependency/security scope and the six account-form regressions are in [the follow-up](DEPENDENCY_SECURITY_20261103.md). Prior genuine position/stress/planner/GasGuard/Settings/report/wallet acceptance remains [dated separately](../AUTHENTICATED_ACCEPTANCE_20261103.md); it is not relabeled as a fresh full email or native-wallet lifecycle test. Financial models were preserved; the same 320 financial/adapter and 42 API tests passed in the release pipeline.

## Readiness and remaining gates

The supported bounded beta release is verified. **Engineering consolidation and institutional/organizational-transfer readiness remain partially complete.** Production schema/migration reconstruction, fresh founder-independent full-service recovery, complete dashboard/IAM/billing inventory, sender-domain/inbox assurance, full native wallet permission lifecycle and independent operating/security assurance remain outstanding. Native npm SBOM generation and license/IP transfer clearance are not certified. Direct Node ESM image rendering is not a supported product route.

No user or saved record was deleted, no database schema or credential was changed, and no DNS/ownership/paid-plan change or new recurring service was introduced. Normal authenticated inspection may advance operational quota/telemetry counters. Prior compatible frontend version `fe82ed68-bc6f-4357-ab6f-d72e6c802285` and API40 remain the immediately preceding accepted compatibility combination.

This acceptance update changes documentation only. It does not require a second application deployment; production code remains the accepted PR126 release. The [phase checkpoint](CONSOLIDATION_CHECKPOINT.md), [readiness report](ENGINEERING_GOVERNANCE_REPORT.md), [deployment runbook](../../DEPLOYMENT.md) and [founder guide](../development/FOUNDER_DEVELOPMENT_GUIDE.md) provide the next safe actions and ordinary maintenance workflow.

The separately dated [4 November Supabase console audit](SUPABASE_CONSOLE_AUDIT_20261104.md) extends account/configuration coverage without changing this product acceptance date.
