from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .certification import canonical_json, sha256_bytes

TRUST_POLICY_SCHEMA_VERSION = 3
TRUST_POLICY_ALGORITHM = "Ed25519"
_KEY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,127}$")
_POLICY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,127}$")
_ROLE_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RELEASE_RE = re.compile(r"^P([1-9][0-9]*)$")


class ReleaseTrustError(ValueError):
    """Raised when an organizational release trust policy fails closed."""


def _parse_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ReleaseTrustError(f"{label} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReleaseTrustError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReleaseTrustError(f"{label} must include a timezone offset")
    return parsed.astimezone(timezone.utc)


def _release_number(release: str) -> int:
    match = _RELEASE_RE.fullmatch(release)
    if not match:
        raise ReleaseTrustError(f"invalid release codename: {release!r}")
    return int(match.group(1))


def _validate_key_entry(entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise ReleaseTrustError("trust policy keys must be objects")
    expected_fields = {
        "key_id",
        "role",
        "public_key_sha256",
        "status",
        "not_before",
        "not_after",
        "release_min",
        "release_max",
    }
    if set(entry) != expected_fields:
        raise ReleaseTrustError("trust policy key entries must contain exactly the documented fields")
    key_id = entry.get("key_id")
    role = entry.get("role")
    fingerprint = entry.get("public_key_sha256")
    status = entry.get("status")
    if not isinstance(key_id, str) or not _KEY_ID_RE.fullmatch(key_id):
        raise ReleaseTrustError("trust policy key_id is invalid")
    if not isinstance(role, str) or not _ROLE_RE.fullmatch(role):
        raise ReleaseTrustError(f"trust policy key {key_id!r} has invalid role")
    if not isinstance(fingerprint, str) or not _SHA256_RE.fullmatch(fingerprint):
        raise ReleaseTrustError(f"trust policy key {key_id!r} has invalid public_key_sha256")
    if status not in {"ACTIVE", "REVOKED"}:
        raise ReleaseTrustError(f"trust policy key {key_id!r} has invalid status")
    not_before = _parse_timestamp(entry.get("not_before"), f"trust policy key {key_id!r} not_before")
    not_after_raw = entry.get("not_after")
    not_after = None if not_after_raw is None else _parse_timestamp(not_after_raw, f"trust policy key {key_id!r} not_after")
    if not_after is not None and not_after <= not_before:
        raise ReleaseTrustError(f"trust policy key {key_id!r} not_after must be later than not_before")
    release_min = entry.get("release_min")
    release_max = entry.get("release_max")
    if not isinstance(release_min, int) or isinstance(release_min, bool) or release_min < 1:
        raise ReleaseTrustError(f"trust policy key {key_id!r} release_min must be a positive integer")
    if release_max is not None and (
        not isinstance(release_max, int) or isinstance(release_max, bool) or release_max < release_min
    ):
        raise ReleaseTrustError(f"trust policy key {key_id!r} release_max must be null or >= release_min")
    return {
        "key_id": key_id,
        "role": role,
        "public_key_sha256": fingerprint,
        "status": status,
        "not_before": not_before,
        "not_after": not_after,
        "release_min": release_min,
        "release_max": release_max,
    }


def _validate_quorum(quorum: Any, *, keys: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(quorum, dict) or set(quorum) != {"minimum_signatures", "required_roles"}:
        raise ReleaseTrustError("trust policy quorum must contain exactly minimum_signatures and required_roles")
    minimum = quorum.get("minimum_signatures")
    roles = quorum.get("required_roles")
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 2:
        raise ReleaseTrustError("trust policy minimum_signatures must be an integer >= 2")
    if minimum > len(keys):
        raise ReleaseTrustError("trust policy minimum_signatures cannot exceed the number of trusted keys")
    if not isinstance(roles, list) or len(roles) < 2:
        raise ReleaseTrustError("trust policy required_roles must contain at least two roles")
    if any(not isinstance(role, str) or not _ROLE_RE.fullmatch(role) for role in roles):
        raise ReleaseTrustError("trust policy required_roles contains an invalid role")
    if len(set(roles)) != len(roles):
        raise ReleaseTrustError("trust policy required_roles must be unique")
    if minimum < len(roles):
        raise ReleaseTrustError("minimum_signatures must be >= the number of required_roles")
    known_roles = {entry["role"] for entry in keys}
    missing_roles = set(roles) - known_roles
    if missing_roles:
        raise ReleaseTrustError(f"trust policy required_roles are not backed by trusted keys: {sorted(missing_roles)}")
    return {"minimum_signatures": minimum, "required_roles": list(roles)}


def _validate_ceremony(ceremony: Any) -> dict[str, int]:
    if not isinstance(ceremony, dict) or set(ceremony) != {
        "request_ttl_seconds",
        "max_certification_age_seconds",
        "max_clock_skew_seconds",
    }:
        raise ReleaseTrustError(
            "trust policy ceremony must contain exactly request_ttl_seconds, "
            "max_certification_age_seconds and max_clock_skew_seconds"
        )
    request_ttl = ceremony.get("request_ttl_seconds")
    max_age = ceremony.get("max_certification_age_seconds")
    max_skew = ceremony.get("max_clock_skew_seconds")
    if not isinstance(request_ttl, int) or isinstance(request_ttl, bool) or not 300 <= request_ttl <= 86400:
        raise ReleaseTrustError("trust policy request_ttl_seconds must be an integer between 300 and 86400")
    if not isinstance(max_age, int) or isinstance(max_age, bool) or not 3600 <= max_age <= 604800:
        raise ReleaseTrustError(
            "trust policy max_certification_age_seconds must be an integer between 3600 and 604800"
        )
    if not isinstance(max_skew, int) or isinstance(max_skew, bool) or not 0 <= max_skew <= 300:
        raise ReleaseTrustError("trust policy max_clock_skew_seconds must be an integer between 0 and 300")
    return {
        "request_ttl_seconds": request_ttl,
        "max_certification_age_seconds": max_age,
        "max_clock_skew_seconds": max_skew,
    }


def verify_trust_policy(policy: Any) -> dict[str, Any]:
    if not isinstance(policy, dict) or policy.get("schema_version") != TRUST_POLICY_SCHEMA_VERSION:
        raise ReleaseTrustError("unsupported release trust policy schema")
    expected_fields = {
        "schema_version",
        "policy_id",
        "organization",
        "signature_algorithm",
        "quorum",
        "ceremony",
        "keys",
    }
    if set(policy) != expected_fields:
        raise ReleaseTrustError("trust policy must contain exactly the documented top-level fields")
    policy_id = policy.get("policy_id")
    organization = policy.get("organization")
    algorithm = policy.get("signature_algorithm")
    keys = policy.get("keys")
    if not isinstance(policy_id, str) or not _POLICY_ID_RE.fullmatch(policy_id):
        raise ReleaseTrustError("trust policy policy_id is invalid")
    if not isinstance(organization, str) or not organization.strip() or len(organization.strip()) > 128:
        raise ReleaseTrustError("trust policy organization must be 1-128 characters")
    if algorithm != TRUST_POLICY_ALGORITHM:
        raise ReleaseTrustError("trust policy signature_algorithm must be Ed25519")
    if not isinstance(keys, list) or len(keys) < 2:
        raise ReleaseTrustError("trust policy must contain at least two keys")

    validated = [_validate_key_entry(entry) for entry in keys]
    key_ids = [entry["key_id"] for entry in validated]
    fingerprints = [entry["public_key_sha256"] for entry in validated]
    if len(set(key_ids)) != len(key_ids):
        raise ReleaseTrustError("trust policy contains duplicate key_id values")
    if len(set(fingerprints)) != len(fingerprints):
        raise ReleaseTrustError("trust policy contains duplicate public-key fingerprints")
    _validate_quorum(policy.get("quorum"), keys=validated)
    _validate_ceremony(policy.get("ceremony"))
    return policy


def trust_policy_fingerprint(policy: Any) -> str:
    verified = verify_trust_policy(policy)
    return sha256_bytes(canonical_json(verified).encode("utf-8"))


def require_authorized_signer(
    policy: Any,
    *,
    key_id: str,
    public_key_sha256: str,
    release: str,
    signed_at: str,
) -> dict[str, Any]:
    verified = verify_trust_policy(policy)
    release_number = _release_number(release)
    signed_time = _parse_timestamp(signed_at, "attestation generated_at")
    for raw_entry in verified["keys"]:
        entry = _validate_key_entry(raw_entry)
        if entry["key_id"] != key_id:
            continue
        if entry["public_key_sha256"] != public_key_sha256:
            raise ReleaseTrustError("trusted key fingerprint does not match attestation signer")
        if entry["status"] != "ACTIVE":
            raise ReleaseTrustError("release signing key is revoked")
        if signed_time < entry["not_before"]:
            raise ReleaseTrustError("release signature predates key validity")
        if entry["not_after"] is not None and signed_time > entry["not_after"]:
            raise ReleaseTrustError("release signature is outside key validity window")
        if release_number < entry["release_min"]:
            raise ReleaseTrustError("release is below key authorization range")
        if entry["release_max"] is not None and release_number > entry["release_max"]:
            raise ReleaseTrustError("release is above key authorization range")
        return raw_entry
    raise ReleaseTrustError(f"key_id {key_id!r} is not authorized by the trust policy")


def require_authorized_quorum(
    policy: Any,
    *,
    signers: list[dict[str, str]],
    release: str,
    signed_at: str,
) -> list[dict[str, Any]]:
    verified = verify_trust_policy(policy)
    if not isinstance(signers, list):
        raise ReleaseTrustError("release signers must be a list")
    key_ids = [str(signer.get("key_id") or "") for signer in signers if isinstance(signer, dict)]
    fingerprints = [str(signer.get("public_key_sha256") or "") for signer in signers if isinstance(signer, dict)]
    if len(key_ids) != len(signers) or len(fingerprints) != len(signers):
        raise ReleaseTrustError("release signers must contain key_id and public_key_sha256")
    if len(set(key_ids)) != len(key_ids):
        raise ReleaseTrustError("release signer key IDs must be distinct")
    if len(set(fingerprints)) != len(fingerprints):
        raise ReleaseTrustError("release signer public-key fingerprints must be distinct")

    authorized = [
        require_authorized_signer(
            verified,
            key_id=signer["key_id"],
            public_key_sha256=signer["public_key_sha256"],
            release=release,
            signed_at=signed_at,
        )
        for signer in signers
    ]
    quorum = _validate_quorum(verified["quorum"], keys=[_validate_key_entry(entry) for entry in verified["keys"]])
    if len(authorized) < quorum["minimum_signatures"]:
        raise ReleaseTrustError(
            f"release signature quorum not met: {len(authorized)}/{quorum['minimum_signatures']} authorized signatures"
        )
    roles = {str(entry["role"]) for entry in authorized}
    missing_roles = set(quorum["required_roles"]) - roles
    if missing_roles:
        raise ReleaseTrustError(f"release signature quorum is missing required roles: {sorted(missing_roles)}")
    return authorized


def ensure_external_trust_policy(path: Path, root: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ReleaseTrustError(f"release trust policy does not exist or is not a file: {resolved}")
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return resolved
    raise ReleaseTrustError("release trust policy must remain outside the Rivexis repository")
