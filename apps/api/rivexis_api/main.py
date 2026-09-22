from __future__ import annotations
from contextlib import asynccontextmanager
import hashlib
import hmac
import json
import os
from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from rivexis_api.api.deps import current_user
from rivexis_api.api.schemas import (
    AnalysisRequest, HypernativeEvent, LoginRequest, MonitorCreate, OrganizationCreate, OrganizationMemberAdd, OrganizationMemberClaimAccept,
    PortfolioCreate, ProtocolInvestigationCreate, ProtocolInvestigationUpdate, ReportRequest, RoleUpdate, SavedAnalysisCreate, SignupRequest, WorkspaceCreate,
)
from rivexis_api.core.config import settings, validate_runtime_security
from rivexis_api.core.context import (
    reset_actor_user_id, reset_request_id, reset_workspace_id,
    set_actor_user_id, set_request_id, set_workspace_id,
)
from rivexis_api.core.security import create_csrf_token, create_membership_claim, create_token, decode_membership_claim, hash_password, verify_csrf_token, verify_password
from rivexis_api.core.telemetry import init_telemetry, request_span, shutdown_telemetry, telemetry_export_status
from rivexis_api.decision import analyze_decision
from rivexis_api.engines import ENGINES
from rivexis_api.models.decision import DecisionRequest, RivexisDecision
from rivexis_api.models.enums import EngineId
from rivexis_api.providers import ADAPTERS, FALLBACKS, provider_metadata, resolve_provider
from rivexis_api.provider_runtime import snapshot as provider_runtime_snapshot
from rivexis_api.provider_clients import ProviderError
from rivexis_api.services.db import init_db, validate_application_database_role
from rivexis_api.services.explanations import grounded_explanation
from rivexis_api.services.reports import decision_html, decision_pdf, protocol_investigation_html, protocol_investigation_pdf, protocol_review_html, protocol_review_pdf
from rivexis_api.services.alert_delivery import process_due_alerts
from rivexis_api.services.auth_rate_limit import clear_login_attempts, consume_login_attempt
from rivexis_api.services.protocol_adapters import protocol_adapter_capabilities
from rivexis_api.services.deployment_registry import list_protocol_deployments, REGISTRY_VERSION
from rivexis_api.services.registry_governance import registry_fingerprint
from rivexis_api.services.protocol_history import protocol_event_timeline, compare_protocol_configuration
from rivexis_api.version import API_VERSION
from rivexis_api.services.store import (
    add_organization_member, add_organization_member_by_claim, analysis_by_id, analysis_record, audit, bump_user_token_version, create_alert, create_monitor,
    create_organization, create_portfolio, create_report, create_protocol_review, create_saved_analysis, create_user,
    create_workspace, decision_by_id, default_workspace, delete_monitor, delete_saved_analysis,
    get_monitor, get_monitor_internal, get_report, get_user, get_user_by_id, history, list_alerts, list_audit_logs, list_monitors,
    list_organization_members, list_organizations, list_provider_request_events, provider_usage_summary, list_saved_analyses, list_workspaces,
    organization_access, portfolio_by_id, remove_organization_member, save_decision,
    save_engine_result, set_saved_analysis_archived, update_alert_status, update_monitor,
    alert_delivery_metrics, approve_protocol_review, attach_protocol_review_to_investigation, create_protocol_investigation, get_protocol_investigation, list_protocol_investigations, requeue_alert, update_protocol_investigation,
    trace_correlation, update_user_role, update_workspace, workspace_access,
)

ROLES={"Individual","Fund","Treasury","Analyst"}
ORG_ROLES={"OWNER","ADMIN","ANALYST","VIEWER"}
DUMMY_PASSWORD_HASH=hash_password("rivexis-login-timing-dummy-password")

@asynccontextmanager
async def lifespan(_:FastAPI):
    validate_runtime_security()
    init_db()
    validate_application_database_role()
    init_telemetry()
    try:
        yield
    finally:
        shutdown_telemetry()

app=FastAPI(title="Rivexis API",version=API_VERSION,lifespan=lifespan)


def _production() -> bool:
    return os.getenv("RIVEXIS_ENV", str(settings.environment or "development")).strip().lower() in {"production","prod"}


def _guard_provider_deep_probe(deep: bool) -> None:
    # Provider diagnostics use the GLOBAL control-plane scope. Exposing deep probes to
    # tenants in production lets one authenticated account consume shared RPC/provider
    # quota and degrade every workspace. Trusted release certification calls provider
    # adapters directly and is unaffected by this HTTP guard.
    if deep and _production():
        raise HTTPException(403,"Deep provider probes are not exposed through the production tenant API")


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name, token, httponly=True, secure=_production(),
        samesite=settings.session_cookie_samesite, max_age=settings.token_ttl_seconds, path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.session_cookie_name, path="/", secure=_production(),
        httponly=True, samesite=settings.session_cookie_samesite,
    )


def _hypernative_monitor_credential(root_secret: str, workspace_id: str, monitor_id: str) -> str:
    message=f"hypernative-monitor:v1:{workspace_id}:{monitor_id}".encode()
    return hmac.new(root_secret.encode(),message,hashlib.sha256).hexdigest()


def _enforce_login_budget(email: str) -> None:
    try:
        allowed=consume_login_attempt(email)
    except Exception as exc:
        raise HTTPException(503,"Authentication rate limiter unavailable") from exc
    if not allowed:
        raise HTTPException(429,"Too many login attempts")


