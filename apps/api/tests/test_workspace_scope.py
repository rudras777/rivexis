def signup(client,email,role="Analyst"):
    response=client.post('/api/v1/auth/signup',json={"email":email,"password":"correct-horse-battery","role":role})
    assert response.status_code==200
    return {"Authorization":"Bearer "+response.json()["access_token"]}


def provision(client,email,name):
    headers=signup(client,email)
    workspace=client.post('/api/v1/workspaces',headers=headers,json={"name":name,"role":"Analyst"})
    assert workspace.status_code==200
    return headers,workspace.json()


def test_workspace_scoped_collection_reads_fail_closed_for_foreign_workspace(client):
    owner_headers,owner_workspace=provision(client,"workspace-owner@example.com","Owner Desk")
    outsider_headers,_=provision(client,"workspace-outsider@example.com","Outsider Desk")
    workspace_id=owner_workspace["id"]

    assert client.get(f'/api/v1/history?workspace_id={workspace_id}',headers=owner_headers).status_code==200
    assert client.get(f'/api/v1/saved-analyses?workspace_id={workspace_id}',headers=owner_headers).status_code==200
    assert client.get(f'/api/v1/monitors?workspace_id={workspace_id}',headers=owner_headers).status_code==200
    assert client.get(f'/api/v1/providers/runtime?workspace_id={workspace_id}',headers=owner_headers).status_code==200

    assert client.get(f'/api/v1/history?workspace_id={workspace_id}',headers=outsider_headers).status_code==404
    assert client.get(f'/api/v1/saved-analyses?workspace_id={workspace_id}',headers=outsider_headers).status_code==404
    assert client.get(f'/api/v1/monitors?workspace_id={workspace_id}',headers=outsider_headers).status_code==404
    assert client.get(f'/api/v1/providers/runtime?workspace_id={workspace_id}',headers=outsider_headers).status_code==403


def test_workspace_management_and_audit_logs_require_workspace_administration(client):
    owner_headers,owner_workspace=provision(client,"workspace-admin@example.com","Admin Desk")
    outsider_headers,_=provision(client,"workspace-nonadmin@example.com","Other Desk")
    workspace_id=owner_workspace["id"]

    updated=client.patch(
        f'/api/v1/workspaces/{workspace_id}',
        headers=owner_headers,
        json={"name":"Renamed Admin Desk","role":"Fund"},
    )
    assert updated.status_code==200
    assert updated.json()["name"]=="Renamed Admin Desk"
    assert updated.json()["role"]=="Fund"

    logs=client.get(f'/api/v1/workspaces/{workspace_id}/audit-logs?limit=20',headers=owner_headers)
    assert logs.status_code==200
    assert any(row["action"]=="workspace.update" for row in logs.json()["items"])

    denied_update=client.patch(
        f'/api/v1/workspaces/{workspace_id}',
        headers=outsider_headers,
        json={"name":"Unauthorized Rename","role":"Treasury"},
    )
    assert denied_update.status_code==403
    assert client.get(f'/api/v1/workspaces/{workspace_id}/audit-logs',headers=outsider_headers).status_code==403
