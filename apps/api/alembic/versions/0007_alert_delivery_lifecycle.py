"""Add durable alert delivery lifecycle and SLO fields."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision="0007_alert_delivery_lifecycle"
down_revision="0006_alert_provider_event_idempotency"
branch_labels=None
depends_on=None

COLUMNS=(
    ("occurrence_count",sa.Integer(),False,"1"),
    ("first_seen_at",sa.DateTime(timezone=True),False,"CURRENT_TIMESTAMP"),
    ("last_seen_at",sa.DateTime(timezone=True),False,"CURRENT_TIMESTAMP"),
    ("delivery_status",sa.String(24),False,"'pending'"),
    ("delivery_attempts",sa.Integer(),False,"0"),
    ("next_delivery_at",sa.DateTime(timezone=True),True,None),
    ("last_delivery_error",sa.Text(),True,None),
    ("delivered_at",sa.DateTime(timezone=True),True,None),
    ("dead_lettered_at",sa.DateTime(timezone=True),True,None),
)

def upgrade():
    bind=op.get_bind(); existing={c["name"] for c in inspect(bind).get_columns("alerts")}
    with op.batch_alter_table("alerts", recreate="always" if bind.dialect.name=="sqlite" else "auto") as batch:
        for name,typ,nullable,default in COLUMNS:
            if name not in existing:
                batch.add_column(sa.Column(name,typ,nullable=nullable,server_default=sa.text(default) if default else None))
    indexes={i["name"] for i in inspect(bind).get_indexes("alerts")}
    if "alerts_delivery_due_idx" not in indexes:
        op.create_index("alerts_delivery_due_idx","alerts",["workspace_id","delivery_status","next_delivery_at"])

def downgrade():
    bind=op.get_bind(); indexes={i["name"] for i in inspect(bind).get_indexes("alerts")}
    if "alerts_delivery_due_idx" in indexes: op.drop_index("alerts_delivery_due_idx",table_name="alerts")
    current={c["name"] for c in inspect(bind).get_columns("alerts")}
    with op.batch_alter_table("alerts", recreate="always" if bind.dialect.name=="sqlite" else "auto") as batch:
        for name,_,_,_ in reversed(COLUMNS):
            if name in current: batch.drop_column(name)