@app.middleware("http")
async def request_context_and_security_headers(request:Request,call_next):
    if request.method.upper() in {"POST","PUT","PATCH","DELETE"} and request.url.path.startswith("/api/v1/"):
        session_token=request.cookies.get(settings.session_cookie_name,"")
        bearer_present=bool(request.headers.get("Authorization","").strip())
        csrf_exempt=request.url.path in {
            "/api/v1/auth/web/signup", "/api/v1/auth/web/login",
            "/api/v1/integrations/hypernative/events",
        }
        if session_token and not bearer_present and not csrf_exempt:
            if not verify_csrf_token(session_token,request.headers.get("X-Rivexis-CSRF","")):
                return JSONResponse(status_code=403,content={"detail":"CSRF validation failed"})
    incoming=request.headers.get("X-Request-ID","").strip()
    request_id=incoming[:128] if incoming and all(ch.isalnum() or ch in "-_.:" for ch in incoming) else str(uuid4())
    request.state.request_id=request_id
    request_token=set_request_id(request_id)
    actor_token=set_actor_user_id(None)
    workspace_token=set_workspace_id(None)
    # Start with a path-free name. The raw request path can contain tenant/resource IDs.
    # After FastAPI resolves routing, attach only the route template (e.g.
    # /api/v1/workspaces/{workspace_id}) to OTLP.
    with request_span(
        f"HTTP {request.method}",
        incoming_traceparent=request.headers.get("traceparent"),
        attributes={"http.request.method":request.method,"rivexis.request_id":request_id},
    ) as active_trace:
        trace=active_trace.context
        request.state.trace_id=trace.trace_id
        try:
            response=await call_next(request)
            route=getattr(request.scope.get("route"),"path",None)
            if isinstance(route,str) and route:
                active_trace.update_name(f"{request.method} {route}")
                active_trace.set_attribute("http.route",route)
            active_trace.set_status_code(response.status_code)
        finally:
            reset_workspace_id(workspace_token)
            reset_actor_user_id(actor_token)
            reset_request_id(request_token)
    response.headers["X-Request-ID"]=request_id
    response.headers["X-Rivexis-Trace-ID"]=trace.trace_id
    response.headers["traceparent"]=trace.traceparent
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Referrer-Policy"]="no-referrer"
    response.headers["Permissions-Policy"]="camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Resource-Policy"]="same-site"
    response.headers["Cache-Control"]="no-store"
    if _production():
        response.headers["Strict-Transport-Security"]="max-age=31536000; includeSubDomains"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["GET","POST","PATCH","DELETE","OPTIONS"],
    allow_headers=["Authorization","Content-Type","X-Request-ID","X-Rivexis-CSRF","X-Rivexis-Webhook-Secret","traceparent","tracestate"],
)

def _workspace(user,workspace_id:str|None,*,write=False,manage=False):
    w=workspace_access(user.id,workspace_id,write=write,manage=manage) if workspace_id else default_workspace(user.id,write=write)
    if not w: raise HTTPException(403,"No accessible workspace with the required permission")
    return w

def _analysis_for_user(user,analysis_id:str):
    r=analysis_by_id(analysis_id,user.id)
    if not r: raise HTTPException(404,"Analysis not found")
    return r

def _decision_for_user(user,decision_id:str):
    r=decision_by_id(decision_id,user.id)
    if not r: raise HTTPException(404,"Decision not found")
    return r

@app.get("/health")
def health(): return {"status":"ok","service":"rivexis-api","environment":settings.environment,"api_version":API_VERSION}

@app.post("/api/v1/auth/signup")
def signup(req:SignupRequest):
    if req.role not in ROLES: raise HTTPException(422,"Invalid role")
    _enforce_login_budget(req.email)
    if get_user(req.email): raise HTTPException(409,"Email already registered")
    try: u=create_user(req.email,hash_password(req.password),req.role)
    except ValueError as exc: raise HTTPException(409,str(exc)) from exc
    clear_login_attempts(req.email)
    token=create_token(u.email,u.role,u.token_version)
    audit("signup","user",u.id,actor=u.email,actor_user_id=u.id)
    return {"access_token":token,"token_type":"bearer","user":{"id":u.id,"email":u.email,"role":u.role}}

@app.post("/api/v1/auth/login")
def login(req:LoginRequest):
    _enforce_login_budget(req.email)
    u=get_user(req.email)
    encoded=u.password_hash if u else DUMMY_PASSWORD_HASH
    valid=verify_password(req.password,encoded)
    if not u or not valid: raise HTTPException(401,"Invalid credentials")
    clear_login_attempts(req.email)
    audit("login","user",u.id,actor=u.email,actor_user_id=u.id)
    return {"access_token":create_token(u.email,u.role,u.token_version),"token_type":"bearer","user":{"id":u.id,"email":u.email,"role":u.role}}

@app.post("/api/v1/auth/web/signup")
def web_signup(req:SignupRequest,response:Response):
    if req.role not in ROLES: raise HTTPException(422,"Invalid role")
    _enforce_login_budget(req.email)
    if get_user(req.email): raise HTTPException(409,"Email already registered")
    try: u=create_user(req.email,hash_password(req.password),req.role)
    except ValueError as exc: raise HTTPException(409,str(exc)) from exc
    clear_login_attempts(req.email)
    token=create_token(u.email,u.role,u.token_version)
    _set_session_cookie(response,token)
    audit("signup","user",u.id,actor=u.email,actor_user_id=u.id,detail={"session":"cookie"})
    return {"csrf_token":create_csrf_token(token),"user":{"id":u.id,"email":u.email,"role":u.role}}

@app.post("/api/v1/auth/web/login")
def web_login(req:LoginRequest,response:Response):
    _enforce_login_budget(req.email)
    u=get_user(req.email)
    encoded=u.password_hash if u else DUMMY_PASSWORD_HASH
    valid=verify_password(req.password,encoded)
    if not u or not valid: raise HTTPException(401,"Invalid credentials")
    clear_login_attempts(req.email)
    token=create_token(u.email,u.role,u.token_version)
    _set_session_cookie(response,token)
    audit("login","user",u.id,actor=u.email,actor_user_id=u.id,detail={"session":"cookie"})
    return {"csrf_token":create_csrf_token(token),"user":{"id":u.id,"email":u.email,"role":u.role}}

@app.get("/api/v1/auth/web/csrf")
def web_csrf(request:Request,user=Depends(current_user)):
    if getattr(request.state,"auth_source","")!="cookie":
        raise HTTPException(400,"CSRF token is only available for cookie sessions")
    return {"csrf_token":create_csrf_token(request.state.session_token)}

