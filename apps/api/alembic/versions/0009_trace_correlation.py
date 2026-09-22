"""Add W3C trace correlation to provider requests and audit logs."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0009_trace_correlation"
down_revision = "0008_protocol_review_artifacts"
branch_labels = None
depends_on = None


def _add(table: str, name: str, length: int):
    bind = op.get_bind(); dialect = bind.dialect.name
    existing = {c["name"] for c in inspect(bind).get_columns(table)}
    if name in existing:
        return
    with op.batch_alter_table(table, recreate="always" if dialect == "sqlite" else "auto") as batch:
        batch.add_column(sa.Column(name, sa.String(length), nullable=True))


def upgrade():
    for table in ("provider_requests", "audit_logs"):
        _add(table, "trace_id", 32)
        _add(table, "span_id", 16)
    bind = op.get_bind(); dialect = bind.dialect.name
    for table, name in (("provider_requests", "provider_requests_trace_idx"), ("audit_logs", "audit_logs_trace_idx")):
        indexes = {i["name"] for i in inspect(bind).get_indexes(table)}
        if name not in indexes:
            op.create_index(name, table, ["workspace_id", "trace_id", "created_at"])


def downgrade():
    bind = op.get_bind(); dialect = bind.dialect.name
    for table, name in (("provider_requests", "provider_requests_trace_idx"), ("audit_logs", "audit_logs_trace_idx")):
        indexes = {i["name"] for i in inspect(bind).get_indexes(table)}
        if name in indexes:
            op.drop_index(name, table_name=table)
        existing = {c["name"] for c in inspect(bind).get_columns(table)}
        with op.batch_alter_table(table, recreate="always" if dialect == "sqlite" else "auto") as batch:
            for column in ("span_id", "trace_id"):
                if column in existing:
                    batch.drop_column(column)
