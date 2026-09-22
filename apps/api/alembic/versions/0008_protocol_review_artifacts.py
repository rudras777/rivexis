"""Persist protocol configuration reviews as first-class report artifacts."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
revision="0008_protocol_review_artifacts"
down_revision="0007_alert_delivery_lifecycle"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind(); dialect=bind.dialect.name; existing={c['name'] for c in inspect(bind).get_columns('reports')}
    json_type=postgresql.JSONB() if dialect=='postgresql' else sa.JSON()
    with op.batch_alter_table('reports',recreate='always' if dialect=='sqlite' else 'auto') as batch:
        if 'analysis_id' not in existing: batch.add_column(sa.Column('analysis_id',sa.String(36),nullable=True))
        if 'report_type' not in existing: batch.add_column(sa.Column('report_type',sa.String(80),nullable=True))
        if 'storage_ref' not in existing: batch.add_column(sa.Column('storage_ref',sa.Text(),nullable=True))
        if 'payload' not in existing: batch.add_column(sa.Column('payload',json_type,nullable=True))
        if 'approved_by_user_id' not in existing: batch.add_column(sa.Column('approved_by_user_id',sa.String(36),nullable=True))
        if 'approved_at' not in existing: batch.add_column(sa.Column('approved_at',sa.DateTime(timezone=True),nullable=True))
        batch.alter_column('decision_id',existing_type=sa.String(36),nullable=True)
    inspector=inspect(bind); fks=inspector.get_foreign_keys('reports')
    edges={(tuple(x.get('constrained_columns') or []),x.get('referred_table')) for x in fks}
    with op.batch_alter_table('reports',recreate='always' if dialect=='sqlite' else 'auto') as batch:
        if (('analysis_id',),'analyses') not in edges: batch.create_foreign_key('fk_reports_analysis_id__analyses','analyses',['analysis_id'],['id'])
        if (('approved_by_user_id',),'users') not in edges: batch.create_foreign_key('fk_reports_approved_by_user_id__users','users',['approved_by_user_id'],['id'])
    indexes={i['name'] for i in inspect(bind).get_indexes('reports')}
    if 'reports_workspace_type_status_idx' not in indexes:
        op.create_index('reports_workspace_type_status_idx','reports',['workspace_id','report_type','status'])

def downgrade():
    bind=op.get_bind(); dialect=bind.dialect.name
    indexes={i['name'] for i in inspect(bind).get_indexes('reports')}
    if 'reports_workspace_type_status_idx' in indexes: op.drop_index('reports_workspace_type_status_idx',table_name='reports')
    existing={c['name'] for c in inspect(bind).get_columns('reports')}
    with op.batch_alter_table('reports',recreate='always' if dialect=='sqlite' else 'auto') as batch:
        for name in ['approved_at','approved_by_user_id','payload','storage_ref','report_type','analysis_id']:
            if name in existing: batch.drop_column(name)
        batch.alter_column('decision_id',existing_type=sa.String(36),nullable=False)
