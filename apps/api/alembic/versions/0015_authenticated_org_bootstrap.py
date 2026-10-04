from __future__ import annotations

from alembic import op

revision = "0015_authenticated_org_bootstrap"
down_revision = "0014_organization_rls_bootstrap"
branch_labels = None
depends_on = None


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _postgres():
        return
    op.execute("DROP POLICY IF EXISTS rivexis_organization_bootstrap_insert ON public.organizations")
    op.execute(
        """
        CREATE POLICY rivexis_organization_bootstrap_insert ON public.organizations
        FOR INSERT
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM public.users
                WHERE users.id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
            )
            AND (
                (
                    NULLIF((SELECT current_setting('rivexis.organization_id', true)), '') IS NULL
                    AND NULLIF((SELECT current_setting('rivexis.organization_role', true)), '') IS NULL
                )
                OR (
                    id::text = NULLIF((SELECT current_setting('rivexis.organization_id', true)), '')
                    AND NULLIF((SELECT current_setting('rivexis.organization_role', true)), '') = 'OWNER'
                )
            )
        )
        """
    )


def downgrade() -> None:
    if not _postgres():
        return
    op.execute("DROP POLICY IF EXISTS rivexis_organization_bootstrap_insert ON public.organizations")
    op.execute(
        """
        CREATE POLICY rivexis_organization_bootstrap_insert ON public.organizations
        FOR INSERT
        WITH CHECK (
            id::text = NULLIF((SELECT current_setting('rivexis.organization_id', true)), '')
            AND NULLIF((SELECT current_setting('rivexis.organization_role', true)), '') = 'OWNER'
            AND EXISTS (
                SELECT 1 FROM public.users
                WHERE users.id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
            )
        )
        """
    )