@app.post("/api/v1/auth/logout")
def logout(request:Request,response:Response,user=Depends(current_user)):
    audit("logout","user",user.id,actor=user.email,actor_user_id=user.id)
    bump_user_token_version(user.id)
    if getattr(request.state,"auth_source","")=="cookie":
        _clear_session_cookie(response)
    return {"status":"revoked","scope":"all_current_sessions_for_user"}

@app.get("/api/v1/me")
def me(user=Depends(current_user)): return {"id":user.id,"email":user.email,"role":user.role}

@app.post("/api/v1/organizations/{organization_id}/membership-claim")
def organization_membership_claim(organization_id:str,user=Depends(current_user)):
    token=create_membership_claim(user.id,organization_id,user.token_version or 0)
    audit("organization.membership_claim.create","organization",organization_id,actor=user.email,actor_user_id=user.id)
    return {"organization_id":organization_id,"claim_token":token,"expires_in_seconds":settings.membership_claim_ttl_seconds}

@app.patch("/api/v1/me/role")
def me_role(req:RoleUpdate,user=Depends(current_user)):
    if req.role not in ROLES: raise HTTPException(422,"Invalid role")
    u=update_user_role(user.id,req.role)
    audit("user.role.update","user",user.id,actor=user.email,actor_user_id=user.id,detail={"role":req.role})
    return {"id":u.id,"email":u.email,"role":u.role}

@app.get("/api/v1/organizations")
def organizations(user=Depends(current_user)): return {"items":list_organizations(user.id)}

@app.post("/api/v1/organizations")
def organization_create(req:OrganizationCreate,user=Depends(current_user)):
    org=create_organization(user.id,req.name)
    audit("organization.create","organization",org["id"],actor=user.email,actor_user_id=user.id,detail={"name":req.name})
    return org

@app.get("/api/v1/organizations/{organization_id}/members")
def organization_members(organization_id:str,user=Depends(current_user)):
    rows=list_organization_members(user.id,organization_id)
    if rows is None: raise HTTPException(404,"Organization not found")
    return {"items":rows}

@app.post("/api/v1/organizations/{organization_id}/members")
def organization_member_add(organization_id:str,req:OrganizationMemberAdd,user=Depends(current_user)):
    if req.role not in ORG_ROLES: raise HTTPException(422,"Invalid organization role")
    try:r=add_organization_member(
        user.id,organization_id,req.email,req.role,allow_new=settings.allow_direct_org_member_add
    )
    except PermissionError as exc: raise HTTPException(403,str(exc)) from exc
    except LookupError as exc: raise HTTPException(404,str(exc)) from exc
    except ValueError as exc: raise HTTPException(409,str(exc)) from exc
    audit("organization.member.upsert","organization",organization_id,actor=user.email,actor_user_id=user.id,detail={"target_user_id":r["user_id"],"role":r["role"]})
    return r

@app.post("/api/v1/organizations/{organization_id}/members/claim")
def organization_member_claim_accept(organization_id:str,req:OrganizationMemberClaimAccept,user=Depends(current_user)):
    if req.role not in ORG_ROLES: raise HTTPException(422,"Invalid organization role")
    try:
        claim=decode_membership_claim(req.claim_token,organization_id)
        target=get_user_by_id(str(claim["sub"]))
        if not target or int(claim.get("ver",-1)) != int(target.token_version or 0):
            raise ValueError("Membership claim has been revoked")
        r=add_organization_member_by_claim(user.id,organization_id,target.id,req.role)
    except PermissionError as exc: raise HTTPException(403,str(exc)) from exc
    except LookupError as exc: raise HTTPException(404,str(exc)) from exc
    except ValueError as exc: raise HTTPException(409,str(exc)) from exc
    audit("organization.member.claim_accept","organization",organization_id,actor=user.email,actor_user_id=user.id,detail={"target_user_id":r["user_id"],"role":r["role"]})
    return r

@app.delete("/api/v1/organizations/{organization_id}/members/{user_id}")
def organization_member_delete(organization_id:str,user_id:str,user=Depends(current_user)):
    try:ok=remove_organization_member(user.id,organization_id,user_id)
    except PermissionError as exc: raise HTTPException(403,str(exc)) from exc
    except ValueError as exc: raise HTTPException(409,str(exc)) from exc
    if not ok: raise HTTPException(404,"Organization member not found")
    audit("organization.member.delete","organization",organization_id,actor=user.email,actor_user_id=user.id,detail={"target_user_id":user_id})
    return Response(status_code=204)

@app.get("/api/v1/workspaces")
def workspaces(user=Depends(current_user)): return {"items":list_workspaces(user.id)}

@app.post("/api/v1/workspaces")
def workspace_create(req:WorkspaceCreate,user=Depends(current_user)):
    if req.role not in ROLES: raise HTTPException(422,"Invalid role")
    try:r=create_workspace(user.id,req.name,req.role,req.organization_id)
    except PermissionError as exc: raise HTTPException(403,str(exc)) from exc
    audit("workspace.create","workspace",r["id"],actor=user.email,actor_user_id=user.id,workspace_id=r["id"],detail={"organization_id":r["organization_id"]})
    return r

@app.get("/api/v1/workspaces/{workspace_id}")
def workspace_get(workspace_id:str,user=Depends(current_user)):
    r=workspace_access(user.id,workspace_id)
    if not r: raise HTTPException(404,"Workspace not found")
    return r

@app.patch("/api/v1/workspaces/{workspace_id}")
def workspace_patch(workspace_id:str,req:WorkspaceCreate,user=Depends(current_user)):
    if req.role not in ROLES: raise HTTPException(422,"Invalid role")
    r=update_workspace(user.id,workspace_id,req.name,req.role)
    if not r: raise HTTPException(403,"Workspace administration required")
    audit("workspace.update","workspace",workspace_id,actor=user.email,actor_user_id=user.id,workspace_id=workspace_id)
    return r

@app.get("/api/v1/workspaces/{workspace_id}/audit-logs")
def workspace_audit_logs(workspace_id:str,limit:int=Query(100,ge=1,le=500),user=Depends(current_user)):
    rows=list_audit_logs(user.id,workspace_id,limit)
    if rows is None: raise HTTPException(403,"Workspace administration required")
    return {"items":rows}

