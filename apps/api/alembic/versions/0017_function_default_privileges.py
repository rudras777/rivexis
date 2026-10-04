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
    # PostgreSQL's built-in function default grants EXECUTE to PUBLIC globally.
    # A schema-scoped REVOKE cannot subtract that global default, so this must be
    # a global default-privilege change for the migration role.
    op.execute("ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC")


def downgrade() -> None:
    if not _postgres():
        return
    op.execute("ALTER DEFAULT PRIVILEGES GRANT EXECUTE ON FUNCTIONS TO PUBLIC")
