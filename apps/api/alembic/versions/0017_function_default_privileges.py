from __future__ import annotations

from alembic import op

revision = "0017_function_default_privileges"
down_revision = "0016_supabase_network_hardening"
branch_labels = None
depends_on = None


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _postgres():
        return
    # PostgreSQL grants EXECUTE on newly created functions to PUBLIC unless the
    # creator has an explicit default ACL. Rivexis functions are always exposed
    # deliberately, so make future migrations fail closed by default.
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC"
    )


def downgrade() -> None:
    if not _postgres():
        return
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT EXECUTE ON FUNCTIONS TO PUBLIC"
    )