@app.post("/api/v1/portfolios")
def portfolio_create(req:PortfolioCreate,user=Depends(current_user)):
    w=_workspace(user,req.workspace_id,write=True)
    r=create_portfolio(user.id,w["id"],req.name,{"wallets":req.wallets,"manual_positions":req.manual_positions})
    audit("portfolio.create","portfolio",r["id"],actor=user.email,actor_user_id=user.id,workspace_id=w["id"])
    return r

@app.get("/api/v1/portfolios/{portfolio_id}")
def portfolio_get(portfolio_id:str,user=Depends(current_user)):
    p=portfolio_by_id(user.id,portfolio_id)
    if not p: raise HTTPException(404,"Portfolio not found")
    return p

@app.get("/api/v1/providers")
def providers(user=Depends(current_user)): return {"providers":[p.model_dump(mode="json") for p in provider_metadata()],"fallbacks":FALLBACKS}

@app.get("/api/v1/providers/status")
def provider_status(deep:bool=Query(False),chain:str=Query("ethereum"),user=Depends(current_user)):
    _guard_provider_deep_probe(deep)
    return {"chain":chain,"providers":[a.health(deep=deep,chain=chain).model_dump(mode="json") for a in ADAPTERS.values()]}

@app.get("/api/v1/protocol-adapters")
def protocol_adapters():
    return {"items":protocol_adapter_capabilities(),"execution":"read_only","transaction_signing":False}

@app.get("/api/v1/protocol-deployments")
def protocol_deployments(adapter:str|None=Query(None),chain_id:int|None=Query(None)):
    return {"registry_version":REGISTRY_VERSION,"registry_fingerprint":registry_fingerprint(),"items":list_protocol_deployments(adapter,chain_id),"authority":"versioned snapshots of official protocol-owned deployment sources"}

def _protocol_operational_read(req:AnalysisRequest,user,fn,action:str):
    w=_workspace(user,req.workspace_id,write=True)
    token=set_workspace_id(w["id"])
    try:
        try:
            result=fn(req.input)
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc
        except ProviderError as exc:
            raise HTTPException(503,f"{exc.provider_id}: {exc.code}: {exc}") from exc
        audit(action,"workspace",w["id"],actor=user.email,actor_user_id=user.id,workspace_id=w["id"],detail={"protocol_adapter":req.input.get("protocol_adapter") or req.input.get("protocol_type")})
        return result
    finally:
        reset_workspace_id(token)

@app.post("/api/v1/protocol-history/timeline")
def protocol_history_timeline(req:AnalysisRequest,user=Depends(current_user)):
    return _protocol_operational_read(req,user,protocol_event_timeline,"protocol.history.timeline")

@app.post("/api/v1/protocol-config/compare")
def protocol_config_compare(req:AnalysisRequest,user=Depends(current_user)):
    return _protocol_operational_read(req,user,compare_protocol_configuration,"protocol.config.compare")

@app.post("/api/v1/protocol-config/reviews")
def protocol_config_review_create(req:AnalysisRequest,user=Depends(current_user)):
    w=_workspace(user,req.workspace_id,write=True)
    token=set_workspace_id(w["id"])
    try:
        try: review=compare_protocol_configuration(req.input)
        except ValueError as exc: raise HTTPException(422,str(exc)) from exc
        except ProviderError as exc: raise HTTPException(503,f"{exc.provider_id}: {exc.code}: {exc}") from exc
        row=create_protocol_review(user.id,w["id"],review,"json")
        audit("protocol.config.review.create","report",row["id"],actor=user.email,actor_user_id=user.id,workspace_id=w["id"],detail={"adapter":review.get("adapter"),"from_block":review.get("from_block"),"to_block":review.get("to_block"),"change_count":review.get("change_count")})
        return row
    finally: reset_workspace_id(token)

@app.get("/api/v1/protocol-config/reviews/{report_id}")
def protocol_config_review_get(report_id:str,user=Depends(current_user)):
    row=get_report(user.id,report_id,include_payload=True)
    if not row or row.get("report_type")!="protocol_configuration_review": raise HTTPException(404,"Protocol configuration review not found")
    return row

@app.post("/api/v1/protocol-config/reviews/{report_id}/approve")
def protocol_config_review_approve(report_id:str,user=Depends(current_user)):
    row=approve_protocol_review(user.id,report_id)
    if not row: raise HTTPException(404,"Protocol configuration review not found or manager access required")
    audit("protocol.config.review.approve","report",report_id,actor=user.email,actor_user_id=user.id,workspace_id=row["workspace_id"],detail={"status":"approved"})
    return row

@app.get("/api/v1/protocol-config/reviews/{report_id}/render")
def protocol_config_review_render(report_id:str,format:str=Query("html"),user=Depends(current_user)):
    row=get_report(user.id,report_id,include_payload=True)
    if not row or row.get("report_type")!="protocol_configuration_review": raise HTTPException(404,"Protocol configuration review not found")
    review=row.get("payload") or {}; fmt=format.lower()
    if fmt=="json": return {"report":row,"review":review}
    if fmt=="html": return Response(content=protocol_review_html(review),media_type="text/html",headers={"X-Rivexis-Report-Id":report_id})
    if fmt=="pdf": return Response(content=protocol_review_pdf(review),media_type="application/pdf",headers={"X-Rivexis-Report-Id":report_id,"Content-Disposition":f'inline; filename="rivexis-protocol-review-{report_id}.pdf"'})
    raise HTTPException(422,"Supported render formats are html, pdf and json")


@app.post("/api/v1/protocol-investigations")
def protocol_investigation_create(req:ProtocolInvestigationCreate,user=Depends(current_user)):
    w=_workspace(user,req.workspace_id,write=True);token=set_workspace_id(w["id"])
    try:
        try: timeline=protocol_event_timeline(req.input)
        except ValueError as exc: raise HTTPException(422,str(exc)) from exc
        except ProviderError as exc: raise HTTPException(503,f"{exc.provider_id}: {exc.code}: {exc}") from exc
        row=create_protocol_investigation(user.id,w["id"],req.title,req.input,timeline,req.notes)
        audit("protocol.investigation.create","report",row["id"],actor=user.email,actor_user_id=user.id,workspace_id=w["id"],detail={"title":req.title,"event_count":timeline.get("event_count"),"adapter":timeline.get("adapter")})
        return row
    finally: reset_workspace_id(token)

