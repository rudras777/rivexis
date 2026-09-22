from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .certification import canonical_json, seal_evidence, sha256_text, source_tree_fingerprint, verify_evidence
from .certification_profiles import GATE_SPECS, PROFILE_GATES, REQUIRED_STAGING_GATES, normalize_profile
from .version import RELEASE_CODENAME

EXECUTION_RELEASE = RELEASE_CODENAME
EXECUTION_SCHEMA_VERSION = 1
PRODUCTION_EXECUTION_PROFILES = (
    "local",
    "postgres-rls",
    "postgres-dr",
    "redis",
    "registry",
    "providers",
    "protocol",
    "history",
    "dependencies",
)
DEFAULT_MANIFEST_NAME = "certification-execution-manifest.json"
DEFAULT_REPORT_DIR = "certification-reports"
DEFAULT_BUNDLE_NAME = "release-certification-bundle.json"


class CertificationExecutionError(ValueError):
    """Raised when a production certification execution manifest is malformed or stale."""


def _safe_relative_path(value: str, label: str) -> str:
    text = value.strip().replace("\\", "/")
    path = PurePosixPath(text)
    if not text or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise CertificationExecutionError(f"{label} must be a safe repository-relative path")
    return path.as_posix()


def _execution_id_payload(
    source_tree: dict[str, Any],
    required_profiles: list[str],
    required_gates: list[str],
    manifest_path: str,
    report_dir: str,
) -> dict[str, Any]:
    return {
        "release": EXECUTION_RELEASE,
        "source_tree": source_tree,
        "required_profiles": required_profiles,
        "required_gates": required_gates,
        "manifest_path": manifest_path,
        "report_dir": report_dir,
    }


def _profile_prerequisites(profile: str) -> list[str]:
    names = {
        name
        for gate in PROFILE_GATES[profile]
        for name in GATE_SPECS[gate]["prerequisites"]
    }
    return sorted(names)


def _profile_destructive_gates(profile: str) -> list[str]:
    return [gate for gate in PROFILE_GATES[profile] if GATE_SPECS[gate]["destructive"]]


def _report_plan(profile: str, report_dir: str, manifest_path: str) -> dict[str, Any]:
    path = f"{report_dir}/{profile}.json"
    return {
        "profile": profile,
        "path": path,
        "gates": list(PROFILE_GATES[profile]),
        "prerequisites": _profile_prerequisites(profile),
        "destructive_gates": _profile_destructive_gates(profile),
        "command": (
            f"RIVEXIS_CERT_RUNNER_PROFILE={profile} "
            f"RIVEXIS_STAGING_CERT_REPORT={path} "
            f"RIVEXIS_CERT_EXECUTION_MANIFEST={manifest_path} "
            "python scripts/certify_staging_suite.py"
        ),
    }


def _aggregate_plan(reports: list[dict[str, Any]], manifest_path: str) -> dict[str, str]:
    aggregate_reports = " ".join(f"--report {row['path']}" for row in reports)
    return {
        "output": DEFAULT_BUNDLE_NAME,
        "command": (
            f"python scripts/certify_release_bundle.py --manifest {manifest_path} "
            f"{aggregate_reports}"
        ),
        "verify_command": (
            f"python scripts/verify_release_bundle.py {DEFAULT_BUNDLE_NAME} "
            f"--manifest {manifest_path} --require-complete"
        ),
    }


def build_execution_manifest(
    root: Path,
    *,
    report_dir: str = DEFAULT_REPORT_DIR,
    manifest_path: str = DEFAULT_MANIFEST_NAME,
) -> dict[str, Any]:
    report_dir = _safe_relative_path(report_dir, "report_dir")
    manifest_path = _safe_relative_path(manifest_path, "manifest_path")
    if report_dir != DEFAULT_REPORT_DIR:
        raise CertificationExecutionError(f"{EXECUTION_RELEASE} report_dir must be {DEFAULT_REPORT_DIR!r}")
    if manifest_path != DEFAULT_MANIFEST_NAME:
        raise CertificationExecutionError(f"{EXECUTION_RELEASE} manifest_path must be {DEFAULT_MANIFEST_NAME!r}")
    source_sha, source_count = source_tree_fingerprint(root)
    source_tree = {"sha256": source_sha, "file_count": source_count}
    required_profiles = list(PRODUCTION_EXECUTION_PROFILES)
    required_gates = list(REQUIRED_STAGING_GATES)
    execution_id = sha256_text(
        canonical_json(
            _execution_id_payload(source_tree, required_profiles, required_gates, manifest_path, report_dir)
        )
    )
    reports = [_report_plan(profile, report_dir, manifest_path) for profile in required_profiles]
    payload = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "release": EXECUTION_RELEASE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execution_id": execution_id,
        "manifest_path": manifest_path,
        "report_dir": report_dir,
        "source_tree": source_tree,
        "required_profiles": required_profiles,
        "required_gates": required_gates,
        "reports": reports,
        "aggregate": _aggregate_plan(reports, manifest_path),
    }
    return seal_evidence(payload)


def _valid_sha256(value: Any) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)


