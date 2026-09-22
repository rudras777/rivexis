"""Add persistent provider-event idempotency to alerts."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision="0006_alert_provider_event_idempotency"
down_revision="0005_provider_runtime_telemetry"
branch_labels=None
depends_on=None


def upgrade():
    bind=op.get_bind(); inspector=inspect(bind)
    existing={c["name"] for c in inspector.get_columns("alerts")}
    with op.batch_alter_table("alerts", recreate="always" if bind.dialect.name=="sqlite" else "auto") as batch:
        if "provider_id" not in existing:
            batch.add_column(sa.Column("provider_id",sa.String(64),nullable=True))
        if "external_event_key" not in existing:
            batch.add_column(sa.Column("external_event_key",sa.String(256),nullable=True))
    inspector=inspect(bind)
    indexes={i["name"] for i in inspector.get_indexes("alerts")}
    if "ix_alerts_provider_id" not in indexes:
        op.create_index("ix_alerts_provider_id","alerts",["provider_id"])
    if "ix_alerts_external_event_key" not in indexes:
        op.create_index("ix_alerts_external_event_key","alerts",["external_event_key"])
    uniques={tuple(u.get("column_names") or []) for u in inspector.get_unique_constraints("alerts")}
    if ("workspace_id","provider_id","external_event_key") not in uniques:
        with op.batch_alter_table("alerts", recreate="always" if bind.dialect.name=="sqlite" else "auto") as batch:
            batch.create_unique_constraint("uq_alerts_provider_event",["workspace_id","provider_id","external_event_key"])


def downgrade():
    bind=op.get_bind(); inspector=inspect(bind)
    indexes={i["name"] for i in inspector.get_indexes("alerts")}
    for name in ("ix_alerts_external_event_key","ix_alerts_provider_id"):
        if name in indexes:
            op.drop_index(name,table_name="alerts")
    uniques={u.get("name") for u in inspector.get_unique_constraints("alerts")}
    with op.batch_alter_table("alerts", recreate="always" if bind.dialect.name=="sqlite" else "auto") as batch:
        if "uq_alerts_provider_event" in uniques:
            batch.drop_constraint("uq_alerts_provider_event",type_="unique")
        current={c["name"] for c in inspect(bind).get_columns("alerts")}
        for name in ("external_event_key","provider_id"):
            if name in current:
                batch.drop_column(name)