@app.get("/api/v1/protocol-investigations")
def protocol_investigation_list(workspace_id:str|None=Query(None),user=Depends(current_user)):
    w=_workspace(user,workspace_id,write=False);rows=list_protocol_investigations(user.id,w["id"])
    if rows is None: raise HTTPException(403,"Workspace access required")
    return {"workspace_id":w["id"],"items":rows}

@app.get("/api/v1/protocol-investigations/{case_id}")
def protocol_investigation_get(case_id:str,user=Depends(current_user)):
    row=get_protocol_investigation(user.id,case_id)
    if not row: raise HTTPException(404,"Protocol investigation not found")
    return row

@app.patch("/api/v1/protocol-investigations/{case_id}")
def protocol_investigation_update(case_id:str,req:ProtocolInvestigationUpdate,user=Depends(current_user)):
    try: row=update_protocol_investigation(user.id,case_id,status=req.status,disposition=req.disposition,notes=req.notes)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    if not row: raise HTTPException(404,"Protocol investigation not found or write access required")
    audit("protocol.investigation.update","report",case_id,actor=user.email,actor_user_id=user.id,workspace_id=row["workspace_id"],detail={"status":row["status"],"has_disposition":bool((row.get("payload") or {}).get("disposition"))})
    return row

@app.post("/api/v1/protocol-investigations/{case_id}/reviews/{review_id}")
def protocol_investigation_attach_review(case_id:str,review_id:str,user=Depends(current_user)):
    row=attach_protocol_review_to_investigation(user.id,case_id,review_id)
    if not row: raise HTTPException(404,"Investigation/review not found, cross-workspace reference, or write access required")
    audit("protocol.investigation.review.attach","report",case_id,actor=user.email,actor_user_id=user.id,workspace_id=row["workspace_id"],detail={"review_id":review_id})
    return row

@app.get("/api/v1/protocol-investigations/{case_id}/render")
def protocol_investigation_render(case_id:str,format:str=Query("html"),user=Depends(current_user)):
    row=get_protocol_investigation(user.id,case_id)
    if not row: raise HTTPException(404,"Protocol investigation not found")
    fmt=format.lower()
    if fmt=="json": return row
    if fmt=="html": return Response(content=protocol_investigation_html(row),media_type="text/html",headers={"X-Rivexis-Report-Id":case_id})
    if fmt=="pdf": return Response(content=protocol_investigation_pdf(row),media_type="application/pdf",headers={"X-Rivexis-Report-Id":case_id,"Content-Disposition":f'inline; filename="rivexis-investigation-{case_id}.pdf"'})
    raise HTTPException(422,"Supported render formats are html, pdf and json")

@app.get("/api/v1/providers/resolve/{category}")
def provider_resolve(category:str,deep:bool=Query(False),allow_demo:bool=Query(False),chain:str=Query("ethereum"),user=Depends(current_user)):
    _guard_provider_deep_probe(deep)
    return resolve_provider(category,deep,allow_demo,chain=chain).as_dict()


@app.get("/api/v1/observability/traces/{trace_id}")
def observability_trace(trace_id:str,workspace_id:str|None=Query(None),limit:int=Query(200,ge=1,le=500),user=Depends(current_user)):
    w=_workspace(user,workspace_id,write=False)
    try: result=trace_correlation(user.id,w["id"],trace_id,limit)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    if result is None: raise HTTPException(403,"Workspace access required")
    return result

@app.get("/api/v1/observability/status")
def observability_status(user=Depends(current_user)):
    return telemetry_export_status()

@app.get("/api/v1/providers/runtime")
def provider_runtime(workspace_id:str|None=Query(None),user=Depends(current_user)):
    w=_workspace(user,workspace_id,write=False)
    return provider_runtime_snapshot(w["id"])

@app.get("/api/v1/providers/runtime/requests")
def provider_runtime_requests(workspace_id:str|None=Query(None),limit:int=Query(100,ge=1,le=500),user=Depends(current_user)):
    w=_workspace(user,workspace_id,write=False)
    rows=list_provider_request_events(user.id,w["id"],limit)
    if rows is None: raise HTTPException(403,"Workspace access required")
    return {"workspace_id":w["id"],"items":rows}

@app.get("/api/v1/providers/runtime/usage")
def provider_runtime_usage(workspace_id:str|None=Query(None),hours:int=Query(24,ge=1,le=2160),user=Depends(current_user)):
    w=_workspace(user,workspace_id,write=False)
    summary=provider_usage_summary(user.id,w["id"],hours)
    if summary is None: raise HTTPException(403,"Workspace access required")
    return summary

@app.get("/api/v1/providers/{provider_id}")
def provider(provider_id:str,deep:bool=Query(False),chain:str=Query("ethereum"),user=Depends(current_user)):
    _guard_provider_deep_probe(deep)
    a=ADAPTERS.get(provider_id)
    if not a: raise HTTPException(404,"Provider not found")
    return {"metadata":a.metadata.model_dump(mode="json"),"health":a.health(deep,chain=chain).model_dump(mode="json")}

def run(engine_id:EngineId,req:AnalysisRequest,user,workspace_id:str|None=None):
    w=_workspace(user,workspace_id or req.workspace_id,write=True)
    token=set_workspace_id(w["id"])
    try:
        result=ENGINES[engine_id](req.input,req.demo)
        save_engine_result(result,user.id,w["id"])
        audit("analysis.run","analysis",result.analysis_id,actor=user.email,actor_user_id=user.id,workspace_id=w["id"],detail={"engine":engine_id.value,"demo":req.demo,"status":result.status.value})
        return result
    finally:
        reset_workspace_id(token)

