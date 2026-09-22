"""Add PostgreSQL-backed distributed runtime budgets and provider circuits."""

from alembic import op
import sqlalchemy as sa

revision = "0011_postgres_runtime_controls"
down_revision = "0010_org_workspace_membership_rls"
branch_labels = None
depends_on = None


def _secure_runtime_tables() -> None:
    for table in ("runtime_rate_events", "runtime_provider_circuits"):
        op.execute(sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text(
            """
DO $$
DECLARE
  api_role text;
BEGIN
  FOREACH api_role IN ARRAY ARRAY['anon', 'authenticated', 'service_role'] LOOP
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = api_role) THEN
      EXECUTE format('REVOKE ALL ON runtime_rate_events FROM %I', api_role);
      EXECUTE format('REVOKE ALL ON runtime_provider_circuits FROM %I', api_role);
    END IF;
  END LOOP;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rivexis_app') THEN
    GRANT SELECT, INSERT, DELETE ON runtime_rate_events TO rivexis_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON runtime_provider_circuits TO rivexis_app;
    CREATE POLICY rivexis_runtime_control ON runtime_rate_events
      FOR ALL TO rivexis_app USING (true) WITH CHECK (true);
    CREATE POLICY rivexis_runtime_control ON runtime_provider_circuits
      FOR ALL TO rivexis_app USING (true) WITH CHECK (true);
  END IF;
END $$
"""
        )
    )


def upgrade():
    op.create_table(
        "runtime_rate_events",
        sa.Column("event_id", sa.String(32), primary_key=True),
        sa.Column("bucket", sa.String(512), nullable=False),
        sa.Column("occurred_at", sa.Float(), nullable=False),
    )
    op.create_index(
        "ix_runtime_rate_events_bucket_occurred_at",
        "runtime_rate_events",
        ["bucket", "occurred_at"],
    )
    op.create_table(
        "runtime_provider_circuits",
        sa.Column("scope", sa.String(128), primary_key=True),
        sa.Column("provider_id", sa.String(128), primary_key=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("opened_until", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.Float(), nullable=False),
    )
    if op.get_bind().dialect.name == "postgresql":
        # These internal tables live in Supabase's exposed public schema for Alembic
        # portability, but only the dedicated backend role can access them.
        _secure_runtime_tables()


def downgrade():
    op.drop_table("runtime_provider_circuits")
    op.drop_index("ix_runtime_rate_events_bucket_occurred_at", table_name="runtime_rate_events")
    op.drop_table("runtime_rate_events")
