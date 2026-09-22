from __future__ import annotations

import pytest

from rivexis_api.core.context import reset_workspace_id, set_workspace_id
from rivexis_api.provider_runtime import RuntimeControlError, execute, reset_runtime_state, snapshot


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    reset_runtime_state()
    monkeypatch.setenv("RIVEXIS_PROVIDER_RETRY_BASE_SECONDS", "0")
    monkeypatch.setenv("RIVEXIS_PROVIDER_RETRY_MAX_SECONDS", "0")
    monkeypatch.setenv("RIVEXIS_PROVIDER_CALLS_PER_MINUTE", "120")
    monkeypatch.setenv("RIVEXIS_PROVIDER_CIRCUIT_FAILURE_THRESHOLD", "4")
    monkeypatch.setenv("RIVEXIS_PROVIDER_CIRCUIT_COOLDOWN_SECONDS", "30")
    monkeypatch.setenv("RIVEXIS_PROVIDER_MAX_RETRIES", "2")
    yield
    reset_runtime_state()


class Retryable(RuntimeError):
    code = "TIMEOUT"
    retryable = True


def test_retry_then_success_is_counted():
    attempts = {"n": 0}
    def work():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise Retryable("temporary")
        return {"ok": True}
    assert execute("rpc-a", "probe", work) == {"ok": True}
    data = snapshot("GLOBAL")["providers"]["rpc-a"]
    assert attempts["n"] == 3
    assert data["attempts"] == 3
    assert data["retries"] == 2
    assert data["successes"] == 1
    assert data["failures"] == 0


def test_circuit_opens_after_final_failures(monkeypatch):
    monkeypatch.setenv("RIVEXIS_PROVIDER_MAX_RETRIES", "0")
    monkeypatch.setenv("RIVEXIS_PROVIDER_CIRCUIT_FAILURE_THRESHOLD", "2")
    def fail():
        raise Retryable("down")
    for _ in range(2):
        with pytest.raises(Retryable):
            execute("rpc-b", "probe", fail)
    with pytest.raises(RuntimeControlError) as exc:
        execute("rpc-b", "probe", lambda: "should-not-run")
    assert exc.value.code == "CIRCUIT_OPEN"
    data = snapshot("GLOBAL")["providers"]["rpc-b"]
    assert data["circuit"]["state"] == "OPEN"
    assert data["circuit_rejections"] == 1


def test_cache_is_isolated_by_workspace():
    calls = {"n": 0}
    def work():
        calls["n"] += 1
        return calls["n"]
    t1 = set_workspace_id("workspace-a")
    try:
        assert execute("market", "GET", work, cache_key="same", cache_ttl_seconds=60) == 1
        assert execute("market", "GET", work, cache_key="same", cache_ttl_seconds=60) == 1
    finally:
        reset_workspace_id(t1)
    t2 = set_workspace_id("workspace-b")
    try:
        assert execute("market", "GET", work, cache_key="same", cache_ttl_seconds=60) == 2
    finally:
        reset_workspace_id(t2)
    assert snapshot("workspace-a")["providers"]["market"]["cache_hits"] == 1
    assert snapshot("workspace-b")["providers"]["market"]["cache_hits"] == 0


def test_rate_budget_is_workspace_scoped(monkeypatch):
    monkeypatch.setenv("RIVEXIS_PROVIDER_CALLS_PER_MINUTE", "1")
    monkeypatch.setenv("RIVEXIS_PROVIDER_MAX_RETRIES", "0")
    t1 = set_workspace_id("workspace-a")
    try:
        assert execute("quotes", "GET", lambda: 1) == 1
        with pytest.raises(RuntimeControlError) as exc:
            execute("quotes", "GET", lambda: 2)
        assert exc.value.code == "LOCAL_RATE_LIMIT"
    finally:
        reset_workspace_id(t1)
    t2 = set_workspace_id("workspace-b")
    try:
        assert execute("quotes", "GET", lambda: 3) == 3
    finally:
        reset_workspace_id(t2)


def test_estimated_cost_is_accumulated(monkeypatch):
    monkeypatch.setenv("RIVEXIS_PROVIDER_COSTY_ESTIMATED_COST_USD_PER_ATTEMPT", "0.125")
    assert execute("costy", "GET", lambda: "ok") == "ok"
    data = snapshot("GLOBAL")["providers"]["costy"]
    assert data["estimated_cost_usd"] == pytest.approx(0.125)
    assert data["estimated_cost_per_attempt_usd"] == pytest.approx(0.125)


def test_cacheable_concurrent_calls_are_coalesced(monkeypatch):
    import threading
    import time
    from rivexis_api.provider_runtime import execute, reset_runtime_state
    reset_runtime_state()
    monkeypatch.setenv("RIVEXIS_PROVIDER_MAX_RETRIES", "0")
    calls={"n":0}
    gate=threading.Barrier(3)
    results=[]
    errors=[]
    def provider_call():
        calls["n"]+=1
        time.sleep(0.04)
        return {"value":42}
    def worker():
        try:
            gate.wait()
            results.append(execute("fixture","read",provider_call,cache_key="same",cache_ttl_seconds=5))
        except Exception as exc:
            errors.append(exc)
    threads=[threading.Thread(target=worker) for _ in range(2)]
    for t in threads:t.start()
    gate.wait()
    for t in threads:t.join()
    assert not errors
    assert results==[{"value":42},{"value":42}]
    assert calls["n"]==1