@app.post("/api/v1/analysis/simulations")
def simulation(req:AnalysisRequest,user=Depends(current_user)): return run(EngineId.B1,req,user)
@app.get("/api/v1/analysis/simulations/{analysis_id}")
def simulation_get(analysis_id:str,user=Depends(current_user)): return _analysis_for_user(user,analysis_id)
@app.post("/api/v1/analysis/security")
def security(req:AnalysisRequest,user=Depends(current_user)): return run(EngineId.B2,req,user)
@app.post("/api/v1/analysis/monitoring")
def monitoring(req:AnalysisRequest,user=Depends(current_user)): return run(EngineId.B3,req,user)
@app.get("/api/v1/analysis/security/{analysis_id}")
def security_get(analysis_id:str,user=Depends(current_user)): return _analysis_for_user(user,analysis_id)
@app.post("/api/v1/analysis/entities")
def entities(req:AnalysisRequest,user=Depends(current_user)): return run(EngineId.B4,req,user)
@app.post("/api/v1/analysis/routes")
def routes(req:AnalysisRequest,user=Depends(current_user)): return run(EngineId.B5,req,user)
@app.post("/api/v1/analysis/portfolio")
def portfolio_analysis(req:AnalysisRequest,user=Depends(current_user)): return run(EngineId.F1,req,user)
@app.post("/api/v1/analysis/protocol-risk")
def protocol_risk(req:AnalysisRequest,user=Depends(current_user)): return run(EngineId.F2,req,user)
@app.post("/api/v1/analysis/position-risk")
def position_risk(req:AnalysisRequest,user=Depends(current_user)): return run(EngineId.F3,req,user)
@app.post("/api/v1/analysis/yield")
def yield_analysis(req:AnalysisRequest,user=Depends(current_user)): return run(EngineId.F4,req,user)
@app.post("/api/v1/analysis/treasury")
def treasury(req:AnalysisRequest,user=Depends(current_user)): return run(EngineId.F5,req,user)
@app.post("/api/v1/analysis/{engine_id}")
def analysis_generic(engine_id:EngineId,req:AnalysisRequest,user=Depends(current_user)): return run(engine_id,req,user)

@app.get("/api/v1/analyses/{analysis_id}")
def analysis_get(analysis_id:str,user=Depends(current_user)): return _analysis_for_user(user,analysis_id)
@app.get("/api/v1/analyses/{analysis_id}/evidence")
def evidence(analysis_id:str,user=Depends(current_user)):
    r=_analysis_for_user(user,analysis_id);return {"analysis_id":analysis_id,"evidence":r.get("evidence",[])}
@app.get("/api/v1/analyses/{analysis_id}/sources")
def sources(analysis_id:str,user=Depends(current_user)):
    r=_analysis_for_user(user,analysis_id);return {"analysis_id":analysis_id,"providers":r.get("provider_status",[]),"evidence_providers":sorted({e.get("provider","UNKNOWN") for e in r.get("evidence",[])})}
@app.get("/api/v1/analyses/{analysis_id}/conflicts")
def conflicts(analysis_id:str,user=Depends(current_user)):
    return {"analysis_id":analysis_id,"conflicts":_analysis_for_user(user,analysis_id).get("provider_conflicts",[])}

@app.post("/api/v1/decisions/analyze")
def decision(req:DecisionRequest,user=Depends(current_user)):
    if not req.engine_results: raise HTTPException(422,"At least one persisted engine result is required")
    workspace_ids=set()
    for item in req.engine_results:
        rec=analysis_record(item.analysis_id)
        if not rec or not rec["workspace_id"] or not workspace_access(user.id,rec["workspace_id"]): raise HTTPException(404,"One or more analysis results are unavailable")
        workspace_ids.add(rec["workspace_id"])
    if len(workspace_ids)!=1: raise HTTPException(409,"A decision cannot combine analyses from different workspaces")
    workspace_id=next(iter(workspace_ids))
    if not workspace_access(user.id,workspace_id,write=True): raise HTTPException(403,"Workspace write access required")
    r=analyze_decision(req);save_decision(r,user.id,workspace_id)
    audit("decision.analyze","decision",r.decision_id,actor=user.email,actor_user_id=user.id,workspace_id=workspace_id,detail={"analysis_ids":[x.analysis_id for x in req.engine_results],"decision":r.decision.value})
    return r

@app.get("/api/v1/decisions/{decision_id}")
def decision_get(decision_id:str,user=Depends(current_user)): return _decision_for_user(user,decision_id)
@app.get("/api/v1/decisions/{decision_id}/explanation")
def decision_explanation(decision_id:str,user=Depends(current_user)):
    return grounded_explanation(RivexisDecision.model_validate(_decision_for_user(user,decision_id)))

@app.get("/api/v1/history")
def history_endpoint(limit:int=Query(50,ge=1,le=200),workspace_id:str|None=Query(None),user=Depends(current_user)):
    if workspace_id and not workspace_access(user.id,workspace_id): raise HTTPException(404,"Workspace not found")
    return {"items":history(user.id,limit,workspace_id)}

@app.post("/api/v1/monitors")
def monitor_create(req:MonitorCreate,user=Depends(current_user)):
    w=_workspace(user,req.workspace_id,write=True)
    r=create_monitor(user.id,w["id"],req.entity,req.chain,req.rules,req.config)
    audit("monitor.create","monitor",r["id"],actor=user.email,actor_user_id=user.id,workspace_id=w["id"])
    return r

@app.get("/api/v1/monitors")
def monitor_list(workspace_id:str|None=Query(None),user=Depends(current_user)):
    if workspace_id and not workspace_access(user.id,workspace_id): raise HTTPException(404,"Workspace not found")
    return {"items":list_monitors(user.id,workspace_id)}

@app.get("/api/v1/monitors/{monitor_id}")
def monitor_get(monitor_id:str,user=Depends(current_user)):
    r=get_monitor(user.id,monitor_id)
    if not r: raise HTTPException(404,"Monitor not found")
    return r

