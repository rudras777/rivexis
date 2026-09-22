from __future__ import annotations
import json
from datetime import timedelta
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError
from rivexis_api.core.context import get_request_id, get_span_id, get_trace_id, set_organization_context, reset_organization_context
from rivexis_api.services.db import (
    AlertRow, AnalysisRow, AuditRow, DataSourceRow, DecisionRow, MonitorRow, OrganizationMemberRow,
    OrganizationRow, PortfolioRow, ProviderRequestRow, ReportRow, SavedAnalysisRow, SessionLocal, UserRow, WorkspaceRow, now,
)

ORG_ROLES={"OWNER","ADMIN","ANALYST","VIEWER"}
WRITE_ROLES={"OWNER","ADMIN","ANALYST"}
MANAGE_ROLES={"OWNER","ADMIN"}

def create_user(email, password_hash, role):
    email=email.lower().strip()
    with SessionLocal() as db:
        if db.scalar(select(UserRow).where(UserRow.email==email)): raise ValueError("Email already registered")
        u=UserRow(email=email,password_hash=password_hash,role=role); db.add(u); db.commit(); db.refresh(u); return u

def get_user(email):
    with SessionLocal() as db: return db.scalar(select(UserRow).where(UserRow.email==email.lower().strip()))

def get_user_by_id(user_id):
    with SessionLocal() as db: return db.get(UserRow,user_id)


def bump_user_token_version(user_id):
    with SessionLocal() as db:
        u=db.get(UserRow,user_id)
        if not u:return None
        u.token_version=(u.token_version or 0)+1;db.commit();db.refresh(u);return u.token_version

def update_user_role(user_id,role):
    with SessionLocal() as db:
        u=db.get(UserRow,user_id)
        if not u:return None
        u.role=role; db.commit(); db.refresh(u); return u

def create_organization(user_id,name):
    with SessionLocal() as db:
        org=OrganizationRow(name=name);db.add(org);db.flush()
        db.add(OrganizationMemberRow(organization_id=org.id,user_id=user_id,role="OWNER"));db.commit();db.refresh(org)
        return {"id":org.id,"name":org.name,"member_role":"OWNER","created_at":org.created_at.isoformat()}

def _org_role(db,user_id,organization_id):
    if not organization_id:return None
    m=db.scalar(select(OrganizationMemberRow).where(OrganizationMemberRow.organization_id==organization_id,OrganizationMemberRow.user_id==user_id))
    return m.role if m else None

def list_organizations(user_id):
    with SessionLocal() as db:
        rows=db.execute(select(OrganizationRow,OrganizationMemberRow.role).join(OrganizationMemberRow,OrganizationMemberRow.organization_id==OrganizationRow.id).where(OrganizationMemberRow.user_id==user_id).order_by(OrganizationRow.created_at.desc())).all()
        return [{"id":o.id,"name":o.name,"member_role":role,"created_at":o.created_at.isoformat()} for o,role in rows]

def organization_access(user_id,organization_id,write=False,manage=False):
    with SessionLocal() as db:
        role=_org_role(db,user_id,organization_id)
        if not role:return None
        if manage and role not in MANAGE_ROLES:return None
        if write and role not in WRITE_ROLES:return None
        org=db.get(OrganizationRow,organization_id)
        return ({"id":org.id,"name":org.name,"member_role":role} if org else None)

def list_organization_members(user_id,organization_id):
    access=organization_access(user_id,organization_id)
    if not access:return None
    tokens=set_organization_context(organization_id,access["member_role"])
    try:
        with SessionLocal() as db:
            rows=db.execute(select(OrganizationMemberRow,UserRow).join(UserRow,UserRow.id==OrganizationMemberRow.user_id).where(OrganizationMemberRow.organization_id==organization_id).order_by(OrganizationMemberRow.created_at)).all()
            return [{"user_id":u.id,"email":u.email,"role":m.role,"created_at":m.created_at.isoformat()} for m,u in rows]
    finally:
        reset_organization_context(tokens)

def _upsert_organization_member(db, actor_role, organization_id, user, role):
    existing=db.scalar(select(OrganizationMemberRow).where(
        OrganizationMemberRow.organization_id==organization_id,
        OrganizationMemberRow.user_id==user.id,
    ))
    existing_role=existing.role if existing else None
    if actor_role!="OWNER" and (role=="OWNER" or existing_role=="OWNER"):
        raise PermissionError("Only an organization owner may grant or modify OWNER membership")
    if existing_role=="OWNER" and role!="OWNER":
        owner_count=db.scalar(select(func.count()).select_from(OrganizationMemberRow).where(
            OrganizationMemberRow.organization_id==organization_id,
            OrganizationMemberRow.role=="OWNER",
        )) or 0
        if owner_count<=1:
            raise ValueError("Cannot demote the last organization owner")
    if existing:
        existing.role=role
    else:
        db.add(OrganizationMemberRow(organization_id=organization_id,user_id=user.id,role=role))
    db.commit()
    return {"organization_id":organization_id,"user_id":user.id,"email":user.email,"role":role}


