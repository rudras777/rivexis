# Launch assurance follow-up — 25 October 2026

The existing website remains on the verified security release PR115/08780c416f9632703494cfc0b926c2029219d818, existing Worker460118f6 at100%, native build36fb13f2-52f9-4fe1-bef5-ee92948f809e Ready. Its eight workflows,339 fixture cases per browser,108 actual-public checks,295 financial/auth and25 proxy security cases pass. This follow-up changes repository deployment safeguards and operating evidence, not application, financial, authentication, database, dependencies, design or Worker configuration.

## Deployment safeguard found and closed

Fresh GitHub REST inspection found main unprotected (404), no repository rulesets and no effective branch rules. Direct source pushes could therefore reach the existing auto-deploy integration outside the tested PR procedure. Existing public repository/admin access was confirmed; no new credential or permission recipient was created.

Applied a reversible main branch protection rule using the current official GitHub API. Independent readback confirms:

- Pull requests must be up to date and pass api, web, invariants, postgres-migrations, validate-worker-bundle and validate-cloudflare-default-root.
- Each required check is pinned to the observed GitHub Actions app15368; another app cannot supply a same-named success.
- Administrators follow the same requirements. Force pushes and branch deletion are disabled; unresolved review conversations must be resolved.
- Merge commits remain supported; the branch is not locked. No new reviewer, account credential, collaborator, paid plan or domain is required. Required approving reviews remains0 for the current sole-owner workflow; this is not independent review certification.

These six check names run for every PR in the existing workflows. Conditional Firefox/WebKit workflows remain part of application release acceptance but are not made unconditional branch requirements: documentation-only PRs do not trigger their path filter. The rule does not certify manual Cloudflare dashboard operations or every privileged account activity. The repository owner retains administration and can edit/remove the rule if an operational recovery requires it; removing safeguards is not the default deployment procedure.

The first API request contained both deprecated contexts and the replacement checks fields. GitHub rejected it422 without applying a rule. Removing the redundant deprecated field succeeded; required checks/severity/assertions were not weakened. Original rejection and successful independent readback are preserved in task evidence.

## Wallet acceptance boundary

Existing Chrome and its ordinary RIVEXIS account session are connected through the supported tools. The deployed08780c4 build was reloaded, verified in the DOM and the real installed MetaMask provider was discovered through the explicit connection dialog. The explicit public-address request succeeded using the existing site grant; UI confirmed MetaMask/Ethereum mainnet Chain1. Connected context survived navigation to Contracts. A real reload cleared the volatile connection and required explicit provider selection again. No fresh native permission dialog was exposed or accepted. Additional observable reconnect/local-forget/cancellation checks are recorded in the release PR/checkpoint. No wallet import, signing, token approval or transaction is involved. An unexposed wallet prompt or provider timeout does not count as permission acceptance. Existing saved analysis addresses must be preserved and a late result must not create a connection after local cancellation/timeout.

## Operating decision

Supported controlled beta remains the accepted scope. Two Supabase WARNs remain nonrelocatable pg_net namespace and paid leaked-password protection; no destructive extension change or plan upgrade. Current verified sender is the owner's explicit beta choice. Owned-domain/inbox assurance, full native wallet consent/events, independent key/second-machine/full-service recovery, sustained field/load/provider assurance and independent security/operating review remain separate evidence requirements.

Keep the20October encrypted recovery snapshot, approved23October owner-only copy and separate local key protected. This work does not access, copy or re-test recovery material. No third-party testing service, new permanent project, paid load test or paid AI is introduced. Added recurring service costUSD0; total account billing is not certified.

## Resumption and validation

Record exact protection readback and PR required-check status. Merge this documentation only through the newly enforced normal PR procedure after the six required checks pass; no admin bypass or force-push. Final docs commit, any existing Cloudflare Git deployment and actual same-URL build/health/access checks belong to the release PR and task checkpoint. Passing repeated application fixtures does not close the independent assurance gates above. Application/backend/dependency tree identity is required before reusing PR115 runtime acceptance.
