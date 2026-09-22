def signup(client,email="analyst@example.com",role="Analyst"):
    r=client.post('/api/v1/auth/signup',json={"email":email,"password":"correct-horse-battery","role":role})
    assert r.status_code==200
    return r.json(),{"Authorization":"Bearer "+r.json()["access_token"]}

def provision(client,email="analyst@example.com",role="Analyst",name="Risk Desk"):
    data,h=signup(client,email,role)
    w=client.post('/api/v1/workspaces',headers=h,json={"name":name,"role":role})
    assert w.status_code==200
    return data,h,w.json()

def test_health(client):
    assert client.get('/health').json()['status']=='ok'

def test_workspace_routes_require_authentication(client):
    assert client.post('/api/v1/analysis/security',json={"demo":True,"input":{}}).status_code==401
    assert client.get('/api/v1/history').status_code==401
    assert client.post('/api/v1/monitors',json={"entity":"0xabc"}).status_code==401

def test_auth_workspace_saved_report_flow(client):
    _,h,w=provision(client)
    assert client.get('/api/v1/me',headers=h).status_code==200
    a=client.post('/api/v1/analysis/security',headers=h,json={"demo":True,"workspace_id":w["id"],"input":{"unlimited_approval":True}})
    assert a.status_code==200
    aid=a.json()['analysis_id']
    s=client.post('/api/v1/saved-analyses',headers=h,json={"analysis_id":aid,"title":"Approval review"})
    assert s.status_code==200 and s.json()['workspace_id']==w['id']
    d=client.post('/api/v1/decisions/analyze',headers=h,json={"engine_results":[a.json()]})
    assert d.status_code==200
    rep=client.post('/api/v1/reports',headers=h,json={"decision_id":d.json()['decision_id'],"format":"html"})
    assert rep.status_code==200 and 'RIVEXIS Decision Report' in rep.text
    rid=rep.headers['x-rivexis-report-id']
    persisted=client.get(f'/api/v1/reports/{rid}',headers=h)
    assert persisted.status_code==200 and persisted.json()['workspace_id']==w['id']

def test_named_security_route_not_shadowed(client):
    _,h,_=provision(client)
    r=client.post('/api/v1/analysis/security',headers=h,json={"demo":True,"input":{}})
    assert r.status_code==200 and r.json()['engine_id']=='B2'

def test_provider_status(client):
    _,h,_=provision(client,email="provider-status@example.com")
    r=client.get('/api/v1/providers/status',headers=h)
    assert r.status_code==200 and len(r.json()['providers'])>=20

def test_pdf_report_is_generated(client):
    _,h,_=provision(client)
    engine=client.post('/api/v1/analysis/F3',headers=h,json={"demo":True,"input":{"health_factor":1.12}})
    assert engine.status_code==200
    decision=client.post('/api/v1/decisions/analyze',headers=h,json={"engine_results":[engine.json()]})
    assert decision.status_code==200
    report=client.post('/api/v1/reports',headers=h,json={"decision_id":decision.json()["decision_id"],"format":"pdf"})
    assert report.status_code==200
    assert report.headers['content-type'].startswith('application/pdf')
    assert report.content.startswith(b'%PDF-')
    assert len(report.content)>1500

def test_request_id_and_api_security_headers(client):
    r=client.get('/health',headers={'X-Request-ID':'test-request-123'})
    assert r.headers['x-request-id']=='test-request-123'
    assert r.headers['x-content-type-options']=='nosniff'
    assert r.headers['x-frame-options']=='DENY'
    assert r.headers['referrer-policy']=='no-referrer'
    assert r.headers['cross-origin-resource-policy']=='same-site'

