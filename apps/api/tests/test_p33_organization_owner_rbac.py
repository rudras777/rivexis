from test_api import provision


def _create_org(client, headers, name="Owner Boundary"):
    response = client.post('/api/v1/organizations', headers=headers, json={"name": name})
    assert response.status_code == 200
    return response.json()["id"]


def _add(client, org_id, headers, email, role):
    return client.post(f'/api/v1/organizations/{org_id}/members', headers=headers, json={"email": email, "role": role})


def test_admin_cannot_promote_to_owner(client):
    _, ho, _ = provision(client, "p33-owner@example.com")
    _, ha, _ = provision(client, "p33-admin@example.com")
    _, hm, _ = provision(client, "p33-member@example.com")
    oid = _create_org(client, ho)
    assert _add(client, oid, ho, "p33-admin@example.com", "ADMIN").status_code == 200
    assert _add(client, oid, ho, "p33-member@example.com", "ANALYST").status_code == 200
    assert _add(client, oid, ha, "p33-admin@example.com", "OWNER").status_code == 403
    assert _add(client, oid, ha, "p33-member@example.com", "OWNER").status_code == 403


def test_admin_cannot_modify_or_remove_owner(client):
    _, ho, _ = provision(client, "p33-owner2@example.com")
    _, ha, _ = provision(client, "p33-admin2@example.com")
    _, hx, _ = provision(client, "p33-owner3@example.com")
    oid = _create_org(client, ho, "Owner Protection")
    assert _add(client, oid, ho, "p33-admin2@example.com", "ADMIN").status_code == 200
    assert _add(client, oid, ho, "p33-owner3@example.com", "OWNER").status_code == 200
    assert _add(client, oid, ha, "p33-owner3@example.com", "VIEWER").status_code == 403
    members = client.get(f'/api/v1/organizations/{oid}/members', headers=ho).json()["items"]
    owner3_id = next(x["user_id"] for x in members if x["email"] == "p33-owner3@example.com")
    assert client.delete(f'/api/v1/organizations/{oid}/members/{owner3_id}', headers=ha).status_code == 403


def test_owner_transfer_is_allowed_when_another_owner_remains(client):
    _, ho, _ = provision(client, "p33-owner4@example.com")
    _, hx, _ = provision(client, "p33-owner5@example.com")
    oid = _create_org(client, ho, "Owner Transfer")
    assert _add(client, oid, ho, "p33-owner5@example.com", "OWNER").status_code == 200
    assert _add(client, oid, ho, "p33-owner5@example.com", "ADMIN").status_code == 200
    assert _add(client, oid, ho, "p33-owner5@example.com", "OWNER").status_code == 200
    members = client.get(f'/api/v1/organizations/{oid}/members', headers=ho).json()["items"]
    owner5_id = next(x["user_id"] for x in members if x["email"] == "p33-owner5@example.com")
    assert client.delete(f'/api/v1/organizations/{oid}/members/{owner5_id}', headers=ho).status_code == 204


def test_last_owner_cannot_be_demoted_or_removed(client):
    owner, ho, _ = provision(client, "p33-last-owner@example.com")
    oid = _create_org(client, ho, "Last Owner")
    assert _add(client, oid, ho, "p33-last-owner@example.com", "ADMIN").status_code == 409
    assert client.delete(f'/api/v1/organizations/{oid}/members/{owner["user"]["id"]}', headers=ho).status_code == 409
    members = client.get(f'/api/v1/organizations/{oid}/members', headers=ho).json()["items"]
    assert len(members) == 1 and members[0]["role"] == "OWNER"