def add_organization_member(actor_user_id,organization_id,email,role,*,allow_new=True):
    if role not in ORG_ROLES:raise ValueError("Invalid organization role")
    access=organization_access(actor_user_id,organization_id,manage=True)
    if not access:raise PermissionError("Organization administration required")
    actor_role=access["member_role"]
    tokens=set_organization_context(organization_id,actor_role)
    try:
        with SessionLocal() as db:
            user=db.scalar(select(UserRow).where(UserRow.email==email.lower().strip()))
            if not user:raise LookupError("User must already have a Rivexis account")
            existing=db.scalar(select(OrganizationMemberRow).where(
                OrganizationMemberRow.organization_id==organization_id,
                OrganizationMemberRow.user_id==user.id,
            ))
            if not existing and not allow_new:
                raise PermissionError("New organization members require an authenticated membership claim")
            return _upsert_organization_member(db,actor_role,organization_id,user,role)
    finally:
        reset_organization_context(tokens)


def add_organization_member_by_claim(actor_user_id,organization_id,target_user_id,role):
    if role not in ORG_ROLES:raise ValueError("Invalid organization role")
    access=organization_access(actor_user_id,organization_id,manage=True)
    if not access:raise PermissionError("Organization administration required")
    actor_role=access["member_role"]
    tokens=set_organization_context(organization_id,actor_role)
    try:
        with SessionLocal() as db:
            user=db.get(UserRow,target_user_id)
            if not user:raise LookupError("Membership-claim user no longer exists")
            return _upsert_organization_member(db,actor_role,organization_id,user,role)
    finally:
        reset_organization_context(tokens)

def remove_organization_member(actor_user_id,organization_id,target_user_id):
    access=organization_access(actor_user_id,organization_id,manage=True)
    if not access:raise PermissionError("Organization administration required")
    actor_role=access["member_role"]
    tokens=set_organization_context(organization_id,actor_role)
    try:
        with SessionLocal() as db:
            row=db.scalar(select(OrganizationMemberRow).where(OrganizationMemberRow.organization_id==organization_id,OrganizationMemberRow.user_id==target_user_id))
            if not row:return False
            if row.role=="OWNER":
                if actor_role!="OWNER":
                    raise PermissionError("Only an organization owner may remove OWNER membership")
                owners=list(db.scalars(select(OrganizationMemberRow).where(OrganizationMemberRow.organization_id==organization_id,OrganizationMemberRow.role=="OWNER")))
                if len(owners)<=1:raise ValueError("Cannot remove the last organization owner")
            db.delete(row);db.commit();return True
    finally:
        reset_organization_context(tokens)

def create_workspace(user_id,name,role,organization_id=None):
    org_access=None
    if organization_id:
        org_access=organization_access(user_id,organization_id,write=True)
        if not org_access:raise PermissionError("Organization write access required")
    with SessionLocal() as db:
        # owner_user_id records the creator for lineage/audit. For organization workspaces it
        # is NOT an authorization grant; live access is derived from current org membership.
        r=WorkspaceRow(owner_user_id=user_id,organization_id=organization_id,name=name,role=role);db.add(r);db.commit();db.refresh(r)
        return _workspace(r,user_id,org_access["member_role"] if org_access else None)

def _workspace(row,user_id,member_role=None):
    if row.organization_id:
        access=member_role or "VIEWER"
    else:
        access="OWNER" if row.owner_user_id==user_id else (member_role or "VIEWER")
    return {"id":row.id,"name":row.name,"role":row.role,"organization_id":row.organization_id,"access_role":access,"created_at":row.created_at.isoformat()}

def list_workspaces(user_id):
    with SessionLocal() as db:
        memberships={m.organization_id:m.role for m in db.scalars(select(OrganizationMemberRow).where(OrganizationMemberRow.user_id==user_id))}
        org_ids=list(memberships)
        # Personal workspaces are owner-based. Organization workspaces are membership-based
        # only; creator lineage must never survive organization membership revocation.
        cond=[(WorkspaceRow.owner_user_id==user_id) & WorkspaceRow.organization_id.is_(None)]
        if org_ids:cond.append(WorkspaceRow.organization_id.in_(org_ids))
        rows=list(db.scalars(select(WorkspaceRow).where(or_(*cond)).order_by(WorkspaceRow.created_at.desc())))
        return [_workspace(r,user_id,memberships.get(r.organization_id)) for r in rows]

