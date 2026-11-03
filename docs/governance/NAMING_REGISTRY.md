# Authoritative naming registry

| Category | Standard / current authoritative value | Rule |
|---|---|---|
| Product | Rivexis; visual brand RIVEXIS | No product version suffix |
| Meaning | Risk, Value, Execution, Analysis | Preserve existing identity |
| Repository | `rudras777/rivexis` | Verified public repo; no replacement |
| Branch | `main`; `feature/<description>`; `fix/<description>` | No permanent develop branch without need; historical branches are not renamed |
| Environments | development, staging, production | Describe actual isolation; do not call production-connected previews staging |
| Worker | `rivexis-web` | Explicit compatibility exception to proposed `rivexis-app`; renaming would affect URL, bindings and integrations |
| Ingress | `rvea-rivexis-gateway` | Existing Pages gateway, not a duplicate application |
| API | Existing Supabase `rivexis-api` | Do not deploy the dormant Cloudflare placeholder merely because it has the same name |
| Domain | `rivexis.rvea.info` | Root/WWW Wix portfolio remains separate |
| Supabase project | `ivszvufdonfgwjpfgwii` / Rivexis | Immutable provider ref; retain |
| SQL / TS / components / env | snake_case / camelCase / PascalCase / UPPER_SNAKE_CASE | Follow existing module boundaries |
| History | Existing migration IDs, evidence dates, release tags and provider version counters | Preserve truth; never cosmetically rewrite immutable history |

No production resource rename is approved or needed for this consolidation. Before proposing one, enumerate references, actual provider support, routing/session impact, rollback and tests. Legacy API paths and model/version identifiers are compatibility controls, not brand suffixes.
