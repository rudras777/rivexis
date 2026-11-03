# Technical and organizational handover

No ownership transfer is authorized by this document. The founder's personal Wix site, root `rvea.info`, unrelated projects and private email accounts are outside the Rivexis asset boundary.

## Package to review

| Area | Authoritative entry |
|---|---|
| Source / architecture / naming | README, ARCHITECTURE, CONTRIBUTING, engineering standards and naming registry |
| Resources / environment / deployment | INFRASTRUCTURE, DEPLOYMENT, domain production runbook |
| Data / authorization / API | DATABASE, API, SECURITY and dated acceptance evidence |
| Operations / recovery / cost | OPERATIONS and governance report; actual provider entitlements remain dated observations |
| Routine development | Founder development guide and quick reference |
| Dependencies / provenance | Existing lockfiles, license inventory limitations and preserved Git/evidence history |
| Open decisions | Governance findings, status register and current completion checkpoint |

## Provider transition options

- **GitHub:** transferring the repository, granting a maintainer role and assigning IP rights are separate acts. Confirm current repository-transfer requirements, integration behavior and review protections before executing any transfer ([provider procedure](https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository)).
- **Cloudflare:** inventory Worker/Pages/domain/binding/build-token dependencies. Do not assume the existing resources can be renamed or moved in place. A future account move needs a validated parallel migration, staged source/configuration, routing approval and rollback; no move has been tested here.
- **Supabase:** verify current organization/project transfer eligibility and plan restrictions with the provider. Database data, managed Auth, keys, functions, storage, schedules and billing must all be considered. A database SQL dump alone is not the whole platform.
- **Brevo:** establish organization-level operational access and supported ownership/billing transition with Brevo. Do not give a purchaser the founder's Google password or unrelated mailbox. Current transfer mechanics are unverified.
- **Domain:** retain founder ownership with an agreed subdomain delegation, explicitly assign the relevant subdomain under a future agreement, or migrate only Rivexis to an independent domain. Do not transfer the personal apex/portfolio automatically. User sessions, callbacks and email links require acceptance testing after any hostname change.

## Access transition and acceptance

Identify named incoming operators and required roles; obtain explicit access/ownership/data-transfer approval. Confirm contractual, privacy, IP and third-party license requirements through appropriate review. No root project license or legal ownership determination is established by this audit. Public source visibility is not a substitute for that review.

Prepare independent recovery/key custody, account recovery, provider billing contacts, credential dependency map and scheduled rotation. Grant least privilege through supported provider roles; never share personal credentials. Verify new operators can build from the lockfile, run tests, deploy to an isolated environment, diagnose an incident and recover service without undocumented laptop files. Revoke superseded access only after approved acceptance and dependency verification.

Remaining institutional-transfer gates include production migration reconstruction, current provider IAM/transfer eligibility, complete dependency-license review, full-service recovery and operational ownership. This package does not assert acquisition, licensing, customer-data-transfer or compliance readiness.