def workspace_access(user_id,workspace_id,write=False,manage=False):
    with SessionLocal() as db:
        row=db.get(WorkspaceRow,workspace_id)
        if not row:return None
        if row.organization_id:
            role=_org_role(db,user_id,row.organization_id)
        else:
            role="OWNER" if row.owner_user_id==user_id else None
        if not role:return None
        if manage and role not in MANAGE_ROLES:return None
        if write and role not in WRITE_ROLES:return None
        return _workspace(row,user_id,role)

def default_workspace(user_id,write=False):
    for w in list_workspaces(user_id):
        if not write or w["access_role"] in WRITE_ROLES:return w
    return None

def update_workspace(user_id,workspace_id,name,role):
    access=workspace_access(user_id,workspace_id,manage=True)
    if not access:return None
    with SessionLocal() as db:
        r=db.get(WorkspaceRow,workspace_id)
        if not r:return None
        r.name=name;r.role=role;db.commit();db.refresh(r);return _workspace(r,user_id,access["access_role"])

def save_engine_result(result,user_id=None,workspace_id=None):
    data=result.model_dump(mode="json")
    with SessionLocal() as db:
        db.merge(AnalysisRow(id=result.analysis_id,engine_id=result.engine_id.value,owner_user_id=user_id,workspace_id=workspace_id,payload=json.dumps(data),demo=result.demo)); db.commit()
    return data

def analysis_record(analysis_id):
    with SessionLocal() as db:
        row=db.get(AnalysisRow,analysis_id)
        if not row:return None
        return {"id":row.id,"workspace_id":row.workspace_id,"owner_user_id":row.owner_user_id,"payload":json.loads(row.payload),"created_at":row.created_at.isoformat()}

def analysis_by_id(analysis_id,user_id=None):
    rec=analysis_record(analysis_id)
    if not rec:return None
    if user_id is not None and rec["workspace_id"] and not workspace_access(user_id,rec["workspace_id"]):return None
    if user_id is not None and not rec["workspace_id"] and rec["owner_user_id"] not in (None,user_id):return None
    return rec["payload"]

def save_decision(result,user_id=None,workspace_id=None):
    with SessionLocal() as db: db.merge(DecisionRow(id=result.decision_id,owner_user_id=user_id,workspace_id=workspace_id,payload=json.dumps(result.model_dump(mode="json")))); db.commit()

def decision_record(decision_id):
    with SessionLocal() as db:
        row=db.get(DecisionRow,decision_id)
        if not row:return None
        return {"id":row.id,"workspace_id":row.workspace_id,"owner_user_id":row.owner_user_id,"payload":json.loads(row.payload),"created_at":row.created_at.isoformat()}

def decision_by_id(decision_id,user_id=None):
    rec=decision_record(decision_id)
    if not rec:return None
    if user_id is not None and rec["workspace_id"] and not workspace_access(user_id,rec["workspace_id"]):return None
    if user_id is not None and not rec["workspace_id"] and rec["owner_user_id"] not in (None,user_id):return None
    return rec["payload"]

def history(user_id,limit=50,workspace_id=None):
    allowed=[w["id"] for w in list_workspaces(user_id)]
    if workspace_id:
        if workspace_id not in allowed:return []
        allowed=[workspace_id]
    if not allowed:return []
    with SessionLocal() as db:
        analyses=list(db.scalars(select(AnalysisRow).where(AnalysisRow.workspace_id.in_(allowed)).order_by(AnalysisRow.created_at.desc()).limit(limit)))
        decisions=list(db.scalars(select(DecisionRow).where(DecisionRow.workspace_id.in_(allowed)).order_by(DecisionRow.created_at.desc()).limit(limit)))
    items=[{"type":"analysis","id":x.id,"workspace_id":x.workspace_id,"engine_id":x.engine_id,"demo":x.demo,"created_at":x.created_at.isoformat()} for x in analyses]
    items += [{"type":"decision","id":x.id,"workspace_id":x.workspace_id,"created_at":x.created_at.isoformat()} for x in decisions]
    return sorted(items,key=lambda x:x["created_at"],reverse=True)[:limit]

def create_saved_analysis(user_id,workspace_id,analysis_id,title):
    with SessionLocal() as db:
        existing=db.scalar(select(SavedAnalysisRow).where(SavedAnalysisRow.user_id==user_id,SavedAnalysisRow.analysis_id==analysis_id))
        if existing:
            existing.title=title;existing.archived=False;existing.workspace_id=workspace_id;db.commit();db.refresh(existing);return _saved(existing)
        row=SavedAnalysisRow(user_id=user_id,workspace_id=workspace_id,analysis_id=analysis_id,title=title);db.add(row);db.commit();db.refresh(row);return _saved(row)
