"""Rivexis MVP persistence subset."""
from alembic import op
import sqlalchemy as sa
revision="0001_mvp";down_revision=None;branch_labels=None;depends_on=None

def upgrade():
    op.create_table("users",sa.Column("id",sa.String(36),primary_key=True),sa.Column("email",sa.String(320),nullable=False,unique=True),sa.Column("password_hash",sa.String(512),nullable=False),sa.Column("role",sa.String(32),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_users_email","users",["email"],unique=True)
    op.create_table("workspaces",sa.Column("id",sa.String(36),primary_key=True),sa.Column("owner_user_id",sa.String(36),sa.ForeignKey("users.id"),nullable=False),sa.Column("name",sa.String(120),nullable=False),sa.Column("role",sa.String(32),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False));op.create_index("ix_workspaces_owner_user_id","workspaces",["owner_user_id"])
    op.create_table("analyses",sa.Column("id",sa.String(36),primary_key=True),sa.Column("engine_id",sa.String(4),nullable=False),sa.Column("payload",sa.Text,nullable=False),sa.Column("demo",sa.Boolean,nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False));op.create_index("ix_analyses_engine_id","analyses",["engine_id"])
    op.create_table("decisions",sa.Column("id",sa.String(36),primary_key=True),sa.Column("payload",sa.Text,nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_table("saved_analyses",sa.Column("id",sa.String(36),primary_key=True),sa.Column("user_id",sa.String(36),sa.ForeignKey("users.id"),nullable=False),sa.Column("analysis_id",sa.String(36),nullable=False),sa.Column("title",sa.String(160),nullable=False),sa.Column("archived",sa.Boolean,nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False));op.create_index("ix_saved_analyses_user_id","saved_analyses",["user_id"]);op.create_index("ix_saved_analyses_analysis_id","saved_analyses",["analysis_id"])
    op.create_table("portfolios",sa.Column("id",sa.String(36),primary_key=True),sa.Column("owner_user_id",sa.String(36),sa.ForeignKey("users.id"),nullable=False),sa.Column("name",sa.String(120),nullable=False),sa.Column("payload",sa.Text,nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False));op.create_index("ix_portfolios_owner_user_id","portfolios",["owner_user_id"])
    op.create_table("audit_logs",sa.Column("id",sa.String(36),primary_key=True),sa.Column("actor",sa.String(320)),sa.Column("action",sa.String(120),nullable=False),sa.Column("resource_type",sa.String(80),nullable=False),sa.Column("resource_id",sa.String(120)),sa.Column("detail",sa.Text,nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
def downgrade():
    for table in ["audit_logs","portfolios","saved_analyses","decisions","analyses","workspaces","users"]:op.drop_table(table)
