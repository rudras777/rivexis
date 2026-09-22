from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .certification import canonical_json, sha256_bytes
from .release_signing import verify_release_attestation

LINEAGE_CHECKPOINT_SCHEMA_VERSION = 1
_CHANNEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,63}$")
_RELEASE_RE = re.compile(r"^P([1-9][0-9]*)$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReleaseLineageError(ValueError):
    """Raised when release publication/deployment lineage verification fails closed."""


def _release_number(release: str) -> int:
    match = _RELEASE_RE.fullmatch(release)
    if not match:
        raise ReleaseLineageError(f"invalid release codename: {release!r}")
    return int(match.group(1))


def _timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReleaseLineageError(f"{label} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReleaseLineageError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReleaseLineageError(f"{label} must include a timezone offset")
    return parsed.astimezone(timezone.utc).isoformat()


def _validate_hash(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ReleaseLineageError(f"{label} must be a lowercase SHA-256 hex digest")
    return value


def checkpoint_fingerprint(checkpoint: Mapping[str, Any]) -> str:
    body = dict(checkpoint)
    body.pop("checkpoint_sha256", None)
    return sha256_bytes(canonical_json(body).encode("utf-8"))


def verify_lineage_checkpoint(
    payload: Any,
    *,
    expected_channel: str | None = None,
    expected_head_sha256: str | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ReleaseLineageError("release lineage checkpoint must be an object")
    expected_fields = {
        "schema_version",
        "channel",
        "sequence",
        "release",
        "release_number",
        "artifact_sha256",
        "attestation_sha256",
        "previous_checkpoint_sha256",
        "published_at",
        "checkpoint_sha256",
    }
    if set(payload) != expected_fields or payload.get("schema_version") != LINEAGE_CHECKPOINT_SCHEMA_VERSION:
        raise ReleaseLineageError("unsupported or malformed release lineage checkpoint schema")
    channel = payload.get("channel")
    if not isinstance(channel, str) or not _CHANNEL_RE.fullmatch(channel):
        raise ReleaseLineageError("release lineage channel is invalid")
    if expected_channel is not None and channel != expected_channel:
        raise ReleaseLineageError("release lineage channel does not match expected channel")
    sequence = payload.get("sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise ReleaseLineageError("release lineage sequence must be a positive integer")
    release = payload.get("release")
    if not isinstance(release, str):
        raise ReleaseLineageError("release lineage release must be a release codename")
    number = _release_number(release)
    if payload.get("release_number") != number:
        raise ReleaseLineageError("release lineage release_number does not match release codename")
    _validate_hash(payload.get("artifact_sha256"), "release lineage artifact_sha256")
    _validate_hash(payload.get("attestation_sha256"), "release lineage attestation_sha256")
    previous = payload.get("previous_checkpoint_sha256")
    if sequence == 1:
        if previous is not None:
            raise ReleaseLineageError("genesis release lineage checkpoint must not have a predecessor")
    else:
        _validate_hash(previous, "release lineage previous_checkpoint_sha256")
    _timestamp(payload.get("published_at"), "release lineage published_at")
    supplied = _validate_hash(payload.get("checkpoint_sha256"), "release lineage checkpoint_sha256")
    expected = checkpoint_fingerprint(payload)
    if supplied != expected:
        raise ReleaseLineageError("release lineage checkpoint seal mismatch")
    if expected_head_sha256 is not None:
        _validate_hash(expected_head_sha256, "expected release lineage head")
        if supplied != expected_head_sha256:
            raise ReleaseLineageError("release lineage checkpoint does not match trusted head")
    return payload


def _artifact_sha256(path: Path) -> str:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ReleaseLineageError(f"release artifact does not exist or is not a file: {resolved}")
    data = resolved.read_bytes()
    if not data:
        raise ReleaseLineageError("release artifact must not be empty")
    return hashlib.sha256(data).hexdigest()


def _attestation_sha256(attestation: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json(dict(attestation)).encode("utf-8"))


def advance_release_lineage(
    *,
    root: Path,
    channel: str,
    attestation: dict[str, Any],
    artifact_path: Path,
    trusted_public_keys: Mapping[str, Path],
    trust_policy_path: Path,
    bundle: dict[str, Any],
    manifest: dict[str, Any],
    previous_checkpoint: dict[str, Any] | None = None,
    expected_previous_sha256: str | None = None,
    allow_genesis: bool = False,
) -> dict[str, Any]:
    if not isinstance(channel, str) or not _CHANNEL_RE.fullmatch(channel):
        raise ReleaseLineageError("release lineage channel is invalid")
    if not verify_release_attestation(
        attestation,
        artifact_path,
        trusted_public_keys,
        trust_policy_path,
        bundle=bundle,
        manifest=manifest,
        root=root,
    ):
        raise ReleaseLineageError("release lineage advancement requires a valid quorum release attestation")
    release = attestation.get("release")
    if not isinstance(release, str):
        raise ReleaseLineageError("release attestation does not contain a valid release codename")
    number = _release_number(release)

    if previous_checkpoint is None:
        if not allow_genesis:
            raise ReleaseLineageError("release lineage genesis requires explicit allow_genesis authorization")
        if expected_previous_sha256 is not None:
            raise ReleaseLineageError("genesis release lineage must not specify an expected predecessor hash")
        sequence = 1
        previous_hash = None
    else:
        if expected_previous_sha256 is None:
            raise ReleaseLineageError("release lineage advancement requires the trusted previous head SHA-256")
        previous = verify_lineage_checkpoint(
            previous_checkpoint,
            expected_channel=channel,
            expected_head_sha256=expected_previous_sha256,
        )
        if number <= int(previous["release_number"]):
            raise ReleaseLineageError("release lineage rejects rollback or non-monotonic release advancement")
        sequence = int(previous["sequence"]) + 1
        previous_hash = str(previous["checkpoint_sha256"])

    body = {
        "schema_version": LINEAGE_CHECKPOINT_SCHEMA_VERSION,
        "channel": channel,
        "sequence": sequence,
        "release": release,
        "release_number": number,
        "artifact_sha256": _artifact_sha256(artifact_path),
        "attestation_sha256": _attestation_sha256(attestation),
        "previous_checkpoint_sha256": previous_hash,
        "published_at": datetime.now(timezone.utc).isoformat(),
    }
    return {**body, "checkpoint_sha256": sha256_bytes(canonical_json(body).encode("utf-8"))}


def verify_release_against_lineage(
    *,
    root: Path,
    checkpoint: dict[str, Any],
    expected_head_sha256: str,
    channel: str,
    attestation: dict[str, Any],
    artifact_path: Path,
    trusted_public_keys: Mapping[str, Path],
    trust_policy_path: Path,
    bundle: dict[str, Any],
    manifest: dict[str, Any],
    minimum_release_number: int | None = None,
) -> bool:
    try:
        verified = verify_lineage_checkpoint(
            checkpoint,
            expected_channel=channel,
            expected_head_sha256=expected_head_sha256,
        )
        if not verify_release_attestation(
            attestation,
            artifact_path,
            trusted_public_keys,
            trust_policy_path,
            bundle=bundle,
            manifest=manifest,
            root=root,
        ):
            return False
        release = attestation.get("release")
        if release != verified["release"]:
            return False
        if minimum_release_number is not None:
            if not isinstance(minimum_release_number, int) or isinstance(minimum_release_number, bool) or minimum_release_number < 1:
                return False
            if int(verified["release_number"]) < minimum_release_number:
                return False
        if _artifact_sha256(artifact_path) != verified["artifact_sha256"]:
            return False
        if _attestation_sha256(attestation) != verified["attestation_sha256"]:
            return False
    except ReleaseLineageError:
        return False
    return True