def _saved(row):return {"id":row.id,"workspace_id":row.workspace_id,"analysis_id":row.analysis_id,"title":row.title,"archived":row.archived,"created_at":row.created_at.isoformat()}
def list_saved_analyses(user_id,include_archived=False,workspace_id=None):
    with SessionLocal() as db:
        q=select(SavedAnalysisRow).where(SavedAnalysisRow.user_id==user_id)
        if workspace_id:q=q.where(SavedAnalysisRow.workspace_id==workspace_id)
        if not include_archived:q=q.where(SavedAnalysisRow.archived.is_(False))
        return [_saved(x) for x in db.scalars(q.order_by(SavedAnalysisRow.created_at.desc()))]
def set_saved_analysis_archived(user_id,saved_id,archived):
    with SessionLocal() as db:
        row=db.scalar(select(SavedAnalysisRow).where(SavedAnalysisRow.id==saved_id,SavedAnalysisRow.user_id==user_id))
        if not row:return None
        row.archived=archived;db.commit();db.refresh(row);return _saved(row)
def delete_saved_analysis(user_id,saved_id):
    with SessionLocal() as db:
        row=db.scalar(select(SavedAnalysisRow).where(SavedAnalysisRow.id==saved_id,SavedAnalysisRow.user_id==user_id))
        if not row:return False
        db.delete(row);db.commit();return True

def create_portfolio(user_id,workspace_id,name,payload):
    with SessionLocal() as db:
        row=PortfolioRow(owner_user_id=user_id,workspace_id=workspace_id,name=name,payload=json.dumps(payload));db.add(row);db.commit();db.refresh(row);return {"id":row.id,"workspace_id":row.workspace_id,"name":row.name,**payload}
def portfolio_by_id(user_id,portfolio_id):
    with SessionLocal() as db:
        row=db.get(PortfolioRow,portfolio_id)
        if not row or (row.workspace_id and not workspace_access(user_id,row.workspace_id)) or (not row.workspace_id and row.owner_user_id!=user_id):return None
        return {"id":row.id,"workspace_id":row.workspace_id,"name":row.name,**json.loads(row.payload)}

def create_monitor(user_id,workspace_id,entity,chain,rules,config):
    with SessionLocal() as db:
        row=MonitorRow(workspace_id=workspace_id,created_by_user_id=user_id,entity=entity,chain=chain,rules=json.dumps(rules),config=json.dumps(config));db.add(row);db.commit();db.refresh(row);return _monitor(row)
def _monitor(row):
    return {"id":row.id,"workspace_id":row.workspace_id,"entity":row.entity,"chain":row.chain,"rules":json.loads(row.rules),"config":json.loads(row.config),"status":row.status,"last_snapshot":json.loads(row.last_snapshot) if row.last_snapshot else None,"last_analysis_id":row.last_analysis_id,"last_status":row.last_status,"created_at":row.created_at.isoformat(),"updated_at":row.updated_at.isoformat()}
def list_monitors(user_id,workspace_id=None):
    allowed=[w["id"] for w in list_workspaces(user_id)]
    if workspace_id:
        if workspace_id not in allowed:return []
        allowed=[workspace_id]
    if not allowed:return []
    with SessionLocal() as db:return [_monitor(x) for x in db.scalars(select(MonitorRow).where(MonitorRow.workspace_id.in_(allowed)).order_by(MonitorRow.created_at.desc()))]
def get_monitor(user_id,monitor_id,write=False):
    with SessionLocal() as db:
        row=db.get(MonitorRow,monitor_id)
        if not row or not workspace_access(user_id,row.workspace_id,write=write):return None
        return _monitor(row)
def get_monitor_internal(monitor_id):
    """Internal integration lookup. Caller must perform its own authentication/authorization checks."""
    with SessionLocal() as db:
        row=db.get(MonitorRow,monitor_id)
        return _monitor(row) if row else None

def update_monitor(user_id,monitor_id,entity=None,chain=None,rules=None,config=None,last_snapshot=None,last_analysis_id=None,last_status=None):
    with SessionLocal() as db:
        row=db.get(MonitorRow,monitor_id)
        if not row or not workspace_access(user_id,row.workspace_id,write=True):return None
        if entity is not None:row.entity=entity
        if chain is not None:row.chain=chain
        if rules is not None:row.rules=json.dumps(rules)
        if config is not None:row.config=json.dumps(config)
        if last_snapshot is not None:row.last_snapshot=json.dumps(last_snapshot)
        if last_analysis_id is not None:row.last_analysis_id=last_analysis_id
        if last_status is not None:row.last_status=last_status
        db.commit();db.refresh(row);return _monitor(row)