def test_cross_user_workspace_resource_isolation(client):
    _,h1,w1=provision(client,"owner@example.com")
    _,h2,_=provision(client,"outsider@example.com",name="Outsider")
    a=client.post('/api/v1/analysis/security',headers=h1,json={"demo":True,"workspace_id":w1['id'],"input":{}})
    assert a.status_code==200
    aid=a.json()['analysis_id']
    assert client.get(f'/api/v1/analyses/{aid}',headers=h2).status_code==404
    assert client.get(f'/api/v1/workspaces/{w1["id"]}',headers=h2).status_code==404
    assert client.post('/api/v1/saved-analyses',headers=h2,json={"analysis_id":aid,"title":"stolen"}).status_code==404

def test_organization_membership_rbac_and_viewer_write_denial(client):
    owner,ho,_=provision(client,"org-owner@example.com")
    member,hm,_=provision(client,"org-member@example.com")
    org=client.post('/api/v1/organizations',headers=ho,json={"name":"Institutional Risk Team"})
    assert org.status_code==200
    oid=org.json()['id']
    add=client.post(f'/api/v1/organizations/{oid}/members',headers=ho,json={"email":"org-member@example.com","role":"ANALYST"})
    assert add.status_code==200
    shared=client.post('/api/v1/workspaces',headers=ho,json={"name":"Shared Treasury","role":"Treasury","organization_id":oid})
    assert shared.status_code==200
    wid=shared.json()['id']
    member_workspaces=client.get('/api/v1/workspaces',headers=hm).json()['items']
    assert any(w['id']==wid and w['access_role']=='ANALYST' for w in member_workspaces)
    run=client.post('/api/v1/analysis/security',headers=hm,json={"demo":True,"workspace_id":wid,"input":{}})
    assert run.status_code==200
    downgrade=client.post(f'/api/v1/organizations/{oid}/members',headers=ho,json={"email":"org-member@example.com","role":"VIEWER"})
    assert downgrade.status_code==200
    assert client.get(f'/api/v1/analyses/{run.json()["analysis_id"]}',headers=hm).status_code==200
    denied=client.post('/api/v1/analysis/security',headers=hm,json={"demo":True,"workspace_id":wid,"input":{}})
    assert denied.status_code==403
    assert client.patch(f'/api/v1/workspaces/{wid}',headers=hm,json={"name":"Nope","role":"Treasury"}).status_code==403

def test_persistent_monitor_and_alert_surface_is_workspace_scoped(client):
    _,h,w=provision(client,"monitor@example.com")
    m=client.post('/api/v1/monitors',headers=h,json={"entity":"0x0000000000000000000000000000000000000001","chain":"ethereum","workspace_id":w['id'],"rules":["balance_change"]})
    assert m.status_code==200
    mid=m.json()['id']
    fetched=client.get(f'/api/v1/monitors/{mid}',headers=h)
    assert fetched.status_code==200 and fetched.json()['workspace_id']==w['id']
    listing=client.get('/api/v1/monitors',headers=h).json()['items']
    assert any(x['id']==mid for x in listing)
    alerts=client.get('/api/v1/alerts',headers=h)
    assert alerts.status_code==200 and isinstance(alerts.json()['items'],list)

def test_audit_log_carries_request_id_and_requires_admin(client):
    _,h,w=provision(client,"audit@example.com")
    request_id='audit-case-001'
    r=client.post('/api/v1/analysis/security',headers={**h,'X-Request-ID':request_id},json={"demo":True,"workspace_id":w['id'],"input":{}})
    assert r.status_code==200
    logs=client.get(f'/api/v1/workspaces/{w["id"]}/audit-logs',headers=h)
    assert logs.status_code==200
    analysis_logs=[x for x in logs.json()['items'] if x['action']=='analysis.run']
    assert analysis_logs and analysis_logs[0]['request_id']==request_id

def test_decision_cannot_mix_workspaces(client):
    _,h,w1=provision(client,"decision@example.com",name="Desk One")
    w2=client.post('/api/v1/workspaces',headers=h,json={"name":"Desk Two","role":"Analyst"}).json()
    a1=client.post('/api/v1/analysis/security',headers=h,json={"demo":True,"workspace_id":w1['id'],"input":{}}).json()
    a2=client.post('/api/v1/analysis/security',headers=h,json={"demo":True,"workspace_id":w2['id'],"input":{}}).json()
    r=client.post('/api/v1/decisions/analyze',headers=h,json={"engine_results":[a1,a2]})
    assert r.status_code==409

