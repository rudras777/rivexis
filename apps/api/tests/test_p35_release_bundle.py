from __future__ import annotations

from pathlib import Path

import pytest

from rivexis_api.certification import seal_evidence
from rivexis_api.certification_execution import PRODUCTION_EXECUTION_PROFILES, build_execution_manifest
from rivexis_api.certification_profiles import PROFILE_GATES, REQUIRED_STAGING_GATES
from rivexis_api.release_certification import (
    CertificationBundleError,
    aggregate_staging_reports,
    verify_release_bundle,
)


def make_manifest(tmp_path: Path):
    (tmp_path / "source.txt").write_text("release source")
    return build_execution_manifest(tmp_path)


def staging(manifest, statuses: dict[str, str], *, profile: str, source: str | None = None):
    merged = {name: "SKIP" for name in REQUIRED_STAGING_GATES}
    merged.update(statuses)
    results = [
        {"name": name, "status": merged[name], "duration_ms": 1, "output_sha256": "b" * 64}
        for name in REQUIRED_STAGING_GATES
    ]
    counts = {status: sum(1 for value in merged.values() if value == status) for status in ("PASS", "FAIL", "SKIP")}
    source_tree = dict(manifest["source_tree"])
    if source is not None:
        source_tree["sha256"] = source
    return seal_evidence(
        {
            "schema_version": 3,
            "release": "P37",
            "generated_at": "2026-09-11T00:00:00+00:00",
            "execution": {
                "id": manifest["execution_id"],
                "manifest_evidence_sha256": manifest["evidence_sha256"],
            },
            "runner": {"profile": profile, "id": f"test-{profile}"},
            "runtime": {"python": "3.13"},
            "source_tree": source_tree,
            "results": results,
            "counts": counts,
        }
    )


def complete_reports(manifest):
    return [
        staging(manifest, {gate: "PASS" for gate in PROFILE_GATES[profile]}, profile=profile)
        for profile in PRODUCTION_EXECUTION_PROFILES
    ]


def test_bundle_is_complete_only_when_every_gate_and_planned_profile_passes(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    bundle = aggregate_staging_reports(complete_reports(manifest), execution_manifest=manifest)
    assert bundle["certified"] is True
    assert bundle["execution"]["coverage_complete"] is True
    assert bundle["counts"] == {"PASS": len(REQUIRED_STAGING_GATES), "FAIL": 0, "SKIP": 0}
    assert verify_release_bundle(bundle, require_complete=True, execution_manifest=manifest) is True


def test_missing_planned_profile_blocks_certification_even_if_all_gates_have_pass(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    reports = [report for profile, report in zip(PRODUCTION_EXECUTION_PROFILES, complete_reports(manifest), strict=True) if profile != "dependencies"]
    bundle = aggregate_staging_reports(reports, execution_manifest=manifest)
    assert bundle["counts"]["SKIP"] == 0
    assert bundle["execution"]["missing_profiles"] == ["dependencies"]
    assert bundle["certified"] is False
    assert verify_release_bundle(bundle, require_complete=True, execution_manifest=manifest) is False


def test_authorized_profile_can_fill_skip_from_another_runner(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    first = staging(manifest, {}, profile="local")
    second = staging(manifest, {"postgres-rls": "PASS"}, profile="postgres-rls")
    bundle = aggregate_staging_reports([first, second], execution_manifest=manifest)
    row = next(item for item in bundle["results"] if item["name"] == "postgres-rls")
    assert row["status"] == "PASS"
    assert any(obs["runner_profile"] == "postgres-rls" and obs["authorized_for_gate"] for obs in row["observations"])


def test_unauthorized_profile_cannot_record_pass_for_gate(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    report = staging(manifest, {"postgres-rls": "PASS"}, profile="redis")
    with pytest.raises(CertificationBundleError, match="not authorized"):
        aggregate_staging_reports([report], execution_manifest=manifest)


def test_fail_is_fail_closed_even_when_another_authorized_runner_passes(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    first = staging(manifest, {"redis-distributed": "PASS"}, profile="redis")
    second = staging(manifest, {"redis-distributed": "FAIL"}, profile="redis")
    bundle = aggregate_staging_reports([first, second], execution_manifest=manifest)
    row = next(item for item in bundle["results"] if item["name"] == "redis-distributed")
    assert row["status"] == "FAIL"
    assert bundle["counts"]["FAIL"] == 1


def test_bundle_rejects_mixed_source_trees(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    with pytest.raises(CertificationBundleError, match="source tree"):
        aggregate_staging_reports(
            [
                staging(manifest, {"otlp-local": "PASS"}, profile="local"),
                staging(manifest, {"postgres-rls": "PASS"}, source="c" * 64, profile="postgres-rls"),
            ],
            execution_manifest=manifest,
        )


def test_bundle_rejects_tampered_input_report(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    report = staging(manifest, {"otlp-local": "PASS"}, profile="local")
    report["results"][0]["status"] = "FAIL"
    with pytest.raises(CertificationBundleError, match="evidence SHA-256 mismatch"):
        aggregate_staging_reports([report], execution_manifest=manifest)


def test_bundle_rejects_mismatched_staging_counts_even_when_resealed(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    report = staging(manifest, {"otlp-local": "PASS"}, profile="local")
    report["counts"] = {"PASS": 0, "FAIL": 0, "SKIP": len(REQUIRED_STAGING_GATES)}
    report = seal_evidence(report)
    with pytest.raises(CertificationBundleError, match="counts do not match"):
        aggregate_staging_reports([report], execution_manifest=manifest)


def test_bundle_rejects_omitted_gate_even_when_resealed(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    report = staging(manifest, {"otlp-local": "PASS"}, profile="local")
    report["results"].pop()
    report["counts"]["SKIP"] -= 1
    report = seal_evidence(report)
    with pytest.raises(CertificationBundleError, match="complete ordered"):
        aggregate_staging_reports([report], execution_manifest=manifest)


def test_bundle_rejects_different_execution_manifest_binding(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    report = staging(manifest, {"otlp-local": "PASS"}, profile="local")
    report["execution"]["id"] = "d" * 64
    report = seal_evidence(report)
    with pytest.raises(CertificationBundleError, match="different execution manifest"):
        aggregate_staging_reports([report], execution_manifest=manifest)


def test_bundle_contract_rejects_profile_tampering(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    bundle = aggregate_staging_reports(complete_reports(manifest), execution_manifest=manifest)
    bundle["input_reports"][0]["runner"]["profile"] = "redis"
    bundle = seal_evidence(bundle)
    assert verify_release_bundle(bundle, execution_manifest=manifest) is False
