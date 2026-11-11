# Public migration source provenance

11 November 2026. **Partially complete.** No production DDL, migration-ledger edit, user-row read, new grant or credential change occurred.

## Verified scope

The existing project still has 48 migration ledger entries. A read-only server-side comparison covered all 29 retained public SQL files: four timestamped migrations and 25 infrastructure recipes. The sensitive historical entry `20260922162311` was excluded. The server returned file names and matching version/name/statement-count metadata, never historical SQL or customer data.

Ten files match twelve applied entries after converting CRLF to LF and trimming outer space, tab, CR and LF only. Comments, internal whitespace, case and quoted values remain significant. Both similarly named duplicate migrations are retained as separate applied versions. All four timestamped files match, including these truthful aliases:

| Source timestamp | Applied version | Name |
|---|---|---|
| 20261009133430 | 20261009135602 | defi_beta_budget |
| 20261009145634 | 20261009150456 | legacy_private_table_rls |

The six matching infrastructure recipes are 006, 007, 009, 012, 014 and 015. Recipes007 and009 each match two ledger entries. Their mappings and normalized SHA256 source digests are in `PRODUCTION_MIGRATION_REGISTER.json` under the separately dated `sourceComparison`; its original 3 November metadata observation is preserved.

Thirty-six applied entries remain unreconciled. The other nineteen public recipes do not fully match under this strict comparison. This is neither proof that they are missing nor proof of a semantic defect: historical patches, formatting, comments and source consolidation require separate review. No confidential historical SQL was exported to resolve those differences.

### Follow-up: ten leading-header differences verified

The separate `leadingCommentComparison` now records ten additional entries from infrastructure recipes016–025. After the original normalization, only leading `--` line comments and outer whitespace are removed, identically on both sides. Block comments, quoted comment markers, trailing/internal comments, SQL statements and function bodies are preserved. A lone internal CR is conservatively retained. Combined content coverage is22 of48, with26 entries still unreconciled. The initial full-text12/48 result is unchanged and remains separately recorded; these additional ten are not mislabeled full-text matches or independently replayed migrations.

The Windows CLI had a reproduced output defect: reading source CRLF bytes correctly and then printing them through normal Windows stdout could turn them into CRCRLF inside string literals. Explicit SQL escapes for CR/LF/tab now preserve data regardless of console newline translation. This affected query generation after the byte-reader correction, not default digest validation or production data. Fresh generated strict/header queries returned12/22 matches respectively. Twenty Python regressions pass, including the Windows transport case and adversarial header/identity/coverage checks. Ten synthetic read-only PostgreSQL cases independently confirm the same normalization boundaries without tables, customer data or writes.

## Reproduce without migration execution

```sh
python scripts/migration_provenance.py
python -m unittest scripts.test_migration_provenance
python scripts/migration_provenance.py --comparison-query
python scripts/migration_provenance.py --comparison-query --ignore-leading-comments
```

The default command verifies the public source set and normalized digests against the dated observation. It does not contact production or refresh that observation. CI fails on changed/missing/extra sources until their provenance is reviewed. The optional command emits a single SELECT query containing the already-public source bodies as quoted string data; it never opens a connection or executes SQL. A separately authorized read-only operator can submit it through the existing database connection. Its result contains matching metadata only and excludes the sensitive version. Twelve local regression tests cover source drift, coverage, timestamp aliases, meaningful whitespace, duplicate/unknown identities, traversal, SQL quoting and sensitive exclusions. The generated query was executed read-only and independently reproduced the original twelve matches.

This is not an ordered executable baseline, migration replay, full-service restore or permission to run reset/push. The 5 November matching-image schema-only restore retains its dated scope. Further confidential review and an approved recovery exercise remain required. Rollback of this source-only guard is a normal reviewed revert; no database rollback is needed.

## Account protection observations

The existing Supabase Security page on 11 November shows an enrolled MFA method and offers a backup method. No secret or recovery code was read; independent recovery-code custody remains unverified. The owner reports Cloudflare MFA enabled, but a subsequent documented GET `/user`, using existing Wrangler authentication, still returns `two_factor_authentication_enabled=false` for the matched owner. The connected Cloudflare browser remains at sign-in. This discrepancy remains open; no password reset, new credential, account enforcement change or MFA enrollment was performed by the agent. [Cloudflare MFA instructions](https://developers.cloudflare.com/fundamentals/user-profiles/2fa/).

The owner subsequently clarified that enrollment was in Google, not Cloudflare-native Authentication. That explains the distinct API result; Google MFA and Cloudflare-native enrollment are recorded separately. Native enrollment remains an owner-only step. Additional 11 November catalog/dashboard inspection found net-schema browser-role grants, but only public/graphql_public are exposed to Data API, with zero public tables/functions granted to those roles. No managed-extension grants were changed based on an assumed API vulnerability.
