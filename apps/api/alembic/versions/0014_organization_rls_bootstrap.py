from __future__ import annotations

from alembic import op

revision = "0014_organization_rls_bootstrap"
down_revision = "0013_auth_email_lifecycle"
branch_labels = None
depends_on = None


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _postgres():
        return
    op.execute("DROP POLICY IF EXISTS rivexis_tenant_isolation ON public.organizations")
    op.execute("DROP POLICY IF EXISTS rivexis_organizations_select ON public.organizations")
    op.execute("DROP POLICY IF EXISTS rivexis_organizations_update ON public.organizations")
    op.execute("DROP POLICY IF EXISTS rivexis_organizations_delete ON public.organizations")
    op.execute("DROP POLICY IF EXISTS rivexis_organization_bootstrap_insert ON public.organizations")
    op.execute(
        """
        CREATE POLICY rivexis_organizations_select ON public.organizations
        FOR SELECT
        USING (
            id IN (
                SELECT organization_id FROM public.organization_members
                WHERE user_id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY rivexis_organizations_update ON public.organizations
        FOR UPDATE
        USING (
            id IN (
                SELECT organization_id FROM public.organization_members
                WHERE user_id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
            )
        )
        WITH CHECK (
            id IN (
                SELECT organization_id FROM public.organization_members
                WHERE user_id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY rivexis_organizations_delete ON public.organizations
        FOR DELETE
        USING (
            id IN (
                SELECT organization_id FROM public.organization_members
                WHERE user_id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
            )
        )
        """
    )
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


def downgrade() -> None:
    if not _postgres():
        return
    op.execute("DROP POLICY IF EXISTS rivexis_organizations_select ON public.organizations")
    op.execute("DROP POLICY IF EXISTS rivexis_organizations_update ON public.organizations")
    op.execute("DROP POLICY IF EXISTS rivexis_organizations_delete ON public.organizations")
    op.execute("DROP POLICY IF EXISTS rivexis_organization_bootstrap_insert ON public.organizations")
    op.execute(
        """
        CREATE POLICY rivexis_tenant_isolation ON public.organizations
        USING (
            id IN (
                SELECT organization_id FROM public.organization_members
                WHERE user_id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
            )
        )
        WITH CHECK (
            id IN (
                SELECT organization_id FROM public.organization_members
                WHERE user_id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY rivexis_organization_bootstrap_insert ON public.organizations
        FOR INSERT
        WITH CHECK (
            id = nullif(current_setting('rivexis.organization_id', true), '')
            AND nullif(current_setting('rivexis.organization_role', true), '') = 'OWNER'
            AND EXISTS (
                SELECT 1 FROM public.users
                WHERE id = nullif(current_setting('rivexis.user_id', true), '')
            )
        )
        """
    )
