"""Persist provider runtime telemetry and workspace association."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision="0005_provider_runtime_telemetry"
down_revision="0004_blueprint_contract"
branch_labels=None
depends_on=None

COLUMNS=[
    ("workspace_id",sa.String(36)),
    ("provider_key",sa.String(120)),
    ("operation",sa.String(120)),
    ("attempts",sa.Integer()),
    ("retries",sa.Integer()),
    ("cache_hit",sa.Boolean()),
]

def upgrade():
    bind=op.get_bind(); inspector=inspect(bind)
    existing={c["name"] for c in inspector.get_columns("provider_requests")}
    for name,typ in COLUMNS:
        if name not in existing: op.add_column("provider_requests",sa.Column(name,typ,nullable=True))
    inspector=inspect(bind)
    fk_edges={(tuple(x.get("constrained_columns") or []),x.get("referred_table")) for x in inspector.get_foreign_keys("provider_requests")}
    with op.batch_alter_table("provider_requests",recreate="always" if bind.dialect.name=="sqlite" else "auto") as batch:
        if (("workspace_id",),"workspaces") not in fk_edges:
            batch.create_foreign_key("fk_provider_requests_workspace","workspaces",["workspace_id"],["id"],ondelete="CASCADE")
    inspector=inspect(bind)
    names={i["name"] for i in inspector.get_indexes("provider_requests")}
    if "ix_provider_requests_workspace_id" not in names: op.create_index("ix_provider_requests_workspace_id","provider_requests",["workspace_id"])
    if "ix_provider_requests_provider_key" not in names: op.create_index("ix_provider_requests_provider_key","provider_requests",["provider_key"])
    if "ix_provider_requests_created_at" not in names: op.create_index("ix_provider_requests_created_at","provider_requests",["created_at"])
    if "provider_requests_workspace_time_idx" not in names: op.create_index("provider_requests_workspace_time_idx","provider_requests",["workspace_id","created_at"])
    if bind.dialect.name=="postgresql":
        policy="(workspace_id IN (SELECT id FROM workspaces))"
        op.execute(sa.text('ALTER TABLE "provider_requests" ENABLE ROW LEVEL SECURITY'))
        op.execute(sa.text('ALTER TABLE "provider_requests" FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text('DROP POLICY IF EXISTS rivexis_tenant_isolation ON "provider_requests"'))
        op.execute(sa.text(f'CREATE POLICY rivexis_tenant_isolation ON "provider_requests" USING {policy} WITH CHECK {policy}'))

def downgrade():
    pass
