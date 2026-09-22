from pathlib import Path

from test_api import provision


def _create_org(client, headers, name="P34 Org"):
    r = client.post('/api/v1/organizations', headers=headers, json={"name": name})
    assert r.status_code == 200
    return r.json()["id"]


def _set_member(client, org_id, headers, email, role):
    return client.post(
        f'/api/v1/organizations/{org_id}/members',
        headers=headers,
        json={"email": email, "role": role},
    )


def test_org_workspace_creator_never_gets_owner_override(client):
    _, owner_h, _ = provision(client, "p34-owner@example.com")
    _, analyst_h, _ = provision(client, "p34-analyst@example.com")
    oid = _create_org(client, owner_h)
    assert _set_member(client, oid, owner_h, "p34-analyst@example.com", "ANALYST").status_code == 200

    created = client.post(
        '/api/v1/workspaces',
        headers=analyst_h,
        json={"name": "Analyst-created org workspace", "role": "Analyst", "organization_id": oid},
    )
    assert created.status_code == 200
    workspace = created.json()
    assert workspace["access_role"] == "ANALYST"

    # Creator lineage is not management authority for an organization workspace.
    denied = client.patch(
        f'/api/v1/workspaces/{workspace["id"]}',
        headers=analyst_h,
        json={"name": "Escalated", "role": "Analyst"},
    )
    assert denied.status_code == 403

    # The organization owner can manage a workspace they did not create.
    managed = client.patch(
        f'/api/v1/workspaces/{workspace["id"]}',
        headers=owner_h,
        json={"name": "Owner managed", "role": "Analyst"},
    )
    assert managed.status_code == 200
    assert managed.json()["access_role"] == "OWNER"


def test_org_downgrade_and_removal_revoke_creator_permissions_and_data(client):
    owner, owner_h, _ = provision(client, "p34-owner2@example.com")
    analyst, analyst_h, _ = provision(client, "p34-analyst2@example.com")
    oid = _create_org(client, owner_h, "P34 Revocation Org")
    assert _set_member(client, oid, owner_h, "p34-analyst2@example.com", "ANALYST").status_code == 200

    created = client.post(
        '/api/v1/workspaces',
        headers=analyst_h,
        json={"name": "Creator Revocation", "role": "Analyst", "organization_id": oid},
    )
    assert created.status_code == 200
    wid = created.json()["id"]

    analysis = client.post(
        '/api/v1/analysis/security',
        headers=analyst_h,
        json={"demo": True, "workspace_id": wid, "input": {"unlimited_approval": True}},
    )
    assert analysis.status_code == 200
    aid = analysis.json()["analysis_id"]

    # Downgrade preserves read visibility but revokes write permission, even for creator.
    assert _set_member(client, oid, owner_h, "p34-analyst2@example.com", "VIEWER").status_code == 200
    visible = client.get(f'/api/v1/workspaces/{wid}', headers=analyst_h)
    assert visible.status_code == 200
    assert visible.json()["access_role"] == "VIEWER"
    assert client.get(f'/api/v1/analyses/{aid}', headers=analyst_h).status_code == 200
    assert client.post(
        '/api/v1/analysis/security',
        headers=analyst_h,
        json={"demo": True, "workspace_id": wid, "input": {}},
    ).status_code == 403

    members = client.get(f'/api/v1/organizations/{oid}/members', headers=owner_h).json()["items"]
    analyst_id = next(x["user_id"] for x in members if x["email"] == "p34-analyst2@example.com")
    assert analyst_id == analyst["user"]["id"]
    assert client.delete(f'/api/v1/organizations/{oid}/members/{analyst_id}', headers=owner_h).status_code == 204

    # Removal must revoke both the workspace and every downstream workspace-scoped object.
    assert client.get(f'/api/v1/workspaces/{wid}', headers=analyst_h).status_code == 404
    listed = client.get('/api/v1/workspaces', headers=analyst_h).json()["items"]
    assert all(x["id"] != wid for x in listed)
    assert client.get(f'/api/v1/analyses/{aid}', headers=analyst_h).status_code == 404

    # Organization owner still retains the tenant after removing the creator.
    owner_view = client.get(f'/api/v1/workspaces/{wid}', headers=owner_h)
    assert owner_view.status_code == 200
    assert owner_view.json()["access_role"] == "OWNER"
    assert client.get(f'/api/v1/analyses/{aid}', headers=owner_h).status_code == 200


