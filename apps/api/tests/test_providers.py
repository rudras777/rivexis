from rivexis_api.providers import resolve_provider

def test_unconfigured_provider_does_not_auto_demo(monkeypatch):
    for k in ["ALCHEMY_API_KEY","QUICKNODE_URL","ETHEREUM_RPC_URL"]: monkeypatch.delenv(k,raising=False)
    r=resolve_provider("rpc",allow_demo=False);assert r.provider_id is None and r.status=="PROVIDER_UNAVAILABLE"
def test_demo_requires_opt_in(monkeypatch):
    for k in ["ALCHEMY_API_KEY","QUICKNODE_URL","ETHEREUM_RPC_URL"]: monkeypatch.delenv(k,raising=False)
    r=resolve_provider("rpc",allow_demo=True);assert r.provider_id=="mock" and r.status=="DEMO"