def delete_monitor(user_id,monitor_id):
    with SessionLocal() as db:
        row=db.get(MonitorRow,monitor_id)
        if not row or not workspace_access(user_id,row.workspace_id,write=True):return False
        db.delete(row);db.commit();return True

def create_alert(workspace_id,monitor_id,analysis_id,severity,payload,provider_id=None,external_event_key=None):
    with SessionLocal() as db:
        if provider_id and external_event_key:
            existing=db.scalar(select(AlertRow).where(
                AlertRow.workspace_id==workspace_id,
                AlertRow.provider_id==provider_id,
                AlertRow.external_event_key==external_event_key,
            ))
            if existing:
                existing.occurrence_count=(existing.occurrence_count or 1)+1
                existing.last_seen_at=now()
                db.commit();db.refresh(existing)
                out=_alert(existing);out["duplicate"]=True;return out
        row=AlertRow(
            workspace_id=workspace_id,monitor_id=monitor_id,analysis_id=analysis_id,severity=severity,status="open",
            provider_id=provider_id,external_event_key=external_event_key,payload=json.dumps(payload),
        )
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            if provider_id and external_event_key:
                existing=db.scalar(select(AlertRow).where(
                    AlertRow.workspace_id==workspace_id,
                    AlertRow.provider_id==provider_id,
                    AlertRow.external_event_key==external_event_key,
                ))
                if existing:
                    out=_alert(existing);out["duplicate"]=True;return out
            raise
        db.refresh(row);out=_alert(row);out["duplicate"]=False;return out
def _alert(row):
    return {
        "id":row.id,"workspace_id":row.workspace_id,"monitor_id":row.monitor_id,"analysis_id":row.analysis_id,
        "severity":row.severity,"status":row.status,"provider_id":row.provider_id,"external_event_key":row.external_event_key,
        "occurrence_count":row.occurrence_count,"first_seen_at":row.first_seen_at.isoformat() if row.first_seen_at else None,
        "last_seen_at":row.last_seen_at.isoformat() if row.last_seen_at else None,"delivery_status":row.delivery_status,
        "delivery_attempts":row.delivery_attempts,"next_delivery_at":row.next_delivery_at.isoformat() if row.next_delivery_at else None,
        "last_delivery_error":row.last_delivery_error,"delivered_at":row.delivered_at.isoformat() if row.delivered_at else None,
        "dead_lettered_at":row.dead_lettered_at.isoformat() if row.dead_lettered_at else None,
        "payload":json.loads(row.payload),"created_at":row.created_at.isoformat(),"updated_at":row.updated_at.isoformat(),
    }
def list_alerts(user_id,workspace_id=None):
    allowed=[w["id"] for w in list_workspaces(user_id)]
    if workspace_id:
        if workspace_id not in allowed:return []
        allowed=[workspace_id]
    if not allowed:return []
    with SessionLocal() as db:return [_alert(x) for x in db.scalars(select(AlertRow).where(AlertRow.workspace_id.in_(allowed)).order_by(AlertRow.created_at.desc()))]
def update_alert_status(user_id,alert_id,status):
    if status not in {"open","acknowledged","resolved"}:raise ValueError("Invalid alert status")
    with SessionLocal() as db:
        row=db.get(AlertRow,alert_id)
        if not row or not workspace_access(user_id,row.workspace_id,write=True):return None
        row.status=status;db.commit();db.refresh(row);return _alert(row)


def due_alerts(workspace_id,limit=50):
    current=now()
    with SessionLocal() as db:
        rows=list(db.scalars(select(AlertRow).where(
            AlertRow.workspace_id==workspace_id,
            AlertRow.delivery_status.in_(("pending","retry")),
            or_(AlertRow.next_delivery_at.is_(None),AlertRow.next_delivery_at<=current),
        ).order_by(AlertRow.created_at.asc()).limit(max(1,min(int(limit),200)))))
        return [_alert(r) for r in rows]


def due_alert_workspace_ids(limit=100):
    current=now()
    with SessionLocal() as db:
        rows=db.execute(select(AlertRow.workspace_id).where(
            AlertRow.delivery_status.in_(("pending","retry")),
            or_(AlertRow.next_delivery_at.is_(None),AlertRow.next_delivery_at<=current),
        ).distinct().limit(max(1,min(int(limit),1000)))).all()
    return [row[0] for row in rows if row[0]]

