from __future__ import annotations

import re

import pytest

from rivexis_api.core.context import get_span_id, get_trace_id
from rivexis_api.core.telemetry import TelemetryConfigurationError, child_span, init_telemetry, shutdown_telemetry, telemetry_export_status


def auth(client):
    signup=client.post('/api/v1/auth/signup',json={'email':'p12-observability@example.com','password':'correct-horse-battery','role':'Analyst'})
    return {'Authorization':'Bearer '+signup.json()['access_token']}


def test_child_span_preserves_trace_and_uses_distinct_span_id(monkeypatch):
    monkeypatch.setenv('RIVEXIS_OTEL_ENABLED','false')
    from rivexis_api.core.context import set_trace_context,reset_trace_context
    token=set_trace_context('a'*32,'b'*16)
    try:
        with child_span('provider.test',kind='client') as child:
            assert get_trace_id()=='a'*32
            assert get_span_id()==child.context.span_id
            assert child.context.span_id!='b'*16
            assert child.context.parent_span_id=='b'*16
            assert re.fullmatch(r'[0-9a-f]{16}',child.context.span_id)
        assert get_span_id()=='b'*16
    finally:
        reset_trace_context(token)


def test_enabled_otlp_requires_endpoint(monkeypatch):
    shutdown_telemetry()
    monkeypatch.setenv('RIVEXIS_OTEL_ENABLED','true')
    monkeypatch.delenv('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT',raising=False)
    monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT',raising=False)
    with pytest.raises(TelemetryConfigurationError,match='requires OTEL_EXPORTER'):
        init_telemetry(force=True)
    shutdown_telemetry()


def test_observability_status_endpoint_is_authenticated(client,monkeypatch):
    monkeypatch.setenv('RIVEXIS_OTEL_ENABLED','false')
    assert client.get('/api/v1/observability/status').status_code==401
    response=client.get('/api/v1/observability/status',headers=auth(client))
    assert response.status_code==200
    body=response.json()
    assert body['enabled'] is False
    assert body['service_name']=='rivexis-api'
    assert body['protocol']=='http/protobuf'

def test_unsampled_parent_keeps_unsampled_child_headers(monkeypatch):
    monkeypatch.setenv('RIVEXIS_OTEL_ENABLED','false')
    from rivexis_api.core.telemetry import request_span, trace_headers
    with request_span('GET /unsampled',incoming_traceparent='00-'+'3'*32+'-'+'4'*16+'-00') as root:
        assert root.context.sampled is False
        with child_span('provider.unsampled',kind='client') as child:
            assert child.context.sampled is False
            assert trace_headers()['traceparent'].endswith('-00')