def test_personal_workspace_creator_ownership_is_unchanged(client):
    _, headers, personal = provision(client, "p34-personal@example.com")
    fetched = client.get(f'/api/v1/workspaces/{personal["id"]}', headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["access_role"] == "OWNER"
    patched = client.patch(
        f'/api/v1/workspaces/{personal["id"]}',
        headers=headers,
        json={"name": "Personal renamed", "role": "Analyst"},
    )
    assert patched.status_code == 200


def test_provider_endpoint_redaction_never_persists_rpc_credentials(client):
    from rivexis_api.core.context import reset_workspace_id, set_workspace_id
    from rivexis_api.provider_runtime import execute, safe_provider_endpoint

    _, headers, workspace = provision(client, "p34-endpoint@example.com")
    secret = "super-secret-provider-token"
    assert safe_provider_endpoint("alchemy", f"https://eth-mainnet.g.alchemy.com/v2/{secret}") == "alchemy:json-rpc"
    assert safe_provider_endpoint("quicknode", f"https://tenant.quiknode.pro/{secret}/") == "quicknode:json-rpc"
    assert safe_provider_endpoint("rest", f"https://user:pass@example.com/path?apikey={secret}#fragment") == "https://example.com"

    token = set_workspace_id(workspace["id"])
    try:
        assert execute(
            "alchemy",
            "eth_call",
            lambda: {"ok": True},
            endpoint=f"https://eth-mainnet.g.alchemy.com/v2/{secret}",
        ) == {"ok": True}
    finally:
        reset_workspace_id(token)

    rows = client.get(
        f'/api/v1/providers/runtime/requests?workspace_id={workspace["id"]}',
        headers=headers,
    )
    assert rows.status_code == 200
    item = rows.json()["items"][0]
    assert item["endpoint"] == "alchemy:json-rpc"
    assert secret not in str(item)


def test_provider_transport_errors_do_not_echo_request_urls(monkeypatch):
    import httpx
    from rivexis_api.provider_clients import JsonRpcClient, ProviderError

    secret = "credential-in-url"
    client = JsonRpcClient("alchemy", f"https://eth-mainnet.g.alchemy.com/v2/{secret}")

    class BrokenClient:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def post(self, url, **kwargs):
            request = httpx.Request("POST", url)
            raise httpx.ConnectError(f"failed to connect to {url}", request=request)

    monkeypatch.setattr(httpx, "Client", BrokenClient)
    with __import__('pytest').raises(ProviderError) as exc:
        client.call("eth_blockNumber")
    assert exc.value.code == "TRANSPORT"
    assert secret not in str(exc.value)
    assert "alchemy.com" not in str(exc.value)


def test_provider_transport_source_does_not_interpolate_raw_httpx_exception():
    root = Path(__file__).resolve().parents[3]
    source = (root / "apps/api/rivexis_api/provider_clients.py").read_text()
    assert "transport failure: {exc}" not in source


def test_provider_upstream_error_text_is_never_exposed_as_public_exception(monkeypatch):
    from rivexis_api.provider_clients import EtherscanClient, JsonRpcClient, ProviderError

    rpc_secret = "rpc-secret-that-must-not-escape"
    err = ProviderError(
        f"upstream echoed https://tenant.rpc.example/{rpc_secret} calldata=0xdeadbeef",
        provider_id="alchemy",
        code="RPC_-32000",
    )
    assert rpc_secret not in str(err)
    assert "0xdeadbeef" not in str(err)
    assert str(err) == "JSON-RPC provider request failed"
    # Raw provider text exists only as an internal debugging attribute and must never be serialized by normal exception surfaces.
    assert rpc_secret in err.internal_message


def test_provider_endpoint_and_error_redaction_source_contract():
    root = Path(__file__).resolve().parents[3]
    clients = (root / "apps/api/rivexis_api/provider_clients.py").read_text()
    runtime = (root / "apps/api/rivexis_api/provider_runtime.py").read_text()
    assert "safe_provider_endpoint" in clients
    assert "endpoint = safe_provider_endpoint(provider_id, endpoint)" in runtime
    assert "transport failure: {exc}" not in clients
    assert "super().__init__(message)" not in clients
