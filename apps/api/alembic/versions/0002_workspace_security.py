"""Workspace isolation, organizations, persistent monitoring/reports/alerts, richer audit records."""
from alembic import op
import sqlalchemy as sa

revision="0002_workspace_security"
down_revision="0001_mvp"
branch_labels=None
depends_on=None


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("token_version",sa.Integer(),nullable=False,server_default="0"))
    op.create_table(
        "organizations",
        sa.Column("id",sa.String(36),primary_key=True),
        sa.Column("name",sa.String(160),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
    )
    op.create_table(
        "organization_members",
        sa.Column("organization_id",sa.String(36),sa.ForeignKey("organizations.id",ondelete="CASCADE"),primary_key=True),
        sa.Column("user_id",sa.String(36),sa.ForeignKey("users.id",ondelete="CASCADE"),primary_key=True),
        sa.Column("role",sa.String(24),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
    )
    with op.batch_alter_table("workspaces") as batch:
        batch.add_column(sa.Column("organization_id",sa.String(36),nullable=True))
        batch.create_foreign_key("fk_workspaces_organization","organizations",["organization_id"],["id"])
        batch.create_index("ix_workspaces_organization_id",["organization_id"])
    with op.batch_alter_table("analyses") as batch:
        batch.add_column(sa.Column("owner_user_id",sa.String(36),nullable=True))
        batch.add_column(sa.Column("workspace_id",sa.String(36),nullable=True))
        batch.create_foreign_key("fk_analyses_owner","users",["owner_user_id"],["id"])
        batch.create_foreign_key("fk_analyses_workspace","workspaces",["workspace_id"],["id"])
        batch.create_index("ix_analyses_owner_user_id",["owner_user_id"])
        batch.create_index("ix_analyses_workspace_id",["workspace_id"])
    with op.batch_alter_table("decisions") as batch:
        batch.add_column(sa.Column("owner_user_id",sa.String(36),nullable=True))
        batch.add_column(sa.Column("workspace_id",sa.String(36),nullable=True))
        batch.create_foreign_key("fk_decisions_owner","users",["owner_user_id"],["id"])
        batch.create_foreign_key("fk_decisions_workspace","workspaces",["workspace_id"],["id"])
        batch.create_index("ix_decisions_owner_user_id",["owner_user_id"])
        batch.create_index("ix_decisions_workspace_id",["workspace_id"])
    with op.batch_alter_table("saved_analyses") as batch:
        batch.add_column(sa.Column("workspace_id",sa.String(36),nullable=True))
        batch.create_foreign_key("fk_saved_workspace","workspaces",["workspace_id"],["id"])
        batch.create_index("ix_saved_analyses_workspace_id",["workspace_id"])
        batch.create_unique_constraint("uq_saved_user_analysis",["user_id","analysis_id"])
    with op.batch_alter_table("portfolios") as batch:
        batch.add_column(sa.Column("workspace_id",sa.String(36),nullable=True))
        batch.create_foreign_key("fk_portfolio_workspace","workspaces",["workspace_id"],["id"])
        batch.create_index("ix_portfolios_workspace_id",["workspace_id"])
    with op.batch_alter_table("audit_logs") as batch:
        batch.add_column(sa.Column("actor_user_id",sa.String(36),nullable=True))
        batch.add_column(sa.Column("workspace_id",sa.String(36),nullable=True))
        batch.add_column(sa.Column("request_id",sa.String(128),nullable=True))
        batch.create_foreign_key("fk_audit_actor","users",["actor_user_id"],["id"])
        batch.create_foreign_key("fk_audit_workspace","workspaces",["workspace_id"],["id"])
        batch.create_index("ix_audit_logs_actor_user_id",["actor_user_id"])
        batch.create_index("ix_audit_logs_workspace_id",["workspace_id"])
        batch.create_index("ix_audit_logs_request_id",["request_id"])
    op.create_table(
        "monitors",
        sa.Column("id",sa.String(36),primary_key=True),
        sa.Column("workspace_id",sa.String(36),sa.ForeignKey("workspaces.id",ondelete="CASCADE"),nullable=False),
        sa.Column("created_by_user_id",sa.String(36),sa.ForeignKey("users.id"),nullable=False),
        sa.Column("entity",sa.String(160),nullable=False),
        sa.Column("chain",sa.String(64),nullable=False),
        sa.Column("rules",sa.Text,nullable=False),
        sa.Column("config",sa.Text,nullable=False),
        sa.Column("status",sa.String(48),nullable=False),
        sa.Column("last_snapshot",sa.Text,nullable=True),
        sa.Column("last_analysis_id",sa.String(36),nullable=True),
        sa.Column("last_status",sa.String(48),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
    )
    op.create_index("ix_monitors_workspace_id","monitors",["workspace_id"])
    op.create_index("ix_monitors_created_by_user_id","monitors",["created_by_user_id"])
    op.create_table(
        "alerts",
        sa.Column("id",sa.String(36),primary_key=True),
        sa.Column("workspace_id",sa.String(36),sa.ForeignKey("workspaces.id",ondelete="CASCADE"),nullable=False),
        sa.Column("monitor_id",sa.String(36),sa.ForeignKey("monitors.id",ondelete="CASCADE"),nullable=True),
        sa.Column("analysis_id",sa.String(36),nullable=True),
        sa.Column("severity",sa.String(24),nullable=False),
        sa.Column("status",sa.String(24),nullable=False),
        sa.Column("payload",sa.Text,nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
    )
    op.create_index("ix_alerts_workspace_id","alerts",["workspace_id"])
    op.create_index("ix_alerts_monitor_id","alerts",["monitor_id"])
    op.create_table(
        "reports",
        sa.Column("id",sa.String(36),primary_key=True),
        sa.Column("workspace_id",sa.String(36),sa.ForeignKey("workspaces.id",ondelete="CASCADE"),nullable=False),
        sa.Column("decision_id",sa.String(36),nullable=False),
        sa.Column("format",sa.String(16),nullable=False),
        sa.Column("status",sa.String(24),nullable=False),
        sa.Column("created_by_user_id",sa.String(36),sa.ForeignKey("users.id"),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
    )
    op.create_index("ix_reports_workspace_id","reports",["workspace_id"])
    op.create_index("ix_reports_decision_id","reports",["decision_id"])
    op.create_index("ix_reports_created_by_user_id","reports",["created_by_user_id"])


def downgrade():
    op.drop_table("reports")
    op.drop_table("alerts")
    op.drop_table("monitors")
    with op.batch_alter_table("audit_logs") as batch:
        batch.drop_index("ix_audit_logs_request_id")
        batch.drop_index("ix_audit_logs_workspace_id")
        batch.drop_index("ix_audit_logs_actor_user_id")
        batch.drop_column("request_id")
        batch.drop_column("workspace_id")
        batch.drop_column("actor_user_id")
    with op.batch_alter_table("portfolios") as batch:
        batch.drop_index("ix_portfolios_workspace_id")
        batch.drop_column("workspace_id")
    with op.batch_alter_table("saved_analyses") as batch:
        batch.drop_constraint("uq_saved_user_analysis",type_="unique")
        batch.drop_index("ix_saved_analyses_workspace_id")
        batch.drop_column("workspace_id")
    with op.batch_alter_table("decisions") as batch:
        batch.drop_index("ix_decisions_workspace_id")
        batch.drop_index("ix_decisions_owner_user_id")
        batch.drop_column("workspace_id")
        batch.drop_column("owner_user_id")
    with op.batch_alter_table("analyses") as batch:
        batch.drop_index("ix_analyses_workspace_id")
        batch.drop_index("ix_analyses_owner_user_id")
        batch.drop_column("workspace_id")
        batch.drop_column("owner_user_id")
    with op.batch_alter_table("workspaces") as batch:
        batch.drop_index("ix_workspaces_organization_id")
        batch.drop_column("organization_id")
    op.drop_table("organization_members")
    op.drop_table("organizations")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("token_version")
