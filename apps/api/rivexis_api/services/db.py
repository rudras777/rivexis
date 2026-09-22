from __future__ import annotations
from datetime import datetime, timezone
import os
from uuid import uuid4
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from rivexis_api.core.config import settings
from rivexis_api.core.context import get_actor_user_id, get_workspace_id, get_organization_id, get_organization_role
from rivexis_api.services.postgres_identity import inspect_postgres_role_security_state, validate_standalone_service_role

connect_args={"check_same_thread":False} if settings.database_url.startswith("sqlite") else {}
engine=create_engine(settings.database_url, future=True, connect_args=connect_args)
class RivexisSession(Session):
    pass

SessionLocal=sessionmaker(bind=engine, class_=RivexisSession, expire_on_commit=False)

@event.listens_for(RivexisSession, "after_begin")
def _set_postgres_security_context(session, transaction, connection):
    """Propagate request identity into PostgreSQL transaction-local settings.

    The RLS migration consumes these settings. SQLite test/dev runs intentionally
    skip them. PostgreSQL deployments should use a non-superuser application role
    so FORCE ROW LEVEL SECURITY cannot be bypassed.
    """
    if connection.dialect.name != "postgresql":
        return
    actor = get_actor_user_id() or ""
    workspace = get_workspace_id() or ""
    organization = get_organization_id() or ""
    organization_role = get_organization_role() or ""
    connection.exec_driver_sql("SELECT set_config('rivexis.user_id', %s, true)", (actor,))
    connection.exec_driver_sql("SELECT set_config('rivexis.workspace_id', %s, true)", (workspace,))
    connection.exec_driver_sql("SELECT set_config('rivexis.organization_id', %s, true)", (organization,))
    connection.exec_driver_sql("SELECT set_config('rivexis.organization_role', %s, true)", (organization_role,))




def validate_application_database_role() -> dict[str, object]:
    """Fail closed unless PostgreSQL API runtime credentials are standalone and non-privileged."""
    if engine.dialect.name != "postgresql":
        return {"dialect": engine.dialect.name, "validated": True, "mode": "non_postgres"}
    with engine.connect() as conn:
        state = inspect_postgres_role_security_state(conn)
        validate_standalone_service_role(state, label="application runtime", require_bypassrls=False)
        return {
            "dialect": "postgresql",
            "validated": True,
            "role": state["current_user"],
            "bypassrls": False,
            "parent_role_memberships": 0,
        }


def validate_alert_worker_database_role() -> dict[str, object]:
    """Fail closed unless a PostgreSQL alert worker has narrowly scoped cross-tenant authority.

    SQLite developer/test runs do not need a privileged worker identity. PostgreSQL workers
    must use a dedicated standalone non-superuser BYPASSRLS role because the delivery loop
    enumerates due alerts across all workspaces. The role is accepted only when its effective
    DML is SELECT/UPDATE on ``alerts`` and nothing else in the current schema.
    """
    if engine.dialect.name != "postgresql":
        return {"dialect": engine.dialect.name, "validated": True, "mode": "non_postgres"}
    with engine.connect() as conn:
        state = inspect_postgres_role_security_state(conn)
        validate_standalone_service_role(state, label="alert worker", require_bypassrls=True)
        rows = conn.execute(text("""
            SELECT table_name,
                   has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), 'SELECT') AS can_select,
                   has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), 'INSERT') AS can_insert,
                   has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), 'UPDATE') AS can_update,
                   has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), 'DELETE') AS can_delete
            FROM information_schema.tables
            WHERE table_schema=current_schema() AND table_type='BASE TABLE'
            ORDER BY table_name
        """)).mappings().all()
        seen_alerts = False
        for row in rows:
            table = str(row["table_name"])
            dml = {
                "SELECT": bool(row["can_select"]),
                "INSERT": bool(row["can_insert"]),
                "UPDATE": bool(row["can_update"]),
                "DELETE": bool(row["can_delete"]),
            }
            if table == "alerts":
                seen_alerts = True
                if dml != {"SELECT": True, "INSERT": False, "UPDATE": True, "DELETE": False}:
                    raise RuntimeError(f"Rivexis alert worker requires exactly SELECT+UPDATE on alerts, observed {dml}")
            elif any(dml.values()):
                raise RuntimeError(f"Rivexis alert worker role is over-privileged on table {table!r}: {dml}")
        if not seen_alerts:
            raise RuntimeError("Rivexis alert worker cannot find the migrated alerts table")
        return {
            "dialect": "postgresql",
            "validated": True,
            "role": state["current_user"],
            "bypassrls": True,
            "parent_role_memberships": 0,
            "tables": len(rows),
        }