def mark_alert_delivery(alert_id,*,success,error=None,max_attempts=5,retry_base_seconds=30):
    with SessionLocal() as db:
        row=db.get(AlertRow,alert_id)
        if not row:return None
        row.delivery_attempts=(row.delivery_attempts or 0)+1
        if success:
            row.delivery_status="delivered";row.delivered_at=now();row.next_delivery_at=None;row.last_delivery_error=None
        else:
            row.last_delivery_error=(error or "delivery failed")[:2000]
            if row.delivery_attempts>=max(1,int(max_attempts)):
                row.delivery_status="dead_letter";row.dead_lettered_at=now();row.next_delivery_at=None
            else:
                row.delivery_status="retry"
                delay=max(1,int(retry_base_seconds))*(2**max(0,row.delivery_attempts-1))
                row.next_delivery_at=now()+timedelta(seconds=min(delay,86400))
        db.commit();db.refresh(row);return _alert(row)

def requeue_alert(user_id,alert_id):
    with SessionLocal() as db:
        row=db.get(AlertRow,alert_id)
        if not row or not workspace_access(user_id,row.workspace_id,manage=True):return None
        row.delivery_status="pending";row.delivery_attempts=0;row.next_delivery_at=None;row.last_delivery_error=None;row.dead_lettered_at=None
        db.commit();db.refresh(row);return _alert(row)

def alert_delivery_metrics(user_id,workspace_id,slo_seconds=300):
    if not workspace_access(user_id,workspace_id):return None
    current=now();cutoff=current-timedelta(hours=24);slo=max(1,int(slo_seconds))
    with SessionLocal() as db:
        rows=list(db.scalars(select(AlertRow).where(AlertRow.workspace_id==workspace_id,AlertRow.created_at>=cutoff)))
    pending=[r for r in rows if r.delivery_status in {"pending","retry"}]
    delivered=[r for r in rows if r.delivery_status=="delivered" and r.delivered_at]
    within=sum(1 for r in delivered if (r.delivered_at-r.created_at).total_seconds()<=slo)
    oldest=max(((current-r.created_at).total_seconds() for r in pending),default=0.0)
    return {
        "workspace_id":workspace_id,"window_hours":24,"slo_seconds":slo,"total":len(rows),
        "pending":len(pending),"delivered":len(delivered),"dead_letter":sum(1 for r in rows if r.delivery_status=="dead_letter"),
        "oldest_pending_age_seconds":round(oldest,3),
        "delivered_within_slo_percent":round((within/len(delivered))*100,2) if delivered else None,
    }

def create_report(user_id,workspace_id,decision_id,fmt):
    with SessionLocal() as db:
        row=ReportRow(workspace_id=workspace_id,decision_id=decision_id,report_type="decision",format=fmt,status="generated",created_by_user_id=user_id);db.add(row);db.commit();db.refresh(row);return _report(row)

def _report(row,include_payload=False):
    out={
        "id":row.id,"workspace_id":row.workspace_id,"analysis_id":row.analysis_id,"decision_id":row.decision_id,
        "report_type":row.report_type,"format":row.format,"storage_ref":row.storage_ref,"status":row.status,
        "approved_by_user_id":row.approved_by_user_id,"approved_at":row.approved_at.isoformat() if row.approved_at else None,
        "created_by_user_id":row.created_by_user_id,"created_at":row.created_at.isoformat(),
    }
    if include_payload: out["payload"]=row.payload
    return out

def get_report(user_id,report_id,include_payload=False):
    with SessionLocal() as db:
        row=db.get(ReportRow,report_id)
        if not row or not workspace_access(user_id,row.workspace_id):return None
        return _report(row,include_payload=include_payload)

def create_protocol_review(user_id,workspace_id,payload,fmt="json"):
    with SessionLocal() as db:
        row=ReportRow(
            workspace_id=workspace_id,decision_id=None,analysis_id=None,report_type="protocol_configuration_review",
            format=fmt,status="draft",payload=payload,created_by_user_id=user_id,
        )
        db.add(row);db.commit();db.refresh(row);return _report(row,include_payload=True)

def approve_protocol_review(user_id,report_id):
    with SessionLocal() as db:
        row=db.get(ReportRow,report_id)
        if not row or row.report_type!="protocol_configuration_review" or not workspace_access(user_id,row.workspace_id,manage=True):return None
        row.status="approved";row.approved_by_user_id=user_id;row.approved_at=now();db.commit();db.refresh(row)
        return _report(row,include_payload=True)

def audit(action,resource_type,resource_id=None,actor=None,actor_user_id=None,workspace_id=None,detail=None):
    with SessionLocal() as db:
        db.add(AuditRow(actor=actor,actor_user_id=actor_user_id,workspace_id=workspace_id,request_id=get_request_id(),trace_id=get_trace_id(),span_id=get_span_id(),action=action,resource_type=resource_type,resource_id=resource_id,detail=json.dumps(detail or {})));db.commit()

