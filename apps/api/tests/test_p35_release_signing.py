from __future__ import annotations

import copy
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import rivexis_api.release_signing as release_signing_module
from rivexis_api.certification import seal_evidence
from rivexis_api.certification_execution import PRODUCTION_EXECUTION_PROFILES, build_execution_manifest
from rivexis_api.certification_profiles import PROFILE_GATES, REQUIRED_STAGING_GATES
from rivexis_api.release_certification import aggregate_staging_reports
from rivexis_api.release_signing import (
    ATTESTATION_SCHEMA_VERSION,
    SIGNATURE_ENVELOPE_SCHEMA_VERSION,
    SIGNING_REQUEST_SCHEMA_VERSION,
    ReleaseSigningError,
    assemble_release_attestation,
    build_release_signing_request,
    public_key_fingerprint,
    sign_release_request,
    verify_release_attestation,
    verify_release_signature_envelope,
    verify_release_signing_request,
)
from rivexis_api.release_trust import (
    ReleaseTrustError,
    require_authorized_signer,
    verify_trust_policy,
)
from rivexis_api.version import RELEASE_CODENAME


def _keys(tmp_path: Path, name: str) -> tuple[Path, Path]:
    private = tmp_path / f"{name}-private.pem"
    public = tmp_path / f"{name}-public.pem"
    subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(private)], check=True)
    subprocess.run(["openssl", "pkey", "-in", str(private), "-pubout", "-out", str(public)], check=True)
    return private, public


def _policy(
    tmp_path: Path,
    public_keys: dict[str, tuple[Path, str]],
    *,
    statuses: dict[str, str] | None = None,
    minimum_signatures: int = 2,
    required_roles: list[str] | None = None,
    release_min: int = 24,
    release_max: int | None = 37,
    policy_id: str = "rivexis-release-trust-v3",
    request_ttl_seconds: int = 3600,
    max_certification_age_seconds: int = 86400,
    max_clock_skew_seconds: int = 300,
) -> Path:
    statuses = statuses or {}
    required_roles = required_roles or ["RELEASE_ENGINEERING", "SECURITY"]
    keys = []
    for key_id, (public_key, role) in public_keys.items():
        keys.append(
            {
                "key_id": key_id,
                "role": role,
                "public_key_sha256": public_key_fingerprint(public_key),
                "status": statuses.get(key_id, "ACTIVE"),
                "not_before": "2026-09-01T00:00:00+00:00",
                "not_after": "2026-12-31T23:59:59+00:00",
                "release_min": release_min,
                "release_max": release_max,
            }
        )
    payload = {
        "schema_version": 3,
        "policy_id": policy_id,
        "organization": "Rivexis",
        "signature_algorithm": "Ed25519",
        "quorum": {"minimum_signatures": minimum_signatures, "required_roles": required_roles},
        "ceremony": {
            "request_ttl_seconds": request_ttl_seconds,
            "max_certification_age_seconds": max_certification_age_seconds,
            "max_clock_skew_seconds": max_clock_skew_seconds,
        },
        "keys": keys,
    }
    path = tmp_path / f"{policy_id}.json"
    path.write_text(json.dumps(payload))
    return path


def _staging(manifest: dict, *, profile: str, statuses: dict[str, str]) -> dict:
    merged = {name: "SKIP" for name in REQUIRED_STAGING_GATES}
    merged.update(statuses)
    results = [
        {"name": name, "status": merged[name], "duration_ms": 1, "output_sha256": "b" * 64}
        for name in REQUIRED_STAGING_GATES
    ]
    counts = {status: sum(1 for value in merged.values() if value == status) for status in ("PASS", "FAIL", "SKIP")}
    return seal_evidence(
        {
            "schema_version": 3,
            "release": RELEASE_CODENAME,
            "generated_at": manifest["generated_at"],
            "execution": {"id": manifest["execution_id"], "manifest_evidence_sha256": manifest["evidence_sha256"]},
            "runner": {"profile": profile, "id": f"test-{profile}"},
            "runtime": {"python": "3.13"},
            "source_tree": dict(manifest["source_tree"]),
            "results": results,
            "counts": counts,
        }
    )


def _complete_bundle(repo: Path) -> tuple[dict, dict]:
    (repo / "source.txt").write_text("release source")
    manifest = build_execution_manifest(repo)
    reports = [
        _staging(manifest, profile=profile, statuses={gate: "PASS" for gate in PROFILE_GATES[profile]})
        for profile in PRODUCTION_EXECUTION_PROFILES
    ]
    bundle = aggregate_staging_reports(reports, execution_manifest=manifest)
    assert bundle["certified"] is True
    return manifest, bundle


