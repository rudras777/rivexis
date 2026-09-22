# Database Schema

`infrastructure/db/schema.sql` is the 53-table PostgreSQL production blueprint.

Alembic migrations `0001` and `0002` implement the operational persistence used by the application. `0003_production_schema_rls` expands the clean-upgrade table surface and PostgreSQL RLS policy coverage. `0004_blueprint_contract` promotes the remaining scaffold tables/fields and relationship constraints to the current blueprint contract.

The executable schema contract currently verifies a clean migration against all **53 tables**, **511 blueprint columns**, **102 foreign-key edges**, **20 unique constraints** and **11 named indexes** represented by the blueprint/checking surface, followed by a clean downgrade. This is the current source-of-truth statement; the earlier pre-`0004` scaffold warning no longer applies.

The local parity gate is intentionally not a substitute for managed PostgreSQL certification. PostgreSQL type semantics, FORCE-RLS behavior, role attributes, provider-specific backup/restore behavior, and operational performance still require their dedicated staging gates.

For PostgreSQL, tenant RLS policies are enabled/forced where a workspace/user relationship is available. The SQLAlchemy session injects `rivexis.user_id` and `rivexis.workspace_id` into transaction-local settings. Validate those policies against real PostgreSQL using the exact production-style `NOSUPERUSER NOBYPASSRLS` API role plus the separately isolated alert-worker role. The worker may use BYPASSRLS only when its effective DML is restricted to SELECT+UPDATE on `alerts`.
