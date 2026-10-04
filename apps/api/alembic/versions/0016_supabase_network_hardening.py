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
    # pg_net is a platform-managed extension on hosted Supabase. Its schema ACLs
    # may be restored by the platform, and the Rivexis migration role is not the
    # owner there. Harden only when the executing role owns schema net; hosted
    # Supabase exposure is instead governed by the Data API exposed-schema list.
    op.execute(
        """
        DO $$
        DECLARE
            net_owner oid;
        BEGIN
            SELECT nspowner INTO net_owner FROM pg_namespace WHERE nspname = 'net';
            IF net_owner IS NOT NULL AND net_owner = (SELECT oid FROM pg_roles WHERE rolname = current_user) THEN
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
        DECLARE
            net_owner oid;
        BEGIN
            SELECT nspowner INTO net_owner FROM pg_namespace WHERE nspname = 'net';
            IF net_owner IS NOT NULL AND net_owner = (SELECT oid FROM pg_roles WHERE rolname = current_user) THEN
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
