from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, func, select

from rivexis_api.services.db import AuditRow, ProviderRequestRow, ReportRow, SessionLocal


def _days(name: str, default: int) -> int:
    try:
        return max(0, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def policy() -> dict[str, Any]:
    return {
        "provider_requests_days": _days("RIVEXIS_RETENTION_PROVIDER_REQUESTS_DAYS", 90),
        "audit_logs_days": _days("RIVEXIS_RETENTION_AUDIT_LOGS_DAYS", 365),
        # 0 means indefinite by default. Reports can contain analyst evidence and
        # should not be destroyed merely because telemetry retention elapsed.
        "reports_days": _days("RIVEXIS_RETENTION_REPORTS_DAYS", 0),
        "delete_enabled": os.getenv("RIVEXIS_RETENTION_ALLOW_DELETE", "false").lower() in {"1","true","yes","on"},
        "report_delete_enabled": os.getenv("RIVEXIS_RETENTION_ALLOW_REPORT_DELETE", "false").lower() in {"1","true","yes","on"},
    }


def retention_plan(*, workspace_id: str | None = None, reference_time: datetime | None = None) -> dict[str, Any]:
    ref = reference_time or datetime.now(timezone.utc)
    cfg = policy()
    specs = [
        ("provider_requests", ProviderRequestRow, cfg["provider_requests_days"]),
        ("audit_logs", AuditRow, cfg["audit_logs_days"]),
        ("reports", ReportRow, cfg["reports_days"]),
    ]
    items=[]
    with SessionLocal() as db:
        for name, model, days in specs:
            if days <= 0:
                items.append({"dataset":name,"retention_days":days,"enabled":False,"eligible_rows":0,"cutoff":None})
                continue
            cutoff=ref-timedelta(days=days)
            cond=[model.created_at < cutoff]
            if workspace_id is not None and hasattr(model,"workspace_id"):
                cond.append(model.workspace_id==workspace_id)
            count=db.scalar(select(func.count()).select_from(model).where(*cond)) or 0
            items.append({"dataset":name,"retention_days":days,"enabled":True,"eligible_rows":int(count),"cutoff":cutoff.isoformat()})
    return {"reference_time":ref.isoformat(),"workspace_id":workspace_id,"policy":cfg,"items":items,"dry_run":True}


def apply_retention(*, workspace_id: str | None = None, reference_time: datetime | None = None) -> dict[str, Any]:
    cfg=policy()
    if not cfg["delete_enabled"]:
        raise PermissionError("Retention deletion is disabled; set RIVEXIS_RETENTION_ALLOW_DELETE=true for an approved maintenance window")
    ref=reference_time or datetime.now(timezone.utc)
    specs=[
        ("provider_requests",ProviderRequestRow,cfg["provider_requests_days"],True),
        ("audit_logs",AuditRow,cfg["audit_logs_days"],True),
        ("reports",ReportRow,cfg["reports_days"],cfg["report_delete_enabled"]),
    ]
    deleted={}
    with SessionLocal() as db:
        for name,model,days,allowed in specs:
            if days<=0 or not allowed:
                deleted[name]=0;continue
            cutoff=ref-timedelta(days=days);cond=[model.created_at < cutoff]
            if workspace_id is not None and hasattr(model,"workspace_id"):
                cond.append(model.workspace_id==workspace_id)
            result=db.execute(delete(model).where(*cond));deleted[name]=int(result.rowcount or 0)
        db.commit()
    return {"reference_time":ref.isoformat(),"workspace_id":workspace_id,"deleted":deleted,"policy":cfg,"dry_run":False}
