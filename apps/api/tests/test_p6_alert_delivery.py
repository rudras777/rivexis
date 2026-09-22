from __future__ import annotations

from rivexis_api.services.alert_delivery import process_due_alerts
from rivexis_api.services.store import alert_delivery_metrics, mark_alert_delivery


def provision(client,email="p6-alerts@example.com"):
    signup=client.post('/api/v1/auth/signup',json={"email":email,"password":"correct-horse-battery","role":"Analyst"})
    headers={"Authorization":"Bearer "+signup.json()["access_token"]}
    ws=client.post('/api/v1/workspaces',headers=headers,json={"name":"SOC","role":"Analyst"}).json()
    mon=client.post('/api/v1/monitors',headers=headers,json={"workspace_id":ws["id"],"entity":"0x1111111111111111111111111111111111111111","chain":"ethereum","rules":["threat"]}).json()
    return headers,ws,mon


def ingress(client,ws,mon,event_id="hn-p6-1"):
    body={"workspace_id":ws["id"],"monitor_id":mon["id"],"event_type":"threat","severity":"critical","affected_entity":mon["entity"],"confidence":99,"provider_payload":{"source_event_id":event_id}}
    return client.post('/api/v1/integrations/hypernative/events',json=body,headers={"X-Rivexis-Webhook-Secret":"secret"})


def test_replay_increments_occurrence_without_duplicate_alert(client,monkeypatch):
    monkeypatch.setenv("HYPERNATIVE_WEBHOOK_SECRET","secret")
    headers,ws,mon=provision(client)
    first=ingress(client,ws,mon,"hn-repeat")
    second=ingress(client,ws,mon,"hn-repeat")
    assert first.status_code==second.status_code==202
    items=client.get('/api/v1/alerts',headers=headers,params={"workspace_id":ws["id"]}).json()["items"]
    row=next(x for x in items if x["id"]==first.json()["alert_id"])
    assert row["occurrence_count"]==2
    assert row["delivery_status"]=="pending"
    assert len([x for x in items if x["external_event_key"]=="hn-repeat"])==1


def test_delivery_success_and_slo_metrics(client,monkeypatch):
    monkeypatch.setenv("HYPERNATIVE_WEBHOOK_SECRET","secret")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_URL","https://receiver.invalid/alerts")
    headers,ws,mon=provision(client,"p6-success@example.com")
    accepted=ingress(client,ws,mon,"hn-success")
    sent=[]
    result=process_due_alerts(ws["id"],sender=lambda alert: sent.append(alert["id"]) or {"status_code":202,"latency_ms":1.2})
    assert result["processed"]==1 and result["items"][0]["result"]=="delivered"
    assert sent==[accepted.json()["alert_id"]]
    metrics=client.get('/api/v1/alerts/delivery-metrics',headers=headers,params={"workspace_id":ws["id"],"slo_seconds":300})
    assert metrics.status_code==200
    body=metrics.json(); assert body["delivered"]==1 and body["pending"]==0 and body["dead_letter"]==0
    assert body["delivered_within_slo_percent"]==100.0


def test_delivery_failure_retries_then_dead_letters(client,monkeypatch):
    monkeypatch.setenv("HYPERNATIVE_WEBHOOK_SECRET","secret")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_URL","https://receiver.invalid/alerts")
    monkeypatch.setenv("RIVEXIS_ALERT_MAX_ATTEMPTS","2")
    monkeypatch.setenv("RIVEXIS_ALERT_RETRY_BASE_SECONDS","1")
    headers,ws,mon=provision(client,"p6-fail@example.com")
    accepted=ingress(client,ws,mon,"hn-fail")
    result=process_due_alerts(ws["id"],sender=lambda alert: (_ for _ in ()).throw(RuntimeError("receiver down")))
    assert result["items"][0]["result"]=="retry"
    alert_id=accepted.json()["alert_id"]
    dead=mark_alert_delivery(alert_id,success=False,error="receiver still down",max_attempts=2,retry_base_seconds=1)
    assert dead["delivery_status"]=="dead_letter" and dead["dead_lettered_at"]
    requeued=client.post(f'/api/v1/alerts/{alert_id}/requeue',headers=headers)
    assert requeued.status_code==200
    assert requeued.json()["delivery_status"]=="pending" and requeued.json()["delivery_attempts"]==0


def test_processing_endpoint_does_not_claim_delivery_without_sink(client,monkeypatch):
    monkeypatch.setenv("HYPERNATIVE_WEBHOOK_SECRET","secret")
    monkeypatch.delenv("RIVEXIS_ALERT_WEBHOOK_URL",raising=False)
    headers,ws,mon=provision(client,"p6-nosink@example.com")
    ingress(client,ws,mon,"hn-nosink")
    response=client.post('/api/v1/alerts/process-due',headers=headers,params={"workspace_id":ws["id"]})
    assert response.status_code==200
    assert response.json()["processed"]==0
    assert response.json()["reason"]=="delivery_not_configured"
    items=client.get('/api/v1/alerts',headers=headers,params={"workspace_id":ws["id"]}).json()["items"]
    assert items[0]["delivery_status"]=="pending" and items[0]["delivery_attempts"]==0

def test_due_workspace_discovery_finds_pending_workspace(client,monkeypatch):
    from rivexis_api.services.store import due_alert_workspace_ids
    monkeypatch.setenv("HYPERNATIVE_WEBHOOK_SECRET","secret")
    _,ws,mon=provision(client,"p6-worker@example.com")
    ingress(client,ws,mon,"hn-worker")
    assert ws["id"] in due_alert_workspace_ids()
