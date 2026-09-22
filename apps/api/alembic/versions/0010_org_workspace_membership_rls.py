"""Make organization-workspace access membership-based instead of creator-based."""
from alembic import op
import sqlalchemy as sa

revision = "0010_org_workspace_membership_rls"
down_revision = "0009_trace_correlation"
branch_labels = None
depends_on = None


def _actor() -> str:
    return "NULLIF(current_setting('rivexis.user_id', true), '')"


def _membership_policy() -> str:
    actor = _actor()
    return (
        f"((organization_id IS NULL AND owner_user_id::text = {actor}) "
        f"OR (organization_id IS NOT NULL AND organization_id IN "
        f"(SELECT organization_id FROM organization_members WHERE user_id::text = {actor})))"
    )


def _legacy_policy() -> str:
    actor = _actor()
    return (
        f"(owner_user_id::text = {actor} OR organization_id IN "
        f"(SELECT organization_id FROM organization_members WHERE user_id::text = {actor}))"
    )


def _replace(policy: str) -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(sa.text('ALTER TABLE "workspaces" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text('ALTER TABLE "workspaces" FORCE ROW LEVEL SECURITY'))
    op.execute(sa.text('DROP POLICY IF EXISTS rivexis_tenant_isolation ON "workspaces"'))
    op.execute(sa.text(f'CREATE POLICY rivexis_tenant_isolation ON "workspaces" USING {policy} WITH CHECK {policy}'))


def upgrade():
    _replace(_membership_policy())
    # Older non-certified/staging builds could persist raw provider URLs containing
    # path/query credentials. Endpoint is auxiliary telemetry, so scrub historical
    # values on upgrade rather than retain a potential secret.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "provider_requests" in set(inspector.get_table_names()):
        op.execute(sa.text("UPDATE provider_requests SET endpoint = NULL WHERE endpoint IS NOT NULL"))


def downgrade():
    _replace(_legacy_policy())