def list_audit_logs(user_id,workspace_id,limit=100):
    if not workspace_access(user_id,workspace_id,manage=True):return None
    with SessionLocal() as db:
        rows=list(db.scalars(select(AuditRow).where(AuditRow.workspace_id==workspace_id).order_by(AuditRow.created_at.desc()).limit(limit)))
        return [{"id":r.id,"actor":r.actor,"actor_user_id":r.actor_user_id,"request_id":r.request_id,"trace_id":r.trace_id,"span_id":r.span_id,"action":r.action,"resource_type":r.resource_type,"resource_id":r.resource_id,"detail":json.loads(r.detail),"created_at":r.created_at.isoformat()} for r in rows]


def record_provider_request_event(*,workspace_id,provider_key,operation,endpoint,status,latency_ms,attempts,retries,estimated_cost_usd,error_class=None,cache_hit=False):
    with SessionLocal() as db:
        source=db.scalar(select(DataSourceRow).where(DataSourceRow.provider_id==provider_key))
        if not source:
            source=DataSourceRow(provider_id=provider_key,provider_name=provider_key,category="runtime",enabled=True)
            db.add(source);db.flush()
        row=ProviderRequestRow(
            workspace_id=workspace_id,provider_id=source.id,provider_key=provider_key,operation=operation,endpoint=endpoint or None,
            status=status,latency_ms=latency_ms,estimated_cost=estimated_cost_usd,attempts=attempts,retries=retries,
            cache_hit=cache_hit,error_class=error_class,request_id_external=get_request_id(),trace_id=get_trace_id(),span_id=get_span_id(),
        )
        db.add(row);db.commit();db.refresh(row)
        return row.id

def list_provider_request_events(user_id,workspace_id,limit=100):
    if not workspace_access(user_id,workspace_id):return None
    with SessionLocal() as db:
        rows=list(db.scalars(select(ProviderRequestRow).where(ProviderRequestRow.workspace_id==workspace_id).order_by(ProviderRequestRow.created_at.desc()).limit(limit)))
        return [{
            "id":r.id,"workspace_id":r.workspace_id,"provider":r.provider_key,"operation":r.operation,"endpoint":r.endpoint,
            "status":r.status,"latency_ms":r.latency_ms,"estimated_cost_usd":r.estimated_cost,"attempts":r.attempts,
            "retries":r.retries,"cache_hit":r.cache_hit,"error_class":r.error_class,"request_id":r.request_id_external,"trace_id":r.trace_id,"span_id":r.span_id,
            "created_at":r.created_at.isoformat(),
        } for r in rows]


def provider_usage_summary(user_id,workspace_id,hours=24):
    if not workspace_access(user_id,workspace_id):return None
    cutoff=now()-timedelta(hours=max(1,min(int(hours),24*90)))
    success_statuses=("SUCCESS","CACHE_HIT")
    failure_statuses=("FAILED","CIRCUIT_OPEN","LOCAL_RATE_LIMIT")
    with SessionLocal() as db:
        rows=db.execute(
            select(
                ProviderRequestRow.provider_key,
                func.count(ProviderRequestRow.id),
                func.sum(case((ProviderRequestRow.status.in_(success_statuses),1),else_=0)),
                func.sum(case((ProviderRequestRow.status.in_(failure_statuses),1),else_=0)),
                func.sum(case((ProviderRequestRow.cache_hit.is_(True),1),else_=0)),
                func.coalesce(func.sum(ProviderRequestRow.attempts),0),
                func.coalesce(func.sum(ProviderRequestRow.retries),0),
                func.avg(ProviderRequestRow.latency_ms),
                func.coalesce(func.sum(ProviderRequestRow.estimated_cost),0.0),
            ).where(
                ProviderRequestRow.workspace_id==workspace_id,
                ProviderRequestRow.created_at>=cutoff,
            ).group_by(ProviderRequestRow.provider_key).order_by(ProviderRequestRow.provider_key)
        ).all()
    items=[]
    for provider,calls,successes,failures,cache_hits,attempts,retries,avg_latency,cost in rows:
        items.append({
            "provider":provider,"logical_events":int(calls or 0),"success_events":int(successes or 0),
            "failure_events":int(failures or 0),"cache_hits":int(cache_hits or 0),"attempts":int(attempts or 0),
            "retries":int(retries or 0),"average_latency_ms":round(float(avg_latency),2) if avg_latency is not None else None,
            "estimated_cost_usd":round(float(cost or 0.0),8),
        })
    return {"workspace_id":workspace_id,"window_hours":max(1,min(int(hours),24*90)),"from":cutoff.isoformat(),"items":items}