@app.post("/api/v1/monitors/{monitor_id}/check")
def monitor_check(monitor_id:str,user=Depends(current_user)):
    monitor=get_monitor(user.id,monitor_id,write=True)
    if not monitor: raise HTTPException(404,"Monitor not found")
    payload={"entity":monitor["entity"],"chain":monitor["chain"],**monitor.get("config",{})}
    if monitor.get("last_snapshot") is not None: payload["previous_snapshot"]=monitor["last_snapshot"]
    result=run(EngineId.B3,AnalysisRequest(input=payload,demo=False,workspace_id=monitor["workspace_id"]),user,monitor["workspace_id"])
    snapshot=result.metrics.get("snapshot") if isinstance(result.metrics,dict) else None
    update_monitor(user.id,monitor_id,last_snapshot=snapshot if isinstance(snapshot,dict) else None,last_analysis_id=result.analysis_id,last_status=result.status.value)
    if result.signals or result.hard_blockers or result.severity.value in {"moderate","high","critical"}:
        create_alert(monitor["workspace_id"],monitor_id,result.analysis_id,result.severity.value,{"signals":result.signals,"hard_blockers":result.hard_blockers,"warnings":result.warnings})
    audit("monitor.check","monitor",monitor_id,actor=user.email,actor_user_id=user.id,workspace_id=monitor["workspace_id"],detail={"analysis_id":result.analysis_id,"status":result.status.value})
    return result

@app.patch("/api/v1/monitors/{monitor_id}")
def monitor_patch(monitor_id:str,req:MonitorCreate,user=Depends(current_user)):
    r=update_monitor(user.id,monitor_id,entity=req.entity,chain=req.chain,rules=req.rules,config=req.config)
    if not r: raise HTTPException(404,"Monitor not found")
    audit("monitor.update","monitor",monitor_id,actor=user.email,actor_user_id=user.id,workspace_id=r["workspace_id"])
    return r

@app.delete("/api/v1/monitors/{monitor_id}")
def monitor_delete(monitor_id:str,user=Depends(current_user)):
    r=get_monitor(user.id,monitor_id,write=True)
    if not r: raise HTTPException(404,"Monitor not found")
    if not delete_monitor(user.id,monitor_id): raise HTTPException(404,"Monitor not found")
    audit("monitor.delete","monitor",monitor_id,actor=user.email,actor_user_id=user.id,workspace_id=r["workspace_id"])
    return Response(status_code=204)

@app.post("/api/v1/reports")
def report(req:ReportRequest,user=Depends(current_user)):
    raw=_decision_for_user(user,req.decision_id)
    rec=None
    from rivexis_api.services.store import decision_record
    rec=decision_record(req.decision_id)
    if not rec or not rec["workspace_id"] or not workspace_access(user.id,rec["workspace_id"]): raise HTTPException(404,"Decision not found")
    d=RivexisDecision.model_validate(raw)
    fmt=req.format.lower()
    if fmt not in {"json","pdf","html"}: raise HTTPException(422,"MVP supports html, pdf and json")
    report_row=create_report(user.id,rec["workspace_id"],req.decision_id,fmt);rid=report_row["id"]
    audit("report.generate","report",rid,actor=user.email,actor_user_id=user.id,workspace_id=rec["workspace_id"],detail={"decision_id":req.decision_id,"format":fmt})
    if fmt=="json": return {"report_id":rid,"report":d}
    if fmt=="pdf": return Response(content=decision_pdf(d),media_type="application/pdf",headers={"X-Rivexis-Report-Id":rid,"Content-Disposition":f'inline; filename="rivexis-{rid}.pdf"'})
    return Response(content=decision_html(d),media_type="text/html",headers={"X-Rivexis-Report-Id":rid})

@app.get("/api/v1/reports/{report_id}")
def report_get(report_id:str,user=Depends(current_user)):
    r=get_report(user.id,report_id)
    if not r: raise HTTPException(404,"Report not found")
    return r

@app.get("/api/v1/saved-analyses")
def saved_analyses(user=Depends(current_user),include_archived:bool=Query(False),workspace_id:str|None=Query(None)):
    if workspace_id and not workspace_access(user.id,workspace_id): raise HTTPException(404,"Workspace not found")
    return {"items":list_saved_analyses(user.id,include_archived,workspace_id)}

@app.post("/api/v1/saved-analyses")
def saved_analysis_create(req:SavedAnalysisCreate,user=Depends(current_user)):
    rec=analysis_record(req.analysis_id)
    if not rec or not rec["workspace_id"] or not workspace_access(user.id,rec["workspace_id"]): raise HTTPException(404,"Analysis not found")
    r=create_saved_analysis(user.id,rec["workspace_id"],req.analysis_id,req.title)
    audit("analysis.save","saved_analysis",r["id"],actor=user.email,actor_user_id=user.id,workspace_id=rec["workspace_id"],detail={"analysis_id":req.analysis_id})
    return r

@app.patch("/api/v1/saved-analyses/{saved_id}")
def saved_analysis_archive(saved_id:str,archived:bool=Query(True),user=Depends(current_user)):
    r=set_saved_analysis_archived(user.id,saved_id,archived)
    if not r: raise HTTPException(404,"Saved analysis not found")
    return r

@app.delete("/api/v1/saved-analyses/{saved_id}")
def saved_analysis_delete(saved_id:str,user=Depends(current_user)):
    if not delete_saved_analysis(user.id,saved_id): raise HTTPException(404,"Saved analysis not found")
    return Response(status_code=204)

@app.get("/api/v1/monitors/{monitor_id}/hypernative-webhook-credential")
def hypernative_webhook_credential(monitor_id:str,user=Depends(current_user)):
    monitor=get_monitor(user.id,monitor_id)
    if not monitor: raise HTTPException(404,"Monitor not found")
    if not workspace_access(user.id,monitor["workspace_id"],manage=True):
        raise HTTPException(403,"Workspace administration required")
    root=os.getenv("HYPERNATIVE_WEBHOOK_SECRET","").strip()
    if not root:
        raise HTTPException(503,"Hypernative webhook ingress is not configured")
    if _production() and len(root)<32:
        raise HTTPException(503,"Hypernative webhook ingress secret is too weak for production")
    return {
        "workspace_id":monitor["workspace_id"],"monitor_id":monitor_id,
        "header":"X-Rivexis-Webhook-Secret",
        "credential":_hypernative_monitor_credential(root,monitor["workspace_id"],monitor_id),
        "authentication":"rivexis_monitor_derived_secret_v1",
    }