class Base(DeclarativeBase): pass

def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc)

class UserRow(Base):
    __tablename__="users"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str]=mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str]=mapped_column(String(512))
    role: Mapped[str]=mapped_column(String(32), default="Individual")
    token_version: Mapped[int]=mapped_column(Integer, default=0)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class OrganizationRow(Base):
    __tablename__="organizations"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str]=mapped_column(String(160))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class OrganizationMemberRow(Base):
    __tablename__="organization_members"
    organization_id: Mapped[str]=mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str]=mapped_column(String(24), default="VIEWER")
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class WorkspaceRow(Base):
    __tablename__="workspaces"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    owner_user_id: Mapped[str]=mapped_column(ForeignKey("users.id"), index=True)
    organization_id: Mapped[str | None]=mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    name: Mapped[str]=mapped_column(String(120))
    role: Mapped[str]=mapped_column(String(32), default="Individual")
    token_version: Mapped[int]=mapped_column(Integer, default=0)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)


class DataSourceRow(Base):
    __tablename__="data_sources"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    provider_id: Mapped[str]=mapped_column(String(120), unique=True, index=True)
    provider_name: Mapped[str]=mapped_column(String(160))
    category: Mapped[str]=mapped_column(String(80), default="runtime")
    enabled: Mapped[bool]=mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class ProviderRequestRow(Base):
    __tablename__="provider_requests"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str | None]=mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    provider_id: Mapped[str | None]=mapped_column(ForeignKey("data_sources.id"), nullable=True, index=True)
    provider_key: Mapped[str]=mapped_column(String(120), index=True)
    operation: Mapped[str]=mapped_column(String(120))
    endpoint: Mapped[str | None]=mapped_column(Text, nullable=True)
    status: Mapped[str]=mapped_column(String(48))
    latency_ms: Mapped[float | None]=mapped_column(Float, nullable=True)
    estimated_cost: Mapped[float | None]=mapped_column(Float, nullable=True)
    attempts: Mapped[int]=mapped_column(Integer, default=0)
    retries: Mapped[int]=mapped_column(Integer, default=0)
    cache_hit: Mapped[bool]=mapped_column(Boolean, default=False)
    error_class: Mapped[str | None]=mapped_column(String(120), nullable=True)
    request_id_external: Mapped[str | None]=mapped_column(String(128), nullable=True)
    trace_id: Mapped[str | None]=mapped_column(String(32), nullable=True, index=True)
    span_id: Mapped[str | None]=mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, index=True)