INVESTIGATION_STATUSES={"open","in_review","closed"}

def create_protocol_investigation(user_id,workspace_id,title,input_payload,timeline,notes=""):
    payload={
        "title":title,"input":input_payload,"timeline":timeline,"review_ids":[],
        "disposition":None,"notes":notes or "","status_history":[{"status":"open","at":now().isoformat(),"actor_user_id":user_id}],
    }
    with SessionLocal() as db:
        row=ReportRow(workspace_id=workspace_id,decision_id=None,analysis_id=None,report_type="protocol_investigation_case",format="json",status="open",payload=payload,created_by_user_id=user_id)
        db.add(row);db.commit();db.refresh(row);return _report(row,include_payload=True)

def get_protocol_investigation(user_id,case_id):
    with SessionLocal() as db:
        row=db.get(ReportRow,case_id)
        if not row or row.report_type!="protocol_investigation_case" or not workspace_access(user_id,row.workspace_id):return None
        return _report(row,include_payload=True)

def list_protocol_investigations(user_id,workspace_id):
    if not workspace_access(user_id,workspace_id):return None
    with SessionLocal() as db:
        rows=list(db.scalars(select(ReportRow).where(ReportRow.workspace_id==workspace_id,ReportRow.report_type=="protocol_investigation_case").order_by(ReportRow.created_at.desc())))
        return [_report(r,include_payload=True) for r in rows]

def update_protocol_investigation(user_id,case_id,*,status=None,disposition=None,notes=None):
    with SessionLocal() as db:
        row=db.get(ReportRow,case_id)
        if not row or row.report_type!="protocol_investigation_case" or not workspace_access(user_id,row.workspace_id,write=True):return None
        payload=dict(row.payload or {})
        if status is not None:
            if status not in INVESTIGATION_STATUSES:raise ValueError("Invalid investigation status")
            if status=="closed" and not (disposition or payload.get("disposition")):
                raise ValueError("A disposition is required before closing an investigation")
            if row.status!=status:
                history=list(payload.get("status_history") or [])
                history.append({"status":status,"at":now().isoformat(),"actor_user_id":user_id})
                payload["status_history"]=history
            row.status=status
        if disposition is not None: payload["disposition"]=disposition.strip() or None
        if notes is not None: payload["notes"]=notes
        row.payload=payload;db.commit();db.refresh(row);return _report(row,include_payload=True)

def attach_protocol_review_to_investigation(user_id,case_id,review_id):
    with SessionLocal() as db:
        case=db.get(ReportRow,case_id);review=db.get(ReportRow,review_id)
        if not case or case.report_type!="protocol_investigation_case" or not workspace_access(user_id,case.workspace_id,write=True):return None
        if not review or review.report_type!="protocol_configuration_review" or review.workspace_id!=case.workspace_id:return None
        payload=dict(case.payload or {});ids=list(payload.get("review_ids") or [])
        if review_id not in ids:ids.append(review_id)
        payload["review_ids"]=ids;case.payload=payload;db.commit();db.refresh(case);return _report(case,include_payload=True)

def trace_correlation(user_id,workspace_id,trace_id,limit=200):
    if not workspace_access(user_id,workspace_id):return None
    trace_id=(trace_id or "").strip().lower()
    if len(trace_id)!=32 or any(c not in "0123456789abcdef" for c in trace_id):raise ValueError("trace_id must be 32 lowercase hexadecimal characters")
    limit=max(1,min(int(limit),500))
    with SessionLocal() as db:
        providers=list(db.scalars(select(ProviderRequestRow).where(ProviderRequestRow.workspace_id==workspace_id,ProviderRequestRow.trace_id==trace_id).order_by(ProviderRequestRow.created_at.asc()).limit(limit)))
        audits=list(db.scalars(select(AuditRow).where(AuditRow.workspace_id==workspace_id,AuditRow.trace_id==trace_id).order_by(AuditRow.created_at.asc()).limit(limit)))
    return {
        "workspace_id":workspace_id,"trace_id":trace_id,
        "provider_requests":[{"id":r.id,"provider":r.provider_key,"operation":r.operation,"status":r.status,"latency_ms":r.latency_ms,"attempts":r.attempts,"retries":r.retries,"span_id":r.span_id,"request_id":r.request_id_external,"created_at":r.created_at.isoformat()} for r in providers],
        "audit_events":[{"id":r.id,"action":r.action,"resource_type":r.resource_type,"resource_id":r.resource_id,"span_id":r.span_id,"request_id":r.request_id,"created_at":r.created_at.isoformat()} for r in audits],
    }
