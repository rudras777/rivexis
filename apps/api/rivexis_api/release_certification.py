from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from .certification import seal_evidence, verify_evidence
from .certification_execution import (
    CertificationExecutionError,
    verify_execution_manifest,
)
from .certification_profiles import REQUIRED_STAGING_GATES, normalize_profile, profile_allows
from .version import RELEASE_CODENAME

VALID_STATUSES = {"PASS", "FAIL", "SKIP"}


class CertificationBundleError(ValueError):
    """Raised when staged certification evidence cannot be safely aggregated."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CertificationBundleError(f"{label} must be an object")
    return value


def _valid_sha256(value: Any) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)


def _validate_gate_results(results: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(results, list):
        raise CertificationBundleError(f"{label}.results must be an array")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(results):
        row = _require_mapping(raw, f"{label}.results[{index}]")
        name = str(row.get("name") or "").strip()
        status = str(row.get("status") or "").strip().upper()
        if not name:
            raise CertificationBundleError(f"{label}.results[{index}] is missing a gate name")
        if name in seen:
            raise CertificationBundleError(f"{label} contains duplicate gate {name!r}")
        if status not in VALID_STATUSES:
            raise CertificationBundleError(f"{label}.{name} has invalid status {status!r}")
        seen.add(name)
        normalized.append({**row, "name": name, "status": status})
    return normalized


def _actual_counts(results: list[dict[str, Any]]) -> dict[str, int]:
    return {status: sum(1 for row in results if row["status"] == status) for status in ("PASS", "FAIL", "SKIP")}


def validate_staging_report(
    payload: Any,
    *,
    expected_release: str = RELEASE_CODENAME,
    execution_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = _require_mapping(payload, "staging report")
    if not verify_evidence(report):
        raise CertificationBundleError("staging report evidence SHA-256 mismatch")
    release = str(report.get("release") or "")
    if release != expected_release:
        raise CertificationBundleError(
            f"staging report release mismatch: expected {expected_release}, got {release or '<missing>'}"
        )
    if report.get("schema_version") != 3:
        raise CertificationBundleError(f"{expected_release} staging report schema_version must be 3")

    execution = _require_mapping(report.get("execution"), "staging report execution")
    execution_id = str(execution.get("id") or "")
    manifest_sha = str(execution.get("manifest_evidence_sha256") or "").lower()
    if not _valid_sha256(execution_id):
        raise CertificationBundleError("staging report execution.id is invalid")
    if not _valid_sha256(manifest_sha):
        raise CertificationBundleError("staging report execution.manifest_evidence_sha256 is invalid")

    runner = _require_mapping(report.get("runner"), "staging report runner")
    try:
        profile = normalize_profile(str(runner.get("profile") or ""))
    except ValueError as exc:
        raise CertificationBundleError(str(exc)) from exc
    runner_id = runner.get("id")
    if runner_id is not None and (not isinstance(runner_id, str) or len(runner_id) > 160):
        raise CertificationBundleError("staging report runner.id must be null or a string up to 160 characters")

    source = _require_mapping(report.get("source_tree"), "staging report source_tree")
    source_sha = str(source.get("sha256") or "").strip().lower()
    if not _valid_sha256(source_sha):
        raise CertificationBundleError("staging report source_tree.sha256 is invalid")
    file_count = source.get("file_count")
    if not isinstance(file_count, int) or file_count <= 0:
        raise CertificationBundleError("staging report source_tree.file_count must be a positive integer")

    results = _validate_gate_results(report.get("results"), "staging report")
    result_names = [row["name"] for row in results]
    if result_names != list(REQUIRED_STAGING_GATES):
        raise CertificationBundleError(f"staging report must contain the complete ordered {expected_release} required gate set")
    counts = _actual_counts(results)
    if report.get("counts") != counts:
        raise CertificationBundleError("staging report counts do not match gate results")
    for row in results:
        if row["name"] not in REQUIRED_STAGING_GATES:
            raise CertificationBundleError(f"staging report contains unknown gate {row['name']!r}")
        if row["status"] != "SKIP" and not profile_allows(profile, row["name"]):
            raise CertificationBundleError(
                f"runner profile {profile!r} is not authorized to record {row['status']} for gate {row['name']!r}"
            )

    if execution_manifest is not None:
        try:
            manifest = verify_execution_manifest(execution_manifest)
        except CertificationExecutionError as exc:
            raise CertificationBundleError(str(exc)) from exc
        if release != manifest["release"]:
            raise CertificationBundleError("staging report release does not match execution manifest")
        if execution_id != manifest["execution_id"] or manifest_sha != manifest["evidence_sha256"]:
            raise CertificationBundleError("staging report is bound to a different execution manifest")
        if source != manifest["source_tree"]:
            raise CertificationBundleError("staging report source tree does not match execution manifest")
        if profile not in manifest["required_profiles"]:
            raise CertificationBundleError(f"runner profile {profile!r} is not part of the execution manifest")

    return {
        **report,
        "execution": {"id": execution_id, "manifest_evidence_sha256": manifest_sha},
        "runner": {**runner, "profile": profile},
        "source_tree": {"sha256": source_sha, "file_count": file_count},
        "results": results,
    }


def aggregate_staging_reports(
    reports: Iterable[dict[str, Any]],
    *,
    execution_manifest: dict[str, Any],
    release: str = RELEASE_CODENAME,
    required_gates: Iterable[str] = REQUIRED_STAGING_GATES,
) -> dict[str, Any]:
    try:
        manifest = verify_execution_manifest(execution_manifest)
    except CertificationExecutionError as exc:
        raise CertificationBundleError(str(exc)) from exc
    if manifest["release"] != release:
        raise CertificationBundleError(f"execution manifest release mismatch: expected {release}")

    validated = [
        validate_staging_report(report, expected_release=release, execution_manifest=manifest)
        for report in reports
    ]
    if not validated:
        raise CertificationBundleError("at least one sealed staging report is required")

    source_sha = validated[0]["source_tree"]["sha256"].lower()
    source_count = validated[0]["source_tree"]["file_count"]
    for report in validated[1:]:
        source = report["source_tree"]
        if source["sha256"].lower() != source_sha or source["file_count"] != source_count:
            raise CertificationBundleError("staging reports were produced from different source trees")
    if manifest["source_tree"] != {"sha256": source_sha, "file_count": source_count}:
        raise CertificationBundleError("staging reports do not match the execution manifest source tree")

    gate_names = tuple(dict.fromkeys(str(name).strip() for name in required_gates if str(name).strip()))
    if not gate_names:
        raise CertificationBundleError("required gate set cannot be empty")
    unknown = [name for name in gate_names if name not in REQUIRED_STAGING_GATES]
    if unknown:
        raise CertificationBundleError(f"unknown required gates: {', '.join(unknown)}")
    if list(gate_names) != manifest["required_gates"]:
        raise CertificationBundleError("release required gate set does not match execution manifest")

    indexed = [{row["name"]: row for row in report["results"]} for report in validated]
    merged: list[dict[str, Any]] = []
    for gate in gate_names:
        observations: list[dict[str, Any]] = []
        for report_index, (report, by_name) in enumerate(zip(validated, indexed, strict=True)):
            row = by_name.get(gate)
            if row is None:
                continue
            profile = report["runner"]["profile"]
            observations.append(
                {
                    "report_index": report_index,
                    "report_evidence_sha256": report["evidence_sha256"],
                    "generated_at": report.get("generated_at"),
                    "runner_profile": profile,
                    "runner_id": report["runner"].get("id"),
                    "authorized_for_gate": profile_allows(profile, gate),
                    "status": row["status"],
                    "output_sha256": row.get("output_sha256"),
                    "duration_ms": row.get("duration_ms"),
                }
            )
        statuses = [row["status"] for row in observations if row["authorized_for_gate"]]
        if "FAIL" in statuses:
            status = "FAIL"
            reason = "one or more authorized sealed staging reports recorded FAIL"
        elif "PASS" in statuses:
            status = "PASS"
            reason = "at least one authorized sealed staging report recorded PASS and none recorded FAIL"
        else:
            status = "SKIP"
            reason = "no authorized sealed staging report recorded PASS or FAIL"
        merged.append({"name": gate, "status": status, "reason": reason, "observations": observations})

    counts = _actual_counts(merged)
    observed_profiles = sorted({report["runner"]["profile"] for report in validated})
    required_profiles = list(manifest["required_profiles"])
    missing_profiles = [profile for profile in required_profiles if profile not in observed_profiles]
    coverage_complete = not missing_profiles
    certified = (
        counts["FAIL"] == 0
        and counts["SKIP"] == 0
        and counts["PASS"] == len(merged)
        and coverage_complete
    )
    payload = {
        "schema_version": 3,
        "release": release,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execution": {
            "id": manifest["execution_id"],
            "manifest_evidence_sha256": manifest["evidence_sha256"],
            "required_profiles": required_profiles,
            "observed_profiles": observed_profiles,
            "missing_profiles": missing_profiles,
            "coverage_complete": coverage_complete,
        },
        "source_tree": {"sha256": source_sha, "file_count": source_count},
        "required_gates": list(gate_names),
        "input_reports": [
            {
                "report_index": index,
                "evidence_sha256": report["evidence_sha256"],
                "generated_at": report.get("generated_at"),
                "execution": report.get("execution"),
                "runner": report.get("runner"),
                "runtime": report.get("runtime"),
                "counts": report.get("counts"),
            }
            for index, report in enumerate(validated)
        ],
        "results": merged,
        "counts": counts,
        "certified": certified,
    }
    return seal_evidence(payload)


def verify_release_bundle(
    payload: Any,
    *,
    expected_release: str = RELEASE_CODENAME,
    require_complete: bool = False,
    execution_manifest: dict[str, Any] | None = None,
) -> bool:
    if not isinstance(payload, dict) or not verify_evidence(payload):
        return False
    if str(payload.get("release") or "") != expected_release or payload.get("schema_version") != 3:
        return False

    execution = payload.get("execution")
    if not isinstance(execution, dict):
        return False
    if not _valid_sha256(execution.get("id")) or not _valid_sha256(execution.get("manifest_evidence_sha256")):
        return False
    required_profiles = execution.get("required_profiles")
    observed_profiles = execution.get("observed_profiles")
    missing_profiles = execution.get("missing_profiles")
    if not isinstance(required_profiles, list) or not isinstance(observed_profiles, list) or not isinstance(missing_profiles, list):
        return False
    if len(set(required_profiles)) != len(required_profiles) or len(set(observed_profiles)) != len(observed_profiles):
        return False
    if any(profile not in required_profiles for profile in observed_profiles):
        return False
    expected_missing = [profile for profile in required_profiles if profile not in observed_profiles]
    if missing_profiles != expected_missing or execution.get("coverage_complete") is not (not expected_missing):
        return False

    required = payload.get("required_gates")
    results = payload.get("results")
    inputs = payload.get("input_reports")
    if not isinstance(required, list) or not required or not isinstance(results, list) or not isinstance(inputs, list):
        return False
    if any(name not in REQUIRED_STAGING_GATES for name in required):
        return False
    try:
        normalized = _validate_gate_results(results, "release bundle")
    except CertificationBundleError:
        return False
    names = [row["name"] for row in normalized]
    if names != required or len(set(required)) != len(required):
        return False
    counts = _actual_counts(normalized)
    if payload.get("counts") != counts:
        return False
    certified = (
        counts["FAIL"] == 0
        and counts["SKIP"] == 0
        and counts["PASS"] == len(normalized)
        and execution.get("coverage_complete") is True
    )
    if payload.get("certified") is not certified:
        return False
    if require_complete and not certified:
        return False

    source = payload.get("source_tree")
    if not isinstance(source, dict) or not _valid_sha256(source.get("sha256")) or not isinstance(source.get("file_count"), int):
        return False

    input_profiles: dict[int, str] = {}
    input_execution: set[tuple[str, str]] = set()
    for item in inputs:
        if not isinstance(item, dict) or not isinstance(item.get("report_index"), int):
            return False
        runner = item.get("runner")
        report_execution = item.get("execution")
        if not isinstance(runner, dict) or not isinstance(report_execution, dict):
            return False
        try:
            profile = normalize_profile(str(runner.get("profile") or ""))
        except ValueError:
            return False
        if profile not in required_profiles:
            return False
        input_profiles[item["report_index"]] = profile
        input_execution.add(
            (
                str(report_execution.get("id") or ""),
                str(report_execution.get("manifest_evidence_sha256") or ""),
            )
        )
    if input_execution != {(execution["id"], execution["manifest_evidence_sha256"])}:
        return False
    if sorted(set(input_profiles.values())) != observed_profiles:
        return False

    for row in normalized:
        observations = row.get("observations")
        if not isinstance(observations, list):
            return False
        for obs in observations:
            if not isinstance(obs, dict) or not isinstance(obs.get("report_index"), int):
                return False
            profile = input_profiles.get(obs["report_index"])
            if profile is None or obs.get("runner_profile") != profile:
                return False
            authorized = profile_allows(profile, row["name"])
            if obs.get("authorized_for_gate") is not authorized:
                return False
            if obs.get("status") not in VALID_STATUSES:
                return False
            if obs.get("status") != "SKIP" and not authorized:
                return False

    if execution_manifest is not None:
        try:
            manifest = verify_execution_manifest(execution_manifest)
        except CertificationExecutionError:
            return False
        if manifest["release"] != expected_release or manifest["source_tree"] != source:
            return False
        if execution["id"] != manifest["execution_id"] or execution["manifest_evidence_sha256"] != manifest["evidence_sha256"]:
            return False
        if required_profiles != manifest["required_profiles"] or required != manifest["required_gates"]:
            return False
    return True