@app.post("/api/v1/integrations/hypernative/events", status_code=202)
def hypernative_event(req:HypernativeEvent,request:Request):
    """Rivexis-owned push boundary for customer-configured Hypernative webhook forwarding.

    This validates a Rivexis shared ingress secret. It does not claim to validate a
    Hypernative-native signature scheme, because that contract is customer/configuration specific.
    """
    root_secret=os.getenv("HYPERNATIVE_WEBHOOK_SECRET","").strip()
    if not root_secret:
        raise HTTPException(503,"Hypernative webhook ingress is not configured")
    if _production() and len(root_secret)<32:
        raise HTTPException(503,"Hypernative webhook ingress secret is too weak for production")
    monitor=get_monitor_internal(req.monitor_id)
    if not monitor or monitor["workspace_id"]!=req.workspace_id:
        raise HTTPException(404,"Monitor not found")
    expected=_hypernative_monitor_credential(root_secret,req.workspace_id,req.monitor_id)
    supplied=request.headers.get("X-Rivexis-Webhook-Secret","")
    # Legacy root-secret acceptance is development-only so old local integrations/tests remain usable.
    legacy_ok=not _production() and bool(supplied) and hmac.compare_digest(supplied,root_secret)
    if not supplied or (not hmac.compare_digest(supplied,expected) and not legacy_ok):
        raise HTTPException(401,"Invalid integration secret")
    auth_mode="rivexis_shared_secret" if legacy_ok else "rivexis_monitor_derived_secret_v1"
    try:
        serialized=json.dumps(req.provider_payload,separators=(",",":"),ensure_ascii=False)
    except (TypeError,ValueError) as exc:
        raise HTTPException(422,"provider_payload must be JSON serializable") from exc
    if len(serialized.encode("utf-8"))>65536:
        raise HTTPException(413,"provider_payload exceeds 64 KiB")
    severity=req.severity.strip().lower()
    canonical_severity=severity if severity in {"low","moderate","high","critical","unknown"} else "unknown"
    source_event_id=None
    for key in ("source_event_id","event_id","id"):
        value=req.provider_payload.get(key)
        if isinstance(value,(str,int)) and str(value).strip():
            source_event_id=str(value).strip()[:200]
            break
    canonical_event=json.dumps({
        "workspace_id":req.workspace_id,"monitor_id":req.monitor_id,"event_type":req.event_type,
        "severity":canonical_severity,"affected_entity":req.affected_entity,"confidence":req.confidence,
        "observed_at":req.observed_at,"provider_payload":req.provider_payload,
    },sort_keys=True,separators=(",",":"),ensure_ascii=False)
    event_key=source_event_id or hashlib.sha256(canonical_event.encode("utf-8")).hexdigest()
    payload={
        "provider":"hypernative",
        "event_type":req.event_type,
        "affected_entity":req.affected_entity,
        "confidence":req.confidence,
        "observed_at":req.observed_at,
        "provider_severity":req.severity,
        "provider_event_id":source_event_id,
        "provider_payload":req.provider_payload,
        "ingress_authentication":auth_mode,
    }
    alert=create_alert(
        req.workspace_id,req.monitor_id,None,canonical_severity,payload,
        provider_id="hypernative",external_event_key=event_key,
    )
    audit(
        "integration.hypernative.event.duplicate" if alert.get("duplicate") else "integration.hypernative.event",
        "alert",alert["id"],actor="hypernative-forwarder",
        workspace_id=req.workspace_id,detail={"monitor_id":req.monitor_id,"event_type":req.event_type,"severity":canonical_severity,"duplicate":bool(alert.get("duplicate"))},
    )
    return {
        "accepted":True,
        "duplicate":bool(alert.get("duplicate")),
        "alert_id":alert["id"],
        "workspace_id":req.workspace_id,
        "monitor_id":req.monitor_id,
        "authentication":auth_mode,
        "provider_native_signature_verified":False,
    }

@app.get("/api/v1/alerts")
def alerts(workspace_id:str|None=Query(None),user=Depends(current_user)):
    if workspace_id and not workspace_access(user.id,workspace_id): raise HTTPException(404,"Workspace not found")
    return {"items":list_alerts(user.id,workspace_id),"status":"manual_monitor_alert_persistence_enabled; continuous_threat_stream_not_configured"}

@app.patch("/api/v1/alerts/{alert_id}")
def alert_patch(alert_id:str,status:str=Query(...),user=Depends(current_user)):
    try:r=update_alert_status(user.id,alert_id,status)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    if not r: raise HTTPException(404,"Alert not found")
    audit("alert.status","alert",alert_id,actor=user.email,actor_user_id=user.id,workspace_id=r["workspace_id"],detail={"status":status})
    return r

@app.post("/api/v1/alerts/process-due")
def alerts_process_due(workspace_id:str=Query(...),limit:int=Query(50,ge=1,le=200),user=Depends(current_user)):
    if not workspace_access(user.id,workspace_id,manage=True): raise HTTPException(403,"Workspace management access required")
    result=process_due_alerts(workspace_id,limit)
    audit("alert.delivery.process","workspace",workspace_id,actor=user.email,actor_user_id=user.id,workspace_id=workspace_id,detail={"processed":result.get("processed",0),"skipped":result.get("skipped",0),"reason":result.get("reason")})
    return result

@app.post("/api/v1/alerts/{alert_id}/requeue")
def alert_requeue(alert_id:str,user=Depends(current_user)):
    r=requeue_alert(user.id,alert_id)
    if not r: raise HTTPException(404,"Alert not found or management access required")
    audit("alert.delivery.requeue","alert",alert_id,actor=user.email,actor_user_id=user.id,workspace_id=r["workspace_id"])
    return r

@app.get("/api/v1/alerts/delivery-metrics")
def alerts_delivery_metrics(workspace_id:str=Query(...),slo_seconds:int=Query(300,ge=1,le=86400),user=Depends(current_user)):
    r=alert_delivery_metrics(user.id,workspace_id,slo_seconds)
    if r is None: raise HTTPException(404,"Workspace not found")
    return r
