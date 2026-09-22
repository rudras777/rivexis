"""Expand Alembic table coverage to the 53-table production blueprint and prepare PostgreSQL RLS.

The operational ORM remains intentionally narrower than the full analytical schema. This
migration materializes every blueprint table name so later provider/engine migrations can
add specialized columns incrementally without maintaining a parallel hand-created database.
PostgreSQL deployments also receive FORCE RLS policies on tenant-scoped resources.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0003_production_schema_rls"
down_revision = "0002_workspace_security"
branch_labels = None
depends_on = None

BLUEPRINT_TABLES = [
    "users","profiles","organizations","organization_members","workspaces","chains","assets","tokens","protocols","contracts",
    "wallets","wallet_groups","data_sources","provider_connections","provider_health_checks","provider_requests","analyses","engine_runs",
    "engine_results","decisions","decision_reasons","findings","evidence","source_conflicts","transactions","transaction_traces","transfers",
    "simulations","security_assessments","security_signals","monitors","threat_events","alerts","entities","entity_labels","fund_flows","routes",
    "route_steps","prices","oracle_feeds","oracle_observations","portfolios","portfolio_positions","protocol_metrics","protocol_assessments",
    "defi_positions","yield_strategies","treasury_scenarios","saved_analyses","reports","user_risk_policies","notification_preferences","audit_logs",
]

# Tables already created by 0001/0002 and retained by the operational ORM.
OPERATIONAL_TABLES = {
    "users","organizations","organization_members","workspaces","analyses","decisions","saved_analyses","portfolios","monitors","alerts","reports","audit_logs",
}

WORKSPACE_DIRECT = {
    "wallets","wallet_groups","provider_connections","analyses","decisions","monitors","alerts","portfolios","defi_positions","yield_strategies",
    "treasury_scenarios","saved_analyses","reports","user_risk_policies","notification_preferences","audit_logs",
}

RELATION_COLUMNS = {
    "profiles": ["user_id"],
    "tokens": ["asset_id","chain_id"],
    "contracts": ["chain_id","protocol_id"],
    "wallets": ["workspace_id","chain_id"],
    "wallet_groups": ["workspace_id"],
    "provider_connections": ["workspace_id","provider_id"],
    "provider_health_checks": ["provider_id"],
    "provider_requests": ["provider_id","analysis_id"],
    "engine_runs": ["analysis_id"],
    "engine_results": ["engine_run_id"],
    "decision_reasons": ["decision_id"],
    "findings": ["analysis_id","engine_run_id"],
    "evidence": ["analysis_id","engine_run_id","provider_id"],
    "source_conflicts": ["analysis_id"],
    "transactions": ["chain_id"],
    "transaction_traces": ["transaction_id"],
    "transfers": ["transaction_id","chain_id","asset_id","provider_id"],
    "simulations": ["analysis_id","transaction_id","provider_id"],
    "security_assessments": ["analysis_id"],
    "security_signals": ["assessment_id","provider_id"],
    "threat_events": ["monitor_id","provider_id"],
    "entity_labels": ["entity_id","chain_id","provider_id"],
    "fund_flows": ["analysis_id","provider_id"],
    "routes": ["analysis_id","provider_id"],
    "route_steps": ["route_id"],
    "prices": ["asset_id","provider_id"],
    "oracle_feeds": ["chain_id","protocol_id","asset_id","provider_id"],
    "oracle_observations": ["oracle_feed_id"],
    "portfolio_positions": ["portfolio_id","asset_id","chain_id","protocol_id"],
    "protocol_metrics": ["protocol_id","chain_id","provider_id"],
    "protocol_assessments": ["analysis_id","protocol_id"],
    "defi_positions": ["workspace_id","protocol_id"],
    "yield_strategies": ["workspace_id","protocol_id","asset_id"],
    "treasury_scenarios": ["workspace_id"],
    "user_risk_policies": ["workspace_id"],
    "notification_preferences": ["workspace_id"],
}


def _minimal_columns(table: str):
    columns = [sa.Column("id", sa.String(36), primary_key=True)]
    for name in RELATION_COLUMNS.get(table, []):
        columns.append(sa.Column(name, sa.String(36), nullable=True, index=False))
    if table in WORKSPACE_DIRECT and "workspace_id" not in RELATION_COLUMNS.get(table, []):
        columns.append(sa.Column("workspace_id", sa.String(36), nullable=True))
    # Preserve useful generic fields for phased expansion without JSON-only persistence.
    columns.extend([
        sa.Column("status", sa.String(48), nullable=True),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    ])
    return columns


def _rls_policy_sql(table: str) -> str | None:
    actor = "NULLIF(current_setting('rivexis.user_id', true), '')"
    if table == "workspaces":
        # Personal workspaces are owner-based. Organization workspaces are membership-based
        # only, so creator lineage cannot bypass a later org downgrade/removal.
        return f"((organization_id IS NULL AND owner_user_id::text = {actor}) OR (organization_id IS NOT NULL AND organization_id IN (SELECT organization_id FROM organization_members WHERE user_id::text = {actor})))"
    if table == "organization_members":
        org_ctx = "NULLIF(current_setting('rivexis.organization_id', true), '')"
        role_ctx = "NULLIF(current_setting('rivexis.organization_role', true), '')"
        # Do not self-query organization_members from its own RLS policy: PostgreSQL
        # can reject that as infinite recursion. The elevated organization context is
        # populated only after the application verifies the actor's own membership.
        return f"(user_id::text = {actor} OR (organization_id::text = {org_ctx} AND {role_ctx} IN ('OWNER','ADMIN')))"
    if table == "organizations":
        return f"(id IN (SELECT organization_id FROM organization_members WHERE user_id::text = {actor}))"
    if table == "profiles":
        return f"(user_id::text = {actor})"
    if table in WORKSPACE_DIRECT:
        return f"(workspace_id IN (SELECT id FROM workspaces))"
    if table in {"engine_runs","findings","evidence","source_conflicts","simulations","security_assessments","fund_flows","routes","protocol_assessments"}:
        return "(analysis_id IN (SELECT id FROM analyses))"
    if table == "engine_results":
        return "(engine_run_id IN (SELECT id FROM engine_runs))"
    if table == "decision_reasons":
        return "(decision_id IN (SELECT id FROM decisions))"
    if table == "security_signals":
        return "(assessment_id IN (SELECT id FROM security_assessments))"
    if table == "threat_events":
        return "(monitor_id IN (SELECT id FROM monitors))"
    if table == "portfolio_positions":
        return "(portfolio_id IN (SELECT id FROM portfolios))"
    return None


def upgrade():
    bind = op.get_bind()
    existing = set(inspect(bind).get_table_names())
    for table in BLUEPRINT_TABLES:
        if table not in existing:
            op.create_table(table, *_minimal_columns(table))

    if bind.dialect.name == "postgresql":
        # RLS is defense in depth. Deploy with a non-superuser application role; PostgreSQL
        # superusers can bypass RLS regardless of FORCE ROW LEVEL SECURITY.
        for table in BLUEPRINT_TABLES:
            policy = _rls_policy_sql(table)
            if not policy:
                continue
            op.execute(sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
            op.execute(sa.text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'))
            op.execute(sa.text(f'DROP POLICY IF EXISTS rivexis_tenant_isolation ON "{table}"'))
            op.execute(sa.text(f'CREATE POLICY rivexis_tenant_isolation ON "{table}" USING {policy} WITH CHECK {policy}'))


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table in reversed(BLUEPRINT_TABLES):
            if _rls_policy_sql(table):
                op.execute(sa.text(f'DROP POLICY IF EXISTS rivexis_tenant_isolation ON "{table}"'))
                op.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
    for table in reversed(BLUEPRINT_TABLES):
        if table not in OPERATIONAL_TABLES:
            op.drop_table(table)