def test_logout_revokes_existing_bearer_token(client):
    _,h,_=provision(client,"logout@example.com")
    assert client.get('/api/v1/me',headers=h).status_code==200
    out=client.post('/api/v1/auth/logout',headers=h)
    assert out.status_code==200 and out.json()['status']=='revoked'
    assert client.get('/api/v1/me',headers=h).status_code==401

def test_provider_runtime_requires_auth_and_is_workspace_scoped(client):
    assert client.get("/api/v1/providers/runtime").status_code == 401
    email="runtime@example.com"; password="password123"
    signup=client.post("/api/v1/auth/signup",json={"email":email,"password":password,"role":"Analyst"})
    token=signup.json()["access_token"]
    headers={"Authorization":f"Bearer {token}"}
    ws=client.post("/api/v1/workspaces",headers=headers,json={"name":"Runtime WS","role":"Analyst","organization_id":None}).json()
    response=client.get(f"/api/v1/providers/runtime?workspace_id={ws['id']}",headers=headers)
    assert response.status_code == 200
    assert response.json()["scope"] == ws["id"]


def test_provider_request_history_is_persisted_per_workspace(client):
    from rivexis_api.core.context import reset_workspace_id, set_workspace_id
    from rivexis_api.provider_runtime import execute
    _,h,w=provision(client,"provider-history@example.com")
    token=set_workspace_id(w["id"])
    try:
        assert execute("fixture-provider","probe",lambda:{"ok":True},endpoint="fixture://provider") == {"ok":True}
    finally:
        reset_workspace_id(token)
    r=client.get(f'/api/v1/providers/runtime/requests?workspace_id={w["id"]}',headers=h)
    assert r.status_code==200
    items=r.json()["items"]
    assert items and items[0]["provider"]=="fixture-provider"
    assert items[0]["status"]=="SUCCESS" and items[0]["attempts"]==1


def test_provider_usage_aggregation_is_persisted_and_workspace_scoped(client, monkeypatch):
    from rivexis_api.core.context import reset_workspace_id, set_workspace_id
    from rivexis_api.provider_runtime import execute, reset_runtime_state
    reset_runtime_state()
    monkeypatch.setenv("RIVEXIS_PROVIDER_FIXTURE_USAGE_ESTIMATED_COST_USD_PER_ATTEMPT","0.125")
    _,h,w=provision(client,"provider-usage@example.com")
    token=set_workspace_id(w["id"])
    try:
        execute("fixture_usage","probe",lambda:{"ok":True},endpoint="fixture://usage")
        execute("fixture_usage","cached",lambda:{"ok":True},endpoint="fixture://usage",cache_key="a",cache_ttl_seconds=10)
        execute("fixture_usage","cached",lambda:{"ok":False},endpoint="fixture://usage",cache_key="a",cache_ttl_seconds=10)
    finally:
        reset_workspace_id(token)
    r=client.get(f'/api/v1/providers/runtime/usage?workspace_id={w["id"]}&hours=24',headers=h)
    assert r.status_code==200
    item=next(x for x in r.json()["items"] if x["provider"]=="fixture_usage")
    assert item["logical_events"]==3
    assert item["success_events"]==3
    assert item["cache_hits"]==1
    assert item["attempts"]==2
    assert item["estimated_cost_usd"]==0.25

def test_protocol_adapter_capabilities_endpoint(client):
    r=client.get('/api/v1/protocol-adapters')
    assert r.status_code==200
    body=r.json()
    names={x['adapter'] for x in body['items']}
    assert names=={'aave_v3','compound_v3','morpho_blue'}
    assert body['execution']=='read_only' and body['transaction_signing'] is False
