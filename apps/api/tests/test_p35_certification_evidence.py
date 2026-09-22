from __future__ import annotations

import json
from pathlib import Path

import pytest

from rivexis_api.certification import canonical_json, seal_evidence, source_tree_fingerprint, verify_evidence
from rivexis_api.certification_execution import (
    CertificationExecutionError,
    PRODUCTION_EXECUTION_PROFILES,
    build_execution_manifest,
    verify_execution_manifest,
)
from rivexis_api.certification_profiles import (
    GATE_SPECS,
    PROFILE_GATES,
    REQUIRED_STAGING_GATES,
    certification_plan,
    classify_gate_process_result,
)


def test_evidence_seal_detects_tampering() -> None:
    payload = {"release": "P37", "counts": {"PASS": 1, "FAIL": 0, "SKIP": 0}}
    sealed = seal_evidence(payload)
    assert verify_evidence(sealed) is True
    sealed["counts"]["PASS"] = 2
    assert verify_evidence(sealed) is False


def test_canonical_json_is_order_independent() -> None:
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_source_tree_fingerprint_ignores_transient_certification_files(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("alpha")
    digest1, count1 = source_tree_fingerprint(tmp_path)
    (tmp_path / "cache.db").write_bytes(b"generated")
    (tmp_path / "certification-execution-manifest.json").write_text("generated")
    (tmp_path / "certification-reports").mkdir()
    (tmp_path / "certification-reports" / "local.json").write_text("generated")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_bytes(b"generated")
    digest2, count2 = source_tree_fingerprint(tmp_path)
    assert digest1 == digest2
    assert count1 == count2 == 1


def test_browser_certification_dependencies_are_pinned() -> None:
    root = Path(__file__).resolve().parents[3]
    package = json.loads((root / "apps" / "web" / "package.json").read_text())
    assert package["devDependencies"]["@playwright/test"] == "1.63.0"
    assert package["devDependencies"]["@axe-core/playwright"] == "4.13.0"
    assert package["scripts"]["test:e2e"] == "playwright test"


def test_p36_runner_generated_root_lockfile_does_not_change_source_fingerprint(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("alpha")
    digest1, count1 = source_tree_fingerprint(tmp_path)
    (tmp_path / "package-lock.json").write_text('{"name":"rivexis","lockfileVersion":3,"packages":{}}')
    digest2, count2 = source_tree_fingerprint(tmp_path)
    assert digest1 == digest2
    assert count1 == count2 == 1


def test_p36_frontend_type_dependencies_are_exactly_pinned() -> None:
    root = Path(__file__).resolve().parents[3]
    package = json.loads((root / "apps" / "web" / "package.json").read_text())
    assert package["devDependencies"]["@types/node"] == "22.20.2"
    assert package["devDependencies"]["@types/react"] == "19.3.0"
    assert package["devDependencies"]["@types/react-dom"] == "19.3.0"




def test_p37_gate_result_classifier_catches_multiline_provider_skip_without_false_pass() -> None:
    output = (
        "Blockaid certification: SKIP - set RIVEXIS_CERTIFICATION_ADDRESS\n"
        "SKIP live provider certification: no certifiable credentialed P5 provider + target configured"
    )
    assert classify_gate_process_result(0, output) == "SKIP"


def test_p37_gate_result_classifier_preserves_overall_pass_after_partial_provider_skip() -> None:
    output = (
        "Blockaid certification: SKIP - set RIVEXIS_CERTIFICATION_ADDRESS\n"
        "Nansen certification: PASS\n"
        "Live provider certification: PASS (1 provider probe(s))"
    )
    assert classify_gate_process_result(0, output) == "PASS"


def test_p37_gate_result_classifier_preserves_dependency_skip_and_fail() -> None:
    assert classify_gate_process_result(0, "SKIP dependency certification: prerequisites unavailable\n{\"overall\":\"SKIP\"}") == "SKIP"
    assert classify_gate_process_result(1, "anything") == "FAIL"


def test_p37_gate_result_classifier_requires_explicit_success_evidence() -> None:
    assert classify_gate_process_result(0, "") == "FAIL"
    assert classify_gate_process_result(0, "completed") == "FAIL"
    assert classify_gate_process_result(0, '{"status":"PASS","event_count":1}') == "PASS"
    assert classify_gate_process_result(0, "OTLP certification: PASS (3 spans)") == "PASS"


def test_p24_runner_profiles_cover_every_required_gate() -> None:
    covered = {gate for profile, gates in PROFILE_GATES.items() if profile != "full" for gate in gates}
    assert covered == set(REQUIRED_STAGING_GATES)
    assert tuple(GATE_SPECS) == REQUIRED_STAGING_GATES


def test_certification_plan_contains_no_secret_values_and_marks_dr_destructive() -> None:
    plan = certification_plan()
    assert plan["release"] == "P37"
    assert plan["gates"]["postgres-dr"]["destructive"] is True
    assert "RIVEXIS_BACKUP_SOURCE_DATABASE_URL" in plan["gates"]["postgres-dr"]["prerequisites"]
    rendered = json.dumps(plan)
    assert "postgresql://" not in rendered
    assert "sk-" not in rendered


def test_execution_manifest_is_source_bound_and_covers_specialized_profiles(tmp_path: Path) -> None:
    (tmp_path / "source.txt").write_text("release source")
    manifest = build_execution_manifest(tmp_path)
    verified = verify_execution_manifest(manifest, root=tmp_path)
    assert verified["release"] == "P37"
    assert verified["required_profiles"] == list(PRODUCTION_EXECUTION_PROFILES)
    assert verified["required_gates"] == list(REQUIRED_STAGING_GATES)
    assert "full" not in verified["required_profiles"]
    assert next(row for row in verified["reports"] if row["profile"] == "postgres-dr")["destructive_gates"] == [
        "postgres-dr"
    ]


def test_execution_manifest_rejects_tampering_even_when_source_is_unchanged(tmp_path: Path) -> None:
    (tmp_path / "source.txt").write_text("release source")
    manifest = build_execution_manifest(tmp_path)
    manifest["required_profiles"].pop()
    manifest = seal_evidence(manifest)
    with pytest.raises(CertificationExecutionError, match="required_profiles"):
        verify_execution_manifest(manifest, root=tmp_path)


def test_execution_manifest_rejects_source_drift(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("release source")
    manifest = build_execution_manifest(tmp_path)
    source.write_text("changed")
    with pytest.raises(CertificationExecutionError, match="source tree"):
        verify_execution_manifest(manifest, root=tmp_path)




def test_execution_manifest_rejects_noncanonical_generated_paths(tmp_path: Path) -> None:
    (tmp_path / "source.txt").write_text("release source")
    with pytest.raises(CertificationExecutionError, match="report_dir"):
        build_execution_manifest(tmp_path, report_dir="other-evidence")
    with pytest.raises(CertificationExecutionError, match="manifest_path"):
        build_execution_manifest(tmp_path, manifest_path="other-manifest.json")


def test_staging_orchestrator_has_p22_execution_binding() -> None:
    root = Path(__file__).resolve().parents[3]
    text = (root / "scripts" / "certify_staging_suite.py").read_text()
    assert "from rivexis_api.version import RELEASE_CODENAME" in text
    assert '"release": RELEASE_CODENAME' in text
    assert '"schema_version": 3' in text
    assert "RIVEXIS_CERT_EXECUTION_MANIFEST" in text
    assert "manifest_evidence_sha256" in text


def test_protocol_gate_activates_from_concrete_adapter_targets() -> None:
    from rivexis_api.certification_profiles import gate_enabled
    assert gate_enabled("protocol-adapters", {"RIVEXIS_CERT_AAVE_ASSET": "0xabc"}) is True
    assert gate_enabled("protocol-adapters", {"RIVEXIS_CERT_COMPOUND_ASSET": "0xdef"}) is True
    assert gate_enabled("protocol-adapters", {"RIVEXIS_CERT_MORPHO_MARKET_ID": "0x123"}) is True
    assert gate_enabled("protocol-adapters", {}) is False


def test_protocol_gate_plan_exposes_only_concrete_adapter_prerequisites() -> None:
    plan = certification_plan()
    prereqs = plan["gates"]["protocol-adapters"]["prerequisites"]
    assert prereqs == [
        "RIVEXIS_CERT_AAVE_ASSET",
        "RIVEXIS_CERT_COMPOUND_ASSET",
        "RIVEXIS_CERT_MORPHO_MARKET_ID",
    ]
    assert "RIVEXIS_CERT_PROTOCOL_ADAPTER" not in json.dumps(plan)
