from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import secrets
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .certification import canonical_json, sha256_bytes
from .certification_execution import CertificationExecutionError, verify_execution_manifest
from .release_certification import verify_release_bundle
from .release_trust import (
    ReleaseTrustError,
    ensure_external_trust_policy,
    require_authorized_signer,
    trust_policy_fingerprint,
    verify_trust_policy,
)
from .version import RELEASE_CODENAME

SIGNING_REQUEST_SCHEMA_VERSION = 2
SIGNATURE_ENVELOPE_SCHEMA_VERSION = 1
ATTESTATION_SCHEMA_VERSION = 5
SIGNATURE_ALGORITHM = "Ed25519"
_KEY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,127}$")
_CEREMONY_ID_RE = re.compile(r"^[0-9a-f]{64}$")


class ReleaseSigningError(ValueError):
    """Raised when release signing ceremony creation, signing, assembly or verification fails closed."""


def _run_openssl(args: list[str], *, input_bytes: bytes | None = None) -> bytes:
    try:
        result = subprocess.run(
            ["openssl", *args],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ReleaseSigningError("OpenSSL is required for Ed25519 release attestation") from exc
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ReleaseSigningError(f"OpenSSL command failed: {detail or 'unknown error'}")
    return result.stdout


def _validate_key_id(value: str) -> str:
    key_id = value.strip()
    if not _KEY_ID_RE.fullmatch(key_id):
        raise ReleaseSigningError("key_id must be 1-128 safe identifier characters")
    return key_id


def _require_file(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ReleaseSigningError(f"{label} does not exist or is not a file: {resolved}")
    return resolved


def _ensure_outside_repository(path: Path, root: Path, label: str) -> None:
    resolved_root = root.resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError:
        return
    raise ReleaseSigningError(f"{label} must remain outside the Rivexis repository")


def _load_trust_policy(path: Path, root: Path) -> dict[str, Any]:
    try:
        policy_path = ensure_external_trust_policy(path, root)
        raw = json.loads(policy_path.read_text())
        return verify_trust_policy(raw)
    except (OSError, json.JSONDecodeError, ReleaseTrustError) as exc:
        raise ReleaseSigningError(f"invalid external release trust policy: {exc}") from exc


def _public_der_from_private(private_key: Path) -> bytes:
    return _run_openssl(["pkey", "-in", str(private_key), "-pubout", "-outform", "DER"])


def _public_der(public_key: Path) -> bytes:
    return _run_openssl(["pkey", "-pubin", "-in", str(public_key), "-outform", "DER"])


def public_key_fingerprint(public_key: Path) -> str:
    key = _require_file(public_key, "trusted public key")
    return sha256_bytes(_public_der(key))


def private_key_public_fingerprint(private_key: Path) -> str:
    key = _require_file(private_key, "release signing private key")
    return sha256_bytes(_public_der_from_private(key))


def _sign_ed25519(private_key: Path, message: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="rivexis-sign-") as tmp:
        message_path = Path(tmp) / "payload.bin"
        signature_path = Path(tmp) / "signature.bin"
        message_path.write_bytes(message)
        _run_openssl(
            [
                "pkeyutl",
                "-sign",
                "-rawin",
                "-inkey",
                str(private_key),
                "-in",
                str(message_path),
                "-out",
                str(signature_path),
            ]
        )
        signature = signature_path.read_bytes()
    if len(signature) != 64:
        raise ReleaseSigningError(f"unexpected Ed25519 signature length: {len(signature)}")
    return signature


def _verify_ed25519(public_key: Path, message: bytes, signature: bytes) -> bool:
    with tempfile.TemporaryDirectory(prefix="rivexis-verify-") as tmp:
        message_path = Path(tmp) / "payload.bin"
        signature_path = Path(tmp) / "signature.bin"
        message_path.write_bytes(message)
        signature_path.write_bytes(signature)
        try:
            _run_openssl(
                [
                    "pkeyutl",
                    "-verify",
                    "-rawin",
                    "-pubin",
                    "-inkey",
                    str(public_key),
                    "-in",
                    str(message_path),
                    "-sigfile",
                    str(signature_path),
                ]
            )
        except ReleaseSigningError:
            return False
    return True


def _file_digest(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    if not data:
        raise ReleaseSigningError("release artifact must not be empty")
    return hashlib.sha256(data).hexdigest(), len(data)


def _timestamp_dt(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ReleaseSigningError(f"{label} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReleaseSigningError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReleaseSigningError(f"{label} must include a timezone offset")
    return parsed.astimezone(timezone.utc)


def _parse_timestamp(value: Any, label: str) -> str:
    return _timestamp_dt(value, label).isoformat()


def _certification_time_summary(bundle: dict[str, Any], manifest: dict[str, Any]) -> dict[str, str]:
    inputs = bundle.get("input_reports")
    if not isinstance(inputs, list) or not inputs:
        raise ReleaseSigningError("release certification bundle must contain input report timestamps")
    report_times = [
        _timestamp_dt(item.get("generated_at"), f"certification input report[{index}] generated_at")
        for index, item in enumerate(inputs)
        if isinstance(item, dict)
    ]
    if len(report_times) != len(inputs):
        raise ReleaseSigningError("release certification input reports must be objects")
    bundle_time = _timestamp_dt(bundle.get("generated_at"), "release certification bundle generated_at")
    manifest_time = _timestamp_dt(manifest.get("generated_at"), "certification execution manifest generated_at")
    return {
        "manifest_generated_at": manifest_time.isoformat(),
        "oldest_report_generated_at": min(report_times).isoformat(),
        "newest_report_generated_at": max(report_times).isoformat(),
        "bundle_generated_at": bundle_time.isoformat(),
    }


def _validate_certification_freshness(
    certification: Mapping[str, Any],
    ceremony: Mapping[str, Any],
    *,
    reference_time: datetime,
) -> None:
    oldest = _timestamp_dt(certification.get("oldest_report_generated_at"), "oldest certification report generated_at")
    newest = _timestamp_dt(certification.get("newest_report_generated_at"), "newest certification report generated_at")
    bundle_time = _timestamp_dt(certification.get("bundle_generated_at"), "release certification bundle generated_at")
    manifest_time = _timestamp_dt(certification.get("manifest_generated_at"), "certification execution manifest generated_at")
    max_age = timedelta(seconds=int(ceremony["max_certification_age_seconds"]))
    skew = timedelta(seconds=int(ceremony["max_clock_skew_seconds"]))
    if oldest > newest:
        raise ReleaseSigningError("certification report timestamp range is invalid")
    if manifest_time > oldest + skew:
        raise ReleaseSigningError("certification reports predate the execution manifest")
    if newest > bundle_time + skew:
        raise ReleaseSigningError("release certification bundle predates one or more input reports")
    if max(manifest_time, newest, bundle_time) > reference_time + skew:
        raise ReleaseSigningError("certification evidence is dated in the future beyond allowed clock skew")
    if reference_time - oldest > max_age + skew:
        raise ReleaseSigningError("release certification evidence is stale for the signing ceremony")


def _validate_ceremony_block(
    request: Mapping[str, Any],
    trust_policy: Mapping[str, Any],
    *,
    require_open: bool,
) -> dict[str, Any]:
    ceremony = request.get("ceremony")
    if not isinstance(ceremony, dict) or set(ceremony) != {
        "id",
        "expires_at",
        "request_ttl_seconds",
        "max_certification_age_seconds",
        "max_clock_skew_seconds",
    }:
        raise ReleaseSigningError("release signing request ceremony block is malformed")
    ceremony_id = str(ceremony.get("id") or "")
    if not _CEREMONY_ID_RE.fullmatch(ceremony_id):
        raise ReleaseSigningError("release signing request ceremony id must be a 256-bit lowercase hex value")
    policy_ceremony = trust_policy["ceremony"]
    for field in ("request_ttl_seconds", "max_certification_age_seconds", "max_clock_skew_seconds"):
        if ceremony.get(field) != policy_ceremony.get(field):
            raise ReleaseSigningError(f"release signing request ceremony {field} does not match trust policy")
    created = _timestamp_dt(request.get("created_at"), "release signing request created_at")
    expires = _timestamp_dt(ceremony.get("expires_at"), "release signing request expires_at")
    expected_expiry = created + timedelta(seconds=int(ceremony["request_ttl_seconds"]))
    if expires != expected_expiry:
        raise ReleaseSigningError("release signing request expiry does not match trust-policy TTL")
    if require_open:
        now = datetime.now(timezone.utc)
        skew = timedelta(seconds=int(ceremony["max_clock_skew_seconds"]))
        if now < created - skew:
            raise ReleaseSigningError("release signing request is not active yet")
        if now > expires + skew:
            raise ReleaseSigningError("release signing request has expired")
    return {**ceremony, "id": ceremony_id, "expires_at": expires.isoformat()}


def _validate_signature_time(request: Mapping[str, Any], signed_at: str) -> None:
    ceremony = request.get("ceremony")
    certification = request.get("certification")
    if not isinstance(ceremony, dict) or not isinstance(certification, dict):
        raise ReleaseSigningError("release signing request is missing ceremony/certification timing metadata")
    signed = _timestamp_dt(signed_at, "detached release signature signed_at")
    created = _timestamp_dt(request.get("created_at"), "release signing request created_at")
    expires = _timestamp_dt(ceremony.get("expires_at"), "release signing request expires_at")
    skew = timedelta(seconds=int(ceremony["max_clock_skew_seconds"]))
    if signed < created - skew:
        raise ReleaseSigningError("detached release signature predates the signing ceremony")
    if signed > expires + skew:
        raise ReleaseSigningError("detached release signature was produced after the signing ceremony expired")
    _validate_certification_freshness(certification, ceremony, reference_time=signed)


def _request_body(
    *,
    artifact: Path,
    artifact_sha256: str,
    artifact_size: int,
    bundle: dict[str, Any],
    manifest: dict[str, Any],
    trust_policy: dict[str, Any],
    created_at: str,
    ceremony_id: str,
) -> dict[str, Any]:
    quorum = trust_policy["quorum"]
    ceremony_policy = trust_policy["ceremony"]
    created = _timestamp_dt(created_at, "release signing request created_at")
    expires = created + timedelta(seconds=int(ceremony_policy["request_ttl_seconds"]))
    certification_times = _certification_time_summary(bundle, manifest)
    ceremony = {
        "id": ceremony_id,
        "expires_at": expires.isoformat(),
        "request_ttl_seconds": ceremony_policy["request_ttl_seconds"],
        "max_certification_age_seconds": ceremony_policy["max_certification_age_seconds"],
        "max_clock_skew_seconds": ceremony_policy["max_clock_skew_seconds"],
    }
    certification = {
        "bundle_evidence_sha256": bundle["evidence_sha256"],
        "execution_id": manifest["execution_id"],
        "manifest_evidence_sha256": manifest["evidence_sha256"],
        "certified": True,
        **certification_times,
    }
    _validate_certification_freshness(certification, ceremony, reference_time=created)
    return {
        "schema_version": SIGNING_REQUEST_SCHEMA_VERSION,
        "release": RELEASE_CODENAME,
        "created_at": created.isoformat(),
        "ceremony": ceremony,
        "artifact": {
            "name": artifact.name,
            "sha256": artifact_sha256,
            "size_bytes": artifact_size,
        },
        "source_tree": dict(bundle["source_tree"]),
        "certification": certification,
        "trust": {
            "policy_id": trust_policy["policy_id"],
            "organization": trust_policy["organization"],
            "policy_sha256": trust_policy_fingerprint(trust_policy),
        },
        "authorization": {
            "minimum_signatures": quorum["minimum_signatures"],
            "required_roles": list(quorum["required_roles"]),
        },
    }


def build_release_signing_request(
    root: Path,
    artifact_path: Path,
    bundle: dict[str, Any],
    manifest: dict[str, Any],
    trust_policy_path: Path,
) -> dict[str, Any]:
    """Create a sealed release request containing no private-key material."""
    root = root.resolve()
    artifact = _require_file(artifact_path, "release artifact")
    _ensure_outside_repository(artifact, root, "release artifact")
    trust_policy = _load_trust_policy(trust_policy_path, root)
    try:
        verified_manifest = verify_execution_manifest(manifest, root=root)
    except CertificationExecutionError as exc:
        raise ReleaseSigningError(str(exc)) from exc
    if not verify_release_bundle(
        bundle,
        expected_release=RELEASE_CODENAME,
        require_complete=True,
        execution_manifest=verified_manifest,
    ):
        raise ReleaseSigningError("release signing request requires a complete valid certification bundle")
    artifact_sha256, artifact_size = _file_digest(artifact)
    body = _request_body(
        artifact=artifact,
        artifact_sha256=artifact_sha256,
        artifact_size=artifact_size,
        bundle=bundle,
        manifest=verified_manifest,
        trust_policy=trust_policy,
        created_at=datetime.now(timezone.utc).isoformat(),
        ceremony_id=secrets.token_hex(32),
    )
    return {**body, "request_sha256": sha256_bytes(canonical_json(body).encode("utf-8"))}


def _verify_signing_request_or_raise(
    payload: Any,
    artifact_path: Path,
    trust_policy_path: Path,
    *,
    bundle: dict[str, Any],
    manifest: dict[str, Any],
    root: Path,
    require_open: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    if not isinstance(payload, dict):
        raise ReleaseSigningError("release signing request must be an object")
    expected_fields = {
        "schema_version",
        "release",
        "created_at",
        "ceremony",
        "artifact",
        "source_tree",
        "certification",
        "trust",
        "authorization",
        "request_sha256",
    }
    if set(payload) != expected_fields or payload.get("schema_version") != SIGNING_REQUEST_SCHEMA_VERSION:
        raise ReleaseSigningError("unsupported or malformed release signing request schema")
    if payload.get("release") != RELEASE_CODENAME:
        raise ReleaseSigningError("release signing request release does not match runtime release")
    _parse_timestamp(payload.get("created_at"), "release signing request created_at")
    body = dict(payload)
    supplied_hash = body.pop("request_sha256", None)
    expected_hash = sha256_bytes(canonical_json(body).encode("utf-8"))
    if supplied_hash != expected_hash:
        raise ReleaseSigningError("release signing request seal mismatch")

    root = root.resolve()
    artifact = _require_file(artifact_path, "release artifact")
    _ensure_outside_repository(artifact, root, "release artifact")
    trust_policy = _load_trust_policy(trust_policy_path, root)
    ceremony = _validate_ceremony_block(payload, trust_policy, require_open=require_open)
    try:
        verified_manifest = verify_execution_manifest(manifest, root=root)
    except CertificationExecutionError as exc:
        raise ReleaseSigningError(str(exc)) from exc
    if not verify_release_bundle(
        bundle,
        expected_release=RELEASE_CODENAME,
        require_complete=True,
        execution_manifest=verified_manifest,
    ):
        raise ReleaseSigningError("release signing request requires a complete valid certification bundle")

    artifact_sha256, artifact_size = _file_digest(artifact)
    if payload.get("artifact") != {
        "name": artifact.name,
        "sha256": artifact_sha256,
        "size_bytes": artifact_size,
    }:
        raise ReleaseSigningError("release signing request artifact binding mismatch")
    if payload.get("source_tree") != bundle.get("source_tree"):
        raise ReleaseSigningError("release signing request source-tree binding mismatch")
    expected_certification = {
        "bundle_evidence_sha256": bundle.get("evidence_sha256"),
        "execution_id": verified_manifest.get("execution_id"),
        "manifest_evidence_sha256": verified_manifest.get("evidence_sha256"),
        "certified": True,
        **_certification_time_summary(bundle, verified_manifest),
    }
    if payload.get("certification") != expected_certification:
        raise ReleaseSigningError("release signing request certification binding mismatch")
    _validate_certification_freshness(
        expected_certification,
        ceremony,
        reference_time=_timestamp_dt(payload.get("created_at"), "release signing request created_at"),
    )
    expected_trust = {
        "policy_id": trust_policy.get("policy_id"),
        "organization": trust_policy.get("organization"),
        "policy_sha256": trust_policy_fingerprint(trust_policy),
    }
    if payload.get("trust") != expected_trust:
        raise ReleaseSigningError("release signing request trust-policy binding mismatch")
    quorum = trust_policy["quorum"]
    if payload.get("authorization") != {
        "minimum_signatures": quorum["minimum_signatures"],
        "required_roles": list(quorum["required_roles"]),
    }:
        raise ReleaseSigningError("release signing request quorum binding mismatch")
    return trust_policy, verified_manifest, expected_hash


def verify_release_signing_request(
    payload: Any,
    artifact_path: Path,
    trust_policy_path: Path,
    *,
    bundle: dict[str, Any],
    manifest: dict[str, Any],
    root: Path,
) -> bool:
    try:
        _verify_signing_request_or_raise(
            payload,
            artifact_path,
            trust_policy_path,
            bundle=bundle,
            manifest=manifest,
            root=root,
            require_open=True,
        )
    except ReleaseSigningError:
        return False
    return True


def sign_release_request(
    root: Path,
    request: dict[str, Any],
    artifact_path: Path,
    bundle: dict[str, Any],
    manifest: dict[str, Any],
    *,
    key_id: str,
    private_key_path: Path,
    trust_policy_path: Path,
) -> dict[str, Any]:
    """Sign one sealed request with exactly one externally held private key."""
    trust_policy, _, request_sha256 = _verify_signing_request_or_raise(
        request,
        artifact_path,
        trust_policy_path,
        bundle=bundle,
        manifest=manifest,
        root=root,
        require_open=True,
    )
    key_id = _validate_key_id(key_id)
    private_key = _require_file(private_key_path, f"release signing private key {key_id}")
    _ensure_outside_repository(private_key, root.resolve(), f"release signing private key {key_id}")
    fingerprint = private_key_public_fingerprint(private_key)
    signed_at = datetime.now(timezone.utc).isoformat()
    _validate_signature_time(request, signed_at)
    try:
        authorized = require_authorized_signer(
            trust_policy,
            key_id=key_id,
            public_key_sha256=fingerprint,
            release=RELEASE_CODENAME,
            signed_at=signed_at,
        )
    except ReleaseTrustError as exc:
        raise ReleaseSigningError(f"release signer is not authorized by trust policy: {exc}") from exc
    statement = {
        "schema_version": SIGNATURE_ENVELOPE_SCHEMA_VERSION,
        "release": RELEASE_CODENAME,
        "request_sha256": request_sha256,
        "key_id": key_id,
        "role": str(authorized["role"]),
        "public_key_sha256": fingerprint,
        "signature_algorithm": SIGNATURE_ALGORITHM,
        "signed_at": signed_at,
    }
    message = canonical_json(statement).encode("utf-8")
    signature = _sign_ed25519(private_key, message)
    return {
        **statement,
        "signed_payload_sha256": sha256_bytes(message),
        "value_base64": base64.b64encode(signature).decode("ascii"),
    }


def _verify_signature_envelope_or_raise(
    request: dict[str, Any],
    envelope: Any,
    public_key_path: Path,
    trust_policy: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        raise ReleaseSigningError("detached release signature must be an object")
    expected_fields = {
        "schema_version",
        "release",
        "request_sha256",
        "key_id",
        "role",
        "public_key_sha256",
        "signature_algorithm",
        "signed_at",
        "signed_payload_sha256",
        "value_base64",
    }
    if set(envelope) != expected_fields or envelope.get("schema_version") != SIGNATURE_ENVELOPE_SCHEMA_VERSION:
        raise ReleaseSigningError("unsupported or malformed detached release signature schema")
    if envelope.get("release") != RELEASE_CODENAME:
        raise ReleaseSigningError("detached release signature release mismatch")
    if envelope.get("request_sha256") != request.get("request_sha256"):
        raise ReleaseSigningError("detached release signature targets a different signing request")
    if envelope.get("signature_algorithm") != SIGNATURE_ALGORITHM:
        raise ReleaseSigningError("detached release signature algorithm mismatch")
    key_id = _validate_key_id(str(envelope.get("key_id") or ""))
    signed_at = _parse_timestamp(envelope.get("signed_at"), "detached release signature signed_at")
    _validate_signature_time(request, signed_at)
    public_key = _require_file(public_key_path, f"trusted public key {key_id}")
    fingerprint = public_key_fingerprint(public_key)
    if envelope.get("public_key_sha256") != fingerprint:
        raise ReleaseSigningError("detached release signature public-key fingerprint mismatch")
    try:
        authorized = require_authorized_signer(
            trust_policy,
            key_id=key_id,
            public_key_sha256=fingerprint,
            release=RELEASE_CODENAME,
            signed_at=signed_at,
        )
    except ReleaseTrustError as exc:
        raise ReleaseSigningError(f"detached release signer is not authorized by trust policy: {exc}") from exc
    if envelope.get("role") != str(authorized["role"]):
        raise ReleaseSigningError("detached release signature role mismatch")
    statement = {
        key: envelope[key]
        for key in (
            "schema_version",
            "release",
            "request_sha256",
            "key_id",
            "role",
            "public_key_sha256",
            "signature_algorithm",
            "signed_at",
        )
    }
    message = canonical_json(statement).encode("utf-8")
    if envelope.get("signed_payload_sha256") != sha256_bytes(message):
        raise ReleaseSigningError("detached release signature payload hash mismatch")
    try:
        signature = base64.b64decode(str(envelope.get("value_base64") or ""), validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ReleaseSigningError("detached release signature is not valid base64") from exc
    if len(signature) != 64 or not _verify_ed25519(public_key, message, signature):
        raise ReleaseSigningError("detached Ed25519 release signature verification failed")
    return authorized


def verify_release_signature_envelope(
    request: dict[str, Any],
    envelope: Any,
    public_key_path: Path,
    trust_policy_path: Path,
    *,
    root: Path,
) -> bool:
    try:
        trust_policy = _load_trust_policy(trust_policy_path, root.resolve())
        if request.get("trust") != {
            "policy_id": trust_policy.get("policy_id"),
            "organization": trust_policy.get("organization"),
            "policy_sha256": trust_policy_fingerprint(trust_policy),
        }:
            return False
        _verify_signature_envelope_or_raise(request, envelope, public_key_path, trust_policy)
    except ReleaseSigningError:
        return False
    return True


def assemble_release_attestation(
    root: Path,
    request: dict[str, Any],
    artifact_path: Path,
    bundle: dict[str, Any],
    manifest: dict[str, Any],
    signature_envelopes: Sequence[dict[str, Any]],
    trusted_public_keys: Mapping[str, Path],
    trust_policy_path: Path,
) -> dict[str, Any]:
    """Assemble detached signatures using only public keys; no private key is accepted here."""
    trust_policy, _, _ = _verify_signing_request_or_raise(
        request,
        artifact_path,
        trust_policy_path,
        bundle=bundle,
        manifest=manifest,
        root=root,
    )
    if not signature_envelopes:
        raise ReleaseSigningError("at least one detached release signature is required")
    seen_ids: set[str] = set()
    seen_fingerprints: set[str] = set()
    roles: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for envelope in signature_envelopes:
        key_id = _validate_key_id(str(envelope.get("key_id") or "")) if isinstance(envelope, dict) else ""
        if not key_id or key_id in seen_ids:
            raise ReleaseSigningError("detached release signer key IDs must be distinct")
        if key_id not in trusted_public_keys:
            raise ReleaseSigningError(f"trusted public key is missing for detached signer {key_id}")
        authorized = _verify_signature_envelope_or_raise(
            request,
            envelope,
            Path(trusted_public_keys[key_id]),
            trust_policy,
        )
        fingerprint = str(envelope["public_key_sha256"])
        if fingerprint in seen_fingerprints:
            raise ReleaseSigningError("detached release signer public-key fingerprints must be distinct")
        seen_ids.add(key_id)
        seen_fingerprints.add(fingerprint)
        roles.add(str(authorized["role"]))
        normalized.append(dict(envelope))

    quorum = trust_policy["quorum"]
    minimum = int(quorum["minimum_signatures"])
    if len(normalized) < minimum:
        raise ReleaseSigningError(f"release signature quorum not met: {len(normalized)}/{minimum} authorized signatures")
    missing_roles = set(quorum["required_roles"]) - roles
    if missing_roles:
        raise ReleaseSigningError(f"release signature quorum is missing required roles: {sorted(missing_roles)}")
    normalized.sort(key=lambda item: str(item["key_id"]))
    return {
        "schema_version": ATTESTATION_SCHEMA_VERSION,
        "release": RELEASE_CODENAME,
        "signing_request": dict(request),
        "signatures": normalized,
    }


def verify_release_attestation(
    payload: Any,
    artifact_path: Path,
    trusted_public_keys: Mapping[str, Path],
    trust_policy_path: Path,
    *,
    bundle: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
    expected_key_ids: set[str] | None = None,
    expected_policy_id: str | None = None,
    root: Path | None = None,
) -> bool:
    if root is None or bundle is None or manifest is None:
        return False
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "release", "signing_request", "signatures"}:
        return False
    if payload.get("schema_version") != ATTESTATION_SCHEMA_VERSION or payload.get("release") != RELEASE_CODENAME:
        return False
    request = payload.get("signing_request")
    signatures = payload.get("signatures")
    if not isinstance(request, dict) or not isinstance(signatures, list):
        return False
    try:
        trust_policy = _load_trust_policy(trust_policy_path, root.resolve())
    except ReleaseSigningError:
        return False
    if expected_policy_id is not None and trust_policy.get("policy_id") != expected_policy_id:
        return False
    try:
        expected = assemble_release_attestation(
            root,
            request,
            artifact_path,
            bundle,
            manifest,
            signatures,
            trusted_public_keys,
            trust_policy_path,
        )
    except ReleaseSigningError:
        return False
    if payload != expected:
        return False
    if expected_key_ids is not None and {str(item["key_id"]) for item in signatures} != set(expected_key_ids):
        return False
    return True