def _two_signers(tmp_path: Path):
    release_private, release_public = _keys(tmp_path, "release")
    security_private, security_public = _keys(tmp_path, "security")
    private = {"rivexis-release-engineering": release_private, "rivexis-security": security_private}
    public = {"rivexis-release-engineering": release_public, "rivexis-security": security_public}
    policy = _policy(
        tmp_path,
        {
            "rivexis-release-engineering": (release_public, "RELEASE_ENGINEERING"),
            "rivexis-security": (security_public, "SECURITY"),
        },
    )
    return private, public, policy


def _ceremony(repo: Path, artifact: Path, manifest: dict, bundle: dict, private: dict[str, Path], public: dict[str, Path], policy: Path):
    request = build_release_signing_request(repo, artifact, bundle, manifest, policy)
    envelopes = [
        sign_release_request(
            repo,
            request,
            artifact,
            bundle,
            manifest,
            key_id=key_id,
            private_key_path=private_key,
            trust_policy_path=policy,
        )
        for key_id, private_key in private.items()
    ]
    attestation = assemble_release_attestation(repo, request, artifact, bundle, manifest, envelopes, public, policy)
    return request, envelopes, attestation


def test_detached_ceremony_binds_artifact_evidence_policy_and_quorum(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest, bundle = _complete_bundle(repo)
    artifact = tmp_path / "rivexis-p22.zip"
    artifact.write_bytes(b"immutable release bytes")
    private, public, policy = _two_signers(tmp_path)

    request, envelopes, attestation = _ceremony(repo, artifact, manifest, bundle, private, public, policy)
    assert request["schema_version"] == SIGNING_REQUEST_SCHEMA_VERSION == 2
    assert request["release"] == RELEASE_CODENAME == "P37"
    assert request["authorization"] == {"minimum_signatures": 2, "required_roles": ["RELEASE_ENGINEERING", "SECURITY"]}
    assert all(row["schema_version"] == SIGNATURE_ENVELOPE_SCHEMA_VERSION == 1 for row in envelopes)
    assert {row["request_sha256"] for row in envelopes} == {request["request_sha256"]}
    assert attestation["schema_version"] == ATTESTATION_SCHEMA_VERSION == 5
    assert {row["key_id"] for row in attestation["signatures"]} == set(private)
    assert verify_release_signing_request(request, artifact, policy, bundle=bundle, manifest=manifest, root=repo)
    assert verify_release_attestation(
        attestation,
        artifact,
        public,
        policy,
        bundle=bundle,
        manifest=manifest,
        expected_key_ids=set(private),
        expected_policy_id="rivexis-release-trust-v3",
        root=repo,
    )


def test_each_detached_signature_uses_only_one_private_key_and_verifies_independently(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest, bundle = _complete_bundle(repo)
    artifact = tmp_path / "release.zip"
    artifact.write_bytes(b"artifact")
    private, public, policy = _two_signers(tmp_path)
    request = build_release_signing_request(repo, artifact, bundle, manifest, policy)

    for key_id in sorted(private):
        envelope = sign_release_request(
            repo,
            request,
            artifact,
            bundle,
            manifest,
            key_id=key_id,
            private_key_path=private[key_id],
            trust_policy_path=policy,
        )
        assert envelope["key_id"] == key_id
        assert verify_release_signature_envelope(request, envelope, public[key_id], policy, root=repo)


def test_assembly_refuses_insufficient_quorum_and_missing_required_role(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest, bundle = _complete_bundle(repo)
    artifact = tmp_path / "release.zip"
    artifact.write_bytes(b"artifact")
    private, public, policy = _two_signers(tmp_path)
    request = build_release_signing_request(repo, artifact, bundle, manifest, policy)
    one = sign_release_request(
        repo,
        request,
        artifact,
        bundle,
        manifest,
        key_id="rivexis-release-engineering",
        private_key_path=private["rivexis-release-engineering"],
        trust_policy_path=policy,
    )
    with pytest.raises(ReleaseSigningError, match="quorum not met"):
        assemble_release_attestation(repo, request, artifact, bundle, manifest, [one], public, policy)

    a_private, a_public = _keys(tmp_path, "release-a")
    b_private, b_public = _keys(tmp_path, "release-b")
    _, security_public = _keys(tmp_path, "security-extra")
    role_policy = _policy(
        tmp_path,
        {
            "release-a": (a_public, "RELEASE_ENGINEERING"),
            "release-b": (b_public, "RELEASE_ENGINEERING"),
            "security": (security_public, "SECURITY"),
        },
        policy_id="rivexis-release-trust-v3-role-test",
    )
    role_request = build_release_signing_request(repo, artifact, bundle, manifest, role_policy)
    role_envs = [
        sign_release_request(repo, role_request, artifact, bundle, manifest, key_id="release-a", private_key_path=a_private, trust_policy_path=role_policy),
        sign_release_request(repo, role_request, artifact, bundle, manifest, key_id="release-b", private_key_path=b_private, trust_policy_path=role_policy),
    ]
    with pytest.raises(ReleaseSigningError, match="missing required roles"):
        assemble_release_attestation(
            repo,
            role_request,
            artifact,
            bundle,
            manifest,
            role_envs,
            {"release-a": a_public, "release-b": b_public},
            role_policy,
        )


def test_request_and_signature_tampering_fail_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest, bundle = _complete_bundle(repo)
    artifact = tmp_path / "release.zip"
    artifact.write_bytes(b"artifact")
    private, public, policy = _two_signers(tmp_path)
    request, envelopes, attestation = _ceremony(repo, artifact, manifest, bundle, private, public, policy)

    request_tampered = copy.deepcopy(request)
    request_tampered["artifact"]["size_bytes"] += 1
    assert not verify_release_signing_request(request_tampered, artifact, policy, bundle=bundle, manifest=manifest, root=repo)

    signature_tampered = copy.deepcopy(attestation)
    signature_tampered["signatures"][0]["value_base64"] = "A" * 88
    assert not verify_release_attestation(signature_tampered, artifact, public, policy, bundle=bundle, manifest=manifest, root=repo)

    role_tampered = copy.deepcopy(attestation)
    role_tampered["signatures"][0]["role"] = "SECURITY"
    assert not verify_release_attestation(role_tampered, artifact, public, policy, bundle=bundle, manifest=manifest, root=repo)

    wrong_request = copy.deepcopy(envelopes[0])
    wrong_request["request_sha256"] = "0" * 64
    assert not verify_release_signature_envelope(request, wrong_request, public[wrong_request["key_id"]], policy, root=repo)


def test_attestation_rejects_artifact_tampering_wrong_key_or_dropped_signature(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest, bundle = _complete_bundle(repo)
    artifact = tmp_path / "release.zip"
    artifact.write_bytes(b"original")
    private, public, policy = _two_signers(tmp_path)
    _, _, attestation = _ceremony(repo, artifact, manifest, bundle, private, public, policy)

    artifact.write_bytes(b"tampered")
    assert not verify_release_attestation(attestation, artifact, public, policy, bundle=bundle, manifest=manifest, root=repo)
    artifact.write_bytes(b"original")

    _, wrong_public = _keys(tmp_path, "wrong")
    wrong_keys = dict(public)
    wrong_keys["rivexis-security"] = wrong_public
    assert not verify_release_attestation(attestation, artifact, wrong_keys, policy, bundle=bundle, manifest=manifest, root=repo)

    dropped = copy.deepcopy(attestation)
    dropped["signatures"].pop()
    assert not verify_release_attestation(dropped, artifact, public, policy, bundle=bundle, manifest=manifest, root=repo)


def test_request_creation_refuses_incomplete_bundle(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "source.txt").write_text("release source")
    manifest = build_execution_manifest(repo)
    report = _staging(manifest, profile="local", statuses={"otlp-local": "PASS"})
    bundle = aggregate_staging_reports([report], execution_manifest=manifest)
    artifact = tmp_path / "release.zip"
    artifact.write_bytes(b"artifact")
    _, _, policy = _two_signers(tmp_path)
    with pytest.raises(ReleaseSigningError, match="complete valid certification bundle"):
        build_release_signing_request(repo, artifact, bundle, manifest, policy)


def test_artifact_private_key_and_policy_must_remain_outside_repository(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest, bundle = _complete_bundle(repo)
    private, public, policy = _two_signers(tmp_path)

    inside_artifact = repo / "release.zip"
    inside_artifact.write_bytes(b"artifact")
    with pytest.raises(ReleaseSigningError, match="release artifact must remain outside"):
        build_release_signing_request(repo, inside_artifact, bundle, manifest, policy)
    inside_artifact.unlink()

    artifact = tmp_path / "release.zip"
    artifact.write_bytes(b"artifact")
    request = build_release_signing_request(repo, artifact, bundle, manifest, policy)
    inside_private = repo / "private.pem"
    inside_private.write_bytes(private["rivexis-release-engineering"].read_bytes())
    manifest, bundle = _complete_bundle(repo)
    request = build_release_signing_request(repo, artifact, bundle, manifest, policy)
    with pytest.raises(ReleaseSigningError, match="private key rivexis-release-engineering must remain outside"):
        sign_release_request(
            repo,
            request,
            artifact,
            bundle,
            manifest,
            key_id="rivexis-release-engineering",
            private_key_path=inside_private,
            trust_policy_path=policy,
        )

    inside_policy = repo / "trust-policy.json"
    inside_policy.write_bytes(policy.read_bytes())
    manifest, bundle = _complete_bundle(repo)
    with pytest.raises(ReleaseSigningError, match="trust policy must remain outside"):
        build_release_signing_request(repo, artifact, bundle, manifest, inside_policy)
    assert all(path.is_file() for path in public.values())


def test_revoked_signer_and_policy_substitution_are_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest, bundle = _complete_bundle(repo)
    artifact = tmp_path / "release.zip"
    artifact.write_bytes(b"artifact")
    private, public, active_policy = _two_signers(tmp_path)
    request, _, attestation = _ceremony(repo, artifact, manifest, bundle, private, public, active_policy)

    revoked_policy = _policy(
        tmp_path,
        {
            "rivexis-release-engineering": (public["rivexis-release-engineering"], "RELEASE_ENGINEERING"),
            "rivexis-security": (public["rivexis-security"], "SECURITY"),
        },
        statuses={"rivexis-security": "REVOKED"},
        policy_id="rivexis-release-trust-v3-revoked",
    )
    assert not verify_release_attestation(attestation, artifact, public, revoked_policy, bundle=bundle, manifest=manifest, root=repo)

    payload = json.loads(active_policy.read_text())
    payload["organization"] = "Attacker"
    substituted = tmp_path / "substituted-policy.json"
    substituted.write_text(json.dumps(payload))
    assert not verify_release_signing_request(request, artifact, substituted, bundle=bundle, manifest=manifest, root=repo)


def test_signature_envelope_is_bound_to_signing_time_and_key_authorization(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest, bundle = _complete_bundle(repo)
    artifact = tmp_path / "release.zip"
    artifact.write_bytes(b"artifact")
    private, public, policy = _two_signers(tmp_path)
    request = build_release_signing_request(repo, artifact, bundle, manifest, policy)
    envelope = sign_release_request(
        repo,
        request,
        artifact,
        bundle,
        manifest,
        key_id="rivexis-security",
        private_key_path=private["rivexis-security"],
        trust_policy_path=policy,
    )
    tampered = copy.deepcopy(envelope)
    tampered["signed_at"] = "2027-01-01T00:00:00+00:00"
    assert not verify_release_signature_envelope(request, tampered, public["rivexis-security"], policy, root=repo)


def test_trust_policy_enforces_release_range_and_validity(tmp_path: Path) -> None:
    _, release_public = _keys(tmp_path, "release")
    _, security_public = _keys(tmp_path, "security")
    policy = {
        "schema_version": 3,
        "policy_id": "rivexis-release-trust-v3",
        "organization": "Rivexis",
        "signature_algorithm": "Ed25519",
        "quorum": {"minimum_signatures": 2, "required_roles": ["RELEASE_ENGINEERING", "SECURITY"]},
        "ceremony": {
            "request_ttl_seconds": 3600,
            "max_certification_age_seconds": 86400,
            "max_clock_skew_seconds": 300,
        },
        "keys": [
            {
                "key_id": "release",
                "role": "RELEASE_ENGINEERING",
                "public_key_sha256": public_key_fingerprint(release_public),
                "status": "ACTIVE",
                "not_before": "2026-09-01T00:00:00+00:00",
                "not_after": "2026-10-01T00:00:00+00:00",
                "release_min": 20,
                "release_max": 20,
            },
            {
                "key_id": "security",
                "role": "SECURITY",
                "public_key_sha256": public_key_fingerprint(security_public),
                "status": "ACTIVE",
                "not_before": "2026-09-01T00:00:00+00:00",
                "not_after": "2026-10-01T00:00:00+00:00",
                "release_min": 20,
                "release_max": 20,
            },
        ],
    }
    verify_trust_policy(policy)
    with pytest.raises(ReleaseTrustError, match="above key authorization range"):
        require_authorized_signer(
            policy,
            key_id="release",
            public_key_sha256=public_key_fingerprint(release_public),
            release="P35",
            signed_at="2026-09-11T00:00:00+00:00",
        )
    with pytest.raises(ReleaseTrustError, match="outside key validity window"):
        require_authorized_signer(
            policy,
            key_id="release",
            public_key_sha256=public_key_fingerprint(release_public),
            release="P20",
            signed_at="2026-10-02T00:00:00+00:00",
        )


def test_trust_policy_rejects_duplicate_keys_and_invalid_quorum(tmp_path: Path) -> None:
    _, release_public = _keys(tmp_path, "release")
    _, security_public = _keys(tmp_path, "security")
    base = {
        "schema_version": 3,
        "policy_id": "rivexis-release-trust-v3",
        "organization": "Rivexis",
        "signature_algorithm": "Ed25519",
        "quorum": {"minimum_signatures": 2, "required_roles": ["RELEASE_ENGINEERING", "SECURITY"]},
        "ceremony": {
            "request_ttl_seconds": 3600,
            "max_certification_age_seconds": 86400,
            "max_clock_skew_seconds": 300,
        },
        "keys": [
            {
                "key_id": "release",
                "role": "RELEASE_ENGINEERING",
                "public_key_sha256": public_key_fingerprint(release_public),
                "status": "ACTIVE",
                "not_before": "2026-01-01T00:00:00+00:00",
                "not_after": None,
                "release_min": 20,
                "release_max": None,
            },
            {
                "key_id": "security",
                "role": "SECURITY",
                "public_key_sha256": public_key_fingerprint(security_public),
                "status": "ACTIVE",
                "not_before": "2026-01-01T00:00:00+00:00",
                "not_after": None,
                "release_min": 20,
                "release_max": None,
            },
        ],
    }
    duplicate = copy.deepcopy(base)
    duplicate["keys"][1]["key_id"] = "release"
    with pytest.raises(ReleaseTrustError, match="duplicate key_id"):
        verify_trust_policy(duplicate)
    weak = copy.deepcopy(base)
    weak["quorum"]["minimum_signatures"] = 1
    with pytest.raises(ReleaseTrustError, match=">= 2"):
        verify_trust_policy(weak)
    missing_role = copy.deepcopy(base)
    missing_role["quorum"]["required_roles"] = ["RELEASE_ENGINEERING", "COMPLIANCE"]
    with pytest.raises(ReleaseTrustError, match="not backed"):
        verify_trust_policy(missing_role)


def _freeze_release_time(monkeypatch: pytest.MonkeyPatch, target: datetime) -> None:
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = target.astimezone(timezone.utc)
            if tz is None:
                return value.replace(tzinfo=None)
            return value.astimezone(tz)

    monkeypatch.setattr(release_signing_module, "datetime", FrozenDateTime)


def test_signing_request_has_unique_time_bounded_ceremony_identity(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest, bundle = _complete_bundle(repo)
    artifact = tmp_path / "release.zip"
    artifact.write_bytes(b"artifact")
    _, _, policy = _two_signers(tmp_path)

    first = build_release_signing_request(repo, artifact, bundle, manifest, policy)
    second = build_release_signing_request(repo, artifact, bundle, manifest, policy)
    assert first["ceremony"]["id"] != second["ceremony"]["id"]
    assert len(first["ceremony"]["id"]) == 64
    int(first["ceremony"]["id"], 16)
    created = datetime.fromisoformat(first["created_at"])
    expires = datetime.fromisoformat(first["ceremony"]["expires_at"])
    assert expires - created == timedelta(seconds=3600)
    assert first["ceremony"]["max_certification_age_seconds"] == 86400
    assert first["request_sha256"] != second["request_sha256"]


def test_expired_request_blocks_new_signatures_but_historical_attestation_remains_verifiable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest, bundle = _complete_bundle(repo)
    artifact = tmp_path / "release.zip"
    artifact.write_bytes(b"artifact")
    private, public, policy = _two_signers(tmp_path)
    request, _, attestation = _ceremony(repo, artifact, manifest, bundle, private, public, policy)

    expired_at = datetime.fromisoformat(request["ceremony"]["expires_at"]) + timedelta(seconds=301)
    _freeze_release_time(monkeypatch, expired_at)
    assert not verify_release_signing_request(request, artifact, policy, bundle=bundle, manifest=manifest, root=repo)
    with pytest.raises(ReleaseSigningError, match="expired"):
        sign_release_request(
            repo,
            request,
            artifact,
            bundle,
            manifest,
            key_id="rivexis-release-engineering",
            private_key_path=private["rivexis-release-engineering"],
            trust_policy_path=policy,
        )
    assert verify_release_attestation(attestation, artifact, public, policy, bundle=bundle, manifest=manifest, root=repo)


def test_signer_refuses_certification_that_becomes_stale_during_open_ceremony(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest, bundle = _complete_bundle(repo)
    artifact = tmp_path / "release.zip"
    artifact.write_bytes(b"artifact")
    release_private, release_public = _keys(tmp_path, "release-freshness")
    _, security_public = _keys(tmp_path, "security-freshness")
    policy = _policy(
        tmp_path,
        {
            "release-freshness": (release_public, "RELEASE_ENGINEERING"),
            "security-freshness": (security_public, "SECURITY"),
        },
        policy_id="rivexis-release-trust-v3-freshness",
        request_ttl_seconds=7200,
        max_certification_age_seconds=3600,
        max_clock_skew_seconds=0,
    )
    request = build_release_signing_request(repo, artifact, bundle, manifest, policy)
    future = datetime.fromisoformat(request["created_at"]) + timedelta(seconds=4000)
    _freeze_release_time(monkeypatch, future)
    with pytest.raises(ReleaseSigningError, match="stale"):
        sign_release_request(
            repo,
            request,
            artifact,
            bundle,
            manifest,
            key_id="release-freshness",
            private_key_path=release_private,
            trust_policy_path=policy,
        )


def test_request_creation_refuses_stale_certification_campaign(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "source.txt").write_text("release source")
    manifest = build_execution_manifest(repo)
    manifest["generated_at"] = "2026-09-01T00:00:00+00:00"
    manifest = seal_evidence(manifest)
    reports = [
        _staging(manifest, profile=profile, statuses={gate: "PASS" for gate in PROFILE_GATES[profile]})
        for profile in PRODUCTION_EXECUTION_PROFILES
    ]
    bundle = aggregate_staging_reports(reports, execution_manifest=manifest)
    artifact = tmp_path / "release.zip"
    artifact.write_bytes(b"artifact")
    release_private, release_public = _keys(tmp_path, "release-stale")
    _, security_public = _keys(tmp_path, "security-stale")
    policy = _policy(
        tmp_path,
        {
            "release-stale": (release_public, "RELEASE_ENGINEERING"),
            "security-stale": (security_public, "SECURITY"),
        },
        policy_id="rivexis-release-trust-v3-stale",
        max_certification_age_seconds=3600,
    )
    assert release_private.is_file()
    with pytest.raises(ReleaseSigningError, match="stale"):
        build_release_signing_request(repo, artifact, bundle, manifest, policy)


def test_trust_policy_rejects_unsafe_ceremony_windows(tmp_path: Path) -> None:
    _, release_public = _keys(tmp_path, "release-policy-window")
    _, security_public = _keys(tmp_path, "security-policy-window")
    policy_path = _policy(
        tmp_path,
        {
            "release": (release_public, "RELEASE_ENGINEERING"),
            "security": (security_public, "SECURITY"),
        },
        policy_id="rivexis-release-trust-v3-window",
    )
    base = json.loads(policy_path.read_text())
    weak_ttl = copy.deepcopy(base)
    weak_ttl["ceremony"]["request_ttl_seconds"] = 60
    with pytest.raises(ReleaseTrustError, match="request_ttl_seconds"):
        verify_trust_policy(weak_ttl)
    excessive_age = copy.deepcopy(base)
    excessive_age["ceremony"]["max_certification_age_seconds"] = 604801
    with pytest.raises(ReleaseTrustError, match="max_certification_age_seconds"):
        verify_trust_policy(excessive_age)
    excessive_skew = copy.deepcopy(base)
    excessive_skew["ceremony"]["max_clock_skew_seconds"] = 301
    with pytest.raises(ReleaseTrustError, match="max_clock_skew_seconds"):
        verify_trust_policy(excessive_skew)
