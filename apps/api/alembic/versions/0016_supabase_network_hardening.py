from __future__ import annotations

from alembic import op

revision = "0016_supabase_network_hardening"
down_revision = "0015_authenticated_org_bootstrap"
branch_labels = None
depends_on = None


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _postgres():
        return
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'net') THEN
                REVOKE USAGE ON SCHEMA net FROM PUBLIC;
                REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA net FROM PUBLIC;

                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                    REVOKE USAGE ON SCHEMA net FROM anon;
                    REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA net FROM anon;
                END IF;
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                    REVOKE USAGE ON SCHEMA net FROM authenticated;
                    REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA net FROM authenticated;
                END IF;
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
                    GRANT USAGE ON SCHEMA net TO service_role;
                    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA net TO service_role;
                END IF;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    if not _postgres():
        return
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'net') THEN
                GRANT USAGE ON SCHEMA net TO PUBLIC;
                GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA net TO PUBLIC;

                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                    GRANT USAGE ON SCHEMA net TO anon;
                    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA net TO anon;
                END IF;
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                    GRANT USAGE ON SCHEMA net TO authenticated;
                    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA net TO authenticated;
                END IF;
            END IF;
        END
        $$
        """
    )
