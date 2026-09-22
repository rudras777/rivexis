from __future__ import annotations

import json
from pathlib import Path

from rivexis_api.services.alert_delivery import delivery_error_type, delivery_log_summary
from rivexis_api.workers.alerts import _emit_cycle_log, _emit_error_log


def _sensitive_result():
    return [
        {
            "workspace_id": "workspace-secret-123",
            "processed": 2,
            "skipped": 1,
            "reason": "receiver https://user:password@example.invalid failed",
            "items": [
                {
                    "id": "alert-secret-1",
                    "result": "delivered",
                    "delivery": {"status_code": 204, "latency_ms": 1.2},
                    "alert": {
                        "workspace_id": "workspace-secret-123",
                        "payload": {
                            "wallet": "0xTENANTSECRET",
                            "api_key": "tenant-api-key-secret",
                            "evidence": "private risk evidence",
                        },
                    },
                },
                {
                    "id": "alert-secret-2",
                    "result": "retry",
                    "error": "postgresql://worker:db-secret@host/rivexis",
                    "alert": {"payload": {"secret": "second-tenant-secret"}},
                },
            ],
        }
    ]


def test_shared_delivery_log_summary_contains_operational_counters_only() -> None:
    summary = delivery_log_summary(_sensitive_result())
    assert summary == {
        "workspace_count": 1,
        "processed": 2,
        "skipped": 1,
        "delivered": 1,
        "retry": 1,
        "dead_letter": 0,
        "configuration_degraded": True,
    }
    serialized = json.dumps(summary)
    for secret in (
        "workspace-secret-123",
        "alert-secret-1",
        "0xTENANTSECRET",
        "tenant-api-key-secret",
        "private risk evidence",
        "db-secret",
        "password",
    ):
        assert secret not in serialized


def test_alert_worker_cycle_stdout_never_contains_alert_payload_or_freeform_errors(capsys) -> None:
    _emit_cycle_log(_sensitive_result())
    output = capsys.readouterr().out
    decoded = json.loads(output)
    assert decoded["event"] == "alert_worker_cycle"
    assert set(decoded) == {"event", "summary"}
    assert decoded["summary"]["delivered"] == 1
    assert decoded["summary"]["retry"] == 1
    for secret in (
        "workspace-secret-123",
        "alert-secret-1",
        "0xTENANTSECRET",
        "tenant-api-key-secret",
        "private risk evidence",
        "postgresql://",
        "db-secret",
        "password",
    ):
        assert secret not in output


def test_alert_worker_error_stdout_reports_type_not_exception_message(capsys) -> None:
    _emit_error_log(RuntimeError("tenant-secret https://user:password@example.invalid"))
    output = capsys.readouterr().out
    assert json.loads(output) == {"event": "alert_worker_error", "error_type": "RuntimeError"}
    assert "tenant-secret" not in output
    assert "password" not in output
    assert delivery_error_type(ValueError("secret")) == "ValueError"


def test_manual_alert_queue_cli_uses_shared_metadata_only_redaction_contract() -> None:
    root = Path(__file__).resolve().parents[3]
    cli = (root / "scripts" / "process_alert_queue.py").read_text()
    assert "delivery_log_summary([result])" in cli
    assert '"event":"alert_queue_process"' in cli.replace(" ", "")
    assert "delivery_error_type(exc)" in cli
    assert "json.dumps(process_due_alerts(" not in cli
    assert '"error":str(exc)' not in cli
    assert "print(json.dumps(result" not in cli
