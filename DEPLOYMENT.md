# Deployment and rollback

Production application: `https://rivexis.rvea.info`; recovery/compatibility origin: `https://rivexis-web.rudrasingh0718.workers.dev`. Both reach the existing `rivexis-web` Worker. The Wix root/WWW portfolio is separate.

## Normal frontend release

Use current `main`, a reviewed short branch and the existing protected pull request. All six required checks must pass. The normal production release path is the enabled Cloudflare Workers Build on protected `main`; the main-only `deploy-web` GitHub workflow is a verified fallback. Observe the provider upload and verify the full `rivexis-build` SHA on both application hostnames. Never equate a green test job or a merge with a live deployment, and avoid dispatching parallel release paths.

`npm run build` creates the Worker locally. The controlled `build:vinext` wrapper also generates the anonymous static landing document and its manifest. A subsequent raw `vinext build` removes that artifact; the manual deployment command now calls the controlled wrapper instead. Keep root, application and generated Wrangler files in their documented roles; do not delete them as duplicate services.

The existing `deploy-web` GitHub workflow is the main-only manual recovery/release path. Inspect the intended SHA and successful checks first. PR126 was released through run `41691268003`, Worker version `02442078-81d5-45f5-a4c7-5f3d5f936c42`; non-main probe run `41677165366` skipped the deployment job with zero steps. Cloudflare subsequently built the same PR126 source automatically as `2e2e1a45-b8f0-4316-aaeb-3c815c0bd147`; this was the active version during the 74 live checks. The [console audit](docs/governance/CLOUDFLARE_CONSOLE_AUDIT_20261104.md) verifies the existing `main` build trigger. Use that normal path and retain this manual workflow as a fallback. Documentation changes need no additional manual dispatch, but the current automatic watch path `*` still triggers builds:

```sh
gh pr checks <pull-request-number>
gh workflow run deploy-web.yml --ref main
gh run list --workflow deploy-web.yml --limit 3
```

These commands affect production when the manual deployment runs. The root `npm run deploy` entrypoint is reserved for Cloudflare Workers Builds and requires its exact supplied commit identity. Do not manually deploy the archived Cloudflare API container/placeholder or create a replacement Worker.

## API and database

Supabase Edge deployment is a separate release operation. Preserve the actual current source bundle, file list, import map, JWT setting and function version first. Deploy only the reviewed function after relevant checks, then read back every intended file and test authenticated behavior. A false `verify_jwt` flag does not waive the application-level session and ownership checks. Never silently deploy local tests or change provider settings alongside a source change.

Database changes follow [the migration procedure](DATABASE.md); there is no verified all-service one-command production deploy. Credentials stay in existing provider stores. Use supported authenticated tools or provider dashboard workflows; do not paste tokens into shell history or documentation.

## Release checklist

- Correct source branch/SHA, scope and dependencies; named-file diff and secret checks.
- Relevant model/API/security/browser tests, build and Worker dry-run.
- Disposable validation for schema or infrastructure changes; appropriate recovery point.
- Normal protected merge; actual provider deployment/version and file readback.
- Both public hosts, expected SHA, private guest denial, authenticated critical paths and fresh financial evidence where affected.
- Record known limits, errors, provider status, cost impact and rollback identity.

## Incident rollback checklist

1. Stop further deployment/retries; distinguish frontend, Edge, origin/Auth, database and provider failure.
2. Select the last accepted compatible version of the affected layer only. Current accepted PR126 frontend is `2e2e1a45-b8f0-4316-aaeb-3c815c0bd147` / API40; its earlier manual version was `02442078-81d5-45f5-a4c7-5f3d5f936c42`; preceding accepted frontend is `fe82ed68-bc6f-4357-ab6f-d72e6c802285` / API40 (PR125). Discovery baseline was `d4fd53ce-a317-400b-9fb1-b47b1b4a8df6` / API39. Recheck the latest accepted release before rollback.
3. Use the existing provider's version rollback or securely captured reviewed Edge sources/settings. Do not restore customer data for an application routing error.
4. Preserve Wix nameservers, root/WWW routing, gateway binding, custom hostname and existing users. DNS or credential changes require separate impact review/approval.
5. Verify the exact restored identity, authentication and affected workflows; record unresolved outcomes. Never retry a possibly committed write without checking its record.

Detailed domain/gateway procedure: [production runbook](docs/RVEA_PRODUCTION_RUNBOOK.md). Recovery and incidents: [operations](OPERATIONS.md).
