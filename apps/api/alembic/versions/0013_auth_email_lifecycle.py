from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0013_auth_email_lifecycle"
down_revision = "0012_postgres_performance_hardening"
branch_labels = None
depends_on = None


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    op.create_table(
        "user_auth_state",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_token_digest", sa.String(length=64), nullable=True),
        sa.Column("verification_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_reset_token_digest", sa.String(length=64), nullable=True),
        sa.Column("password_reset_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("verification_token_digest", name="uq_user_auth_state_verification_digest"),
        sa.UniqueConstraint("password_reset_token_digest", name="uq_user_auth_state_reset_digest"),
    )
    op.create_index("ix_user_auth_state_verification_token_digest", "user_auth_state", ["verification_token_digest"], unique=True)
    op.create_index("ix_user_auth_state_password_reset_token_digest", "user_auth_state", ["password_reset_token_digest"], unique=True)

    # Existing accounts predate email verification. Backfill them as verified so
    # enabling the policy later cannot lock out legitimate existing users.
    if _postgres():
        op.execute(
            "INSERT INTO user_auth_state (user_id, email_verified_at, updated_at) "
            "SELECT id::text, now(), now() FROM users"
        )
        op.execute("ALTER TABLE user_auth_state ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE user_auth_state FORCE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY rivexis_auth_state_service ON user_auth_state "
            "FOR ALL TO rivexis_app USING (true) WITH CHECK (true)"
        )
        op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE user_auth_state TO rivexis_app")
    else:
        op.execute(
            "INSERT INTO user_auth_state (user_id, email_verified_at, updated_at) "
            "SELECT id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM users"
        )


def downgrade() -> None:
    if _postgres():
        op.execute("DROP POLICY IF EXISTS rivexis_auth_state_service ON user_auth_state")
    op.drop_index("ix_user_auth_state_password_reset_token_digest", table_name="user_auth_state")
    op.drop_index("ix_user_auth_state_verification_token_digest", table_name="user_auth_state")
    op.drop_table("user_auth_state")