class AnalysisRow(Base):
    __tablename__="analyses"
    id: Mapped[str]=mapped_column(String(36), primary_key=True)
    engine_id: Mapped[str]=mapped_column(String(4), index=True)
    owner_user_id: Mapped[str | None]=mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    workspace_id: Mapped[str | None]=mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    payload: Mapped[str]=mapped_column(Text)
    demo: Mapped[bool]=mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class DecisionRow(Base):
    __tablename__="decisions"
    id: Mapped[str]=mapped_column(String(36), primary_key=True)
    owner_user_id: Mapped[str | None]=mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    workspace_id: Mapped[str | None]=mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    payload: Mapped[str]=mapped_column(Text)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class SavedAnalysisRow(Base):
    __tablename__="saved_analyses"
    __table_args__=(UniqueConstraint("user_id","analysis_id",name="uq_saved_user_analysis"),)
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id"), index=True)
    workspace_id: Mapped[str | None]=mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    analysis_id: Mapped[str]=mapped_column(String(36), index=True)
    title: Mapped[str]=mapped_column(String(160))
    archived: Mapped[bool]=mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class PortfolioRow(Base):
    __tablename__="portfolios"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    owner_user_id: Mapped[str]=mapped_column(ForeignKey("users.id"), index=True)
    workspace_id: Mapped[str | None]=mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    name: Mapped[str]=mapped_column(String(120))
    payload: Mapped[str]=mapped_column(Text, default="{}")
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class MonitorRow(Base):
    __tablename__="monitors"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str]=mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    created_by_user_id: Mapped[str]=mapped_column(ForeignKey("users.id"), index=True)
    entity: Mapped[str]=mapped_column(String(160))
    chain: Mapped[str]=mapped_column(String(64), default="ethereum")
    rules: Mapped[str]=mapped_column(Text, default="[]")
    config: Mapped[str]=mapped_column(Text, default="{}")
    status: Mapped[str]=mapped_column(String(48), default="configured_manual_polling")
    last_snapshot: Mapped[str | None]=mapped_column(Text, nullable=True)
    last_analysis_id: Mapped[str | None]=mapped_column(String(36), nullable=True)
    last_status: Mapped[str | None]=mapped_column(String(48), nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class AlertRow(Base):
    __tablename__="alerts"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str]=mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    monitor_id: Mapped[str | None]=mapped_column(ForeignKey("monitors.id", ondelete="CASCADE"), nullable=True, index=True)
    analysis_id: Mapped[str | None]=mapped_column(String(36), nullable=True)
    severity: Mapped[str]=mapped_column(String(24), default="unknown")
    status: Mapped[str]=mapped_column(String(24), default="open")
    provider_id: Mapped[str | None]=mapped_column(String(64), nullable=True, index=True)
    external_event_key: Mapped[str | None]=mapped_column(String(256), nullable=True, index=True)
    occurrence_count: Mapped[int]=mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    last_seen_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    delivery_status: Mapped[str]=mapped_column(String(24), default="pending", index=True)
    delivery_attempts: Mapped[int]=mapped_column(Integer, default=0)
    next_delivery_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_delivery_error: Mapped[str | None]=mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True), nullable=True)
    dead_lettered_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[str]=mapped_column(Text, default="{}")
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class ReportRow(Base):
    __tablename__="reports"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str]=mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    analysis_id: Mapped[str | None]=mapped_column(String(36), nullable=True, index=True)
    decision_id: Mapped[str | None]=mapped_column(String(36), nullable=True, index=True)
    report_type: Mapped[str | None]=mapped_column(String(80), nullable=True, index=True)
    format: Mapped[str]=mapped_column(String(16))
    storage_ref: Mapped[str | None]=mapped_column(Text, nullable=True)
    payload: Mapped[dict | None]=mapped_column(JSON, nullable=True)
    status: Mapped[str]=mapped_column(String(24), default="generated")
    approved_by_user_id: Mapped[str | None]=mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    approved_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[str]=mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class AuditRow(Base):
    __tablename__="audit_logs"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    actor: Mapped[str | None]=mapped_column(String(320), nullable=True)
    actor_user_id: Mapped[str | None]=mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    workspace_id: Mapped[str | None]=mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    request_id: Mapped[str | None]=mapped_column(String(128), nullable=True, index=True)
    trace_id: Mapped[str | None]=mapped_column(String(32), nullable=True, index=True)
    span_id: Mapped[str | None]=mapped_column(String(16), nullable=True)
    action: Mapped[str]=mapped_column(String(120))
    resource_type: Mapped[str]=mapped_column(String(80))
    resource_id: Mapped[str | None]=mapped_column(String(120), nullable=True)
    detail: Mapped[str]=mapped_column(Text, default="{}")
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

def init_db():
    # SQLite developer/test mode self-bootstraps. PostgreSQL and every other production
    # dialect must use Alembic so RLS, constraints, indexes, and the full production
    # schema cannot be silently skipped by ORM create_all().
    auto = os.getenv("RIVEXIS_AUTO_CREATE_SCHEMA", "").lower() in {"1", "true", "yes", "on"}
    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(engine)
        return
    if auto:
        raise RuntimeError(
            "RIVEXIS_AUTO_CREATE_SCHEMA is SQLite-only; production databases must use the dedicated Alembic migration job"
        )