def verify_execution_manifest(payload: Any, *, root: Path | None = None) -> dict[str, Any]:
    if not isinstance(payload, dict) or not verify_evidence(payload):
        raise CertificationExecutionError("execution manifest evidence SHA-256 mismatch")
    if payload.get("schema_version") != EXECUTION_SCHEMA_VERSION:
        raise CertificationExecutionError(f"{EXECUTION_RELEASE} execution manifest schema_version must be {EXECUTION_SCHEMA_VERSION}")
    if payload.get("release") != EXECUTION_RELEASE:
        raise CertificationExecutionError(f"execution manifest release must be {EXECUTION_RELEASE}")

    manifest_path = _safe_relative_path(str(payload.get("manifest_path") or ""), "manifest_path")
    report_dir = _safe_relative_path(str(payload.get("report_dir") or ""), "report_dir")
    if manifest_path != DEFAULT_MANIFEST_NAME:
        raise CertificationExecutionError(f"{EXECUTION_RELEASE} manifest_path must be {DEFAULT_MANIFEST_NAME!r}")
    if report_dir != DEFAULT_REPORT_DIR:
        raise CertificationExecutionError(f"{EXECUTION_RELEASE} report_dir must be {DEFAULT_REPORT_DIR!r}")

    source = payload.get("source_tree")
    if not isinstance(source, dict) or not _valid_sha256(source.get("sha256")):
        raise CertificationExecutionError("execution manifest source_tree.sha256 is invalid")
    if not isinstance(source.get("file_count"), int) or source["file_count"] <= 0:
        raise CertificationExecutionError("execution manifest source_tree.file_count must be positive")

    required_profiles = payload.get("required_profiles")
    required_gates = payload.get("required_gates")
    if required_profiles != list(PRODUCTION_EXECUTION_PROFILES):
        raise CertificationExecutionError(f"execution manifest required_profiles do not match the {EXECUTION_RELEASE} production plan")
    if required_gates != list(REQUIRED_STAGING_GATES):
        raise CertificationExecutionError(f"execution manifest required_gates do not match the {EXECUTION_RELEASE} release gate set")

    expected_id = sha256_text(
        canonical_json(
            _execution_id_payload(source, required_profiles, required_gates, manifest_path, report_dir)
        )
    )
    if payload.get("execution_id") != expected_id:
        raise CertificationExecutionError("execution manifest execution_id does not match source/profile/gate/path plan")

    reports = payload.get("reports")
    if not isinstance(reports, list) or len(reports) != len(PRODUCTION_EXECUTION_PROFILES):
        raise CertificationExecutionError("execution manifest report plan is incomplete")
    seen_profiles: set[str] = set()
    seen_paths: set[str] = set()
    covered_gates: set[str] = set()
    normalized_reports: list[dict[str, Any]] = []
    for index, raw in enumerate(reports):
        if not isinstance(raw, dict):
            raise CertificationExecutionError(f"execution manifest reports[{index}] must be an object")
        try:
            profile = normalize_profile(str(raw.get("profile") or ""))
        except ValueError as exc:
            raise CertificationExecutionError(str(exc)) from exc
        if profile not in PRODUCTION_EXECUTION_PROFILES or profile in seen_profiles:
            raise CertificationExecutionError(f"execution manifest has invalid/duplicate production profile {profile!r}")
        expected = _report_plan(profile, report_dir, manifest_path)
        path = str(raw.get("path") or "")
        if raw != expected:
            raise CertificationExecutionError(f"execution manifest report contract for {profile!r} does not match {EXECUTION_RELEASE}")
        if path in seen_paths:
            raise CertificationExecutionError(f"execution manifest has duplicate report path {path!r}")
        seen_profiles.add(profile)
        seen_paths.add(path)
        covered_gates.update(expected["gates"])
        normalized_reports.append(dict(raw))
    if seen_profiles != set(PRODUCTION_EXECUTION_PROFILES):
        raise CertificationExecutionError("execution manifest is missing one or more production profiles")
    if covered_gates != set(REQUIRED_STAGING_GATES):
        raise CertificationExecutionError("execution manifest production profiles do not cover every required gate")

    expected_aggregate = _aggregate_plan(normalized_reports, manifest_path)
    if payload.get("aggregate") != expected_aggregate:
        raise CertificationExecutionError(f"execution manifest aggregate/verification command plan does not match {EXECUTION_RELEASE}")

    if root is not None:
        actual_sha, actual_count = source_tree_fingerprint(root)
        if source != {"sha256": actual_sha, "file_count": actual_count}:
            raise CertificationExecutionError("execution manifest source tree does not match the current repository")

    return {
        **payload,
        "manifest_path": manifest_path,
        "report_dir": report_dir,
        "reports": normalized_reports,
    }


def report_plan_for_profile(manifest: dict[str, Any], profile: str) -> dict[str, Any]:
    normalized = normalize_profile(profile)
    for row in manifest["reports"]:
        if row["profile"] == normalized:
            return row
    raise CertificationExecutionError(f"runner profile {normalized!r} is not part of the production execution manifest")
