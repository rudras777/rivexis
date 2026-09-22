from __future__ import annotations

import copy
from pathlib import Path

import pytest

from rivexis_api.certification import canonical_json, sha256_bytes
from rivexis_api.release_lineage import (
    LINEAGE_CHECKPOINT_SCHEMA_VERSION,
    ReleaseLineageError,
    advance_release_lineage,
    checkpoint_fingerprint,
    verify_lineage_checkpoint,
    verify_release_against_lineage,
)
from rivexis_api.version import RELEASE_CODENAME
from test_p35_release_signing import _ceremony, _complete_bundle, _two_signers


def _valid_release(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest, bundle = _complete_bundle(repo)
    artifact = tmp_path / "rivexis-p26.zip"
    artifact.write_bytes(b"immutable P35 release bytes")
    private, public, policy = _two_signers(tmp_path)
    request, envelopes, attestation = _ceremony(repo, artifact, manifest, bundle, private, public, policy)
    return repo, manifest, bundle, artifact, public, policy, attestation


def _synthetic_checkpoint(*, release: str, sequence: int, channel: str = "production", previous: str | None = None) -> dict:
    number = int(release[1:])
    body = {
        "schema_version": LINEAGE_CHECKPOINT_SCHEMA_VERSION,
        "channel": channel,
        "sequence": sequence,
        "release": release,
        "release_number": number,
        "artifact_sha256": "a" * 64,
        "attestation_sha256": "b" * 64,
        "previous_checkpoint_sha256": previous,
        "published_at": "2026-09-11T12:00:00+00:00",
    }
    return {**body, "checkpoint_sha256": sha256_bytes(canonical_json(body).encode("utf-8"))}


def test_genesis_lineage_requires_explicit_authorization_and_binds_verified_release(tmp_path: Path) -> None:
    repo, manifest, bundle, artifact, public, policy, attestation = _valid_release(tmp_path)
    with pytest.raises(ReleaseLineageError, match="explicit allow_genesis"):
        advance_release_lineage(
            root=repo,
            channel="production",
            attestation=attestation,
            artifact_path=artifact,
            trusted_public_keys=public,
            trust_policy_path=policy,
            bundle=bundle,
            manifest=manifest,
        )
    checkpoint = advance_release_lineage(
        root=repo,
        channel="production",
        attestation=attestation,
        artifact_path=artifact,
        trusted_public_keys=public,
        trust_policy_path=policy,
        bundle=bundle,
        manifest=manifest,
        allow_genesis=True,
    )
    assert checkpoint["release"] == RELEASE_CODENAME == "P37"
    assert checkpoint["sequence"] == 1
    assert checkpoint["previous_checkpoint_sha256"] is None
    assert verify_lineage_checkpoint(checkpoint, expected_channel="production") == checkpoint
    assert verify_release_against_lineage(
        root=repo,
        checkpoint=checkpoint,
        expected_head_sha256=checkpoint["checkpoint_sha256"],
        channel="production",
        attestation=attestation,
        artifact_path=artifact,
        trusted_public_keys=public,
        trust_policy_path=policy,
        bundle=bundle,
        manifest=manifest,
        minimum_release_number=23,
    )


def test_lineage_advancement_requires_trusted_previous_head_and_is_monotonic(tmp_path: Path) -> None:
    repo, manifest, bundle, artifact, public, policy, attestation = _valid_release(tmp_path)
    previous = _synthetic_checkpoint(release="P22", sequence=7, previous="c" * 64)
    with pytest.raises(ReleaseLineageError, match="trusted previous head"):
        advance_release_lineage(
            root=repo,
            channel="production",
            attestation=attestation,
            artifact_path=artifact,
            trusted_public_keys=public,
            trust_policy_path=policy,
            bundle=bundle,
            manifest=manifest,
            previous_checkpoint=previous,
        )
    checkpoint = advance_release_lineage(
        root=repo,
        channel="production",
        attestation=attestation,
        artifact_path=artifact,
        trusted_public_keys=public,
        trust_policy_path=policy,
        bundle=bundle,
        manifest=manifest,
        previous_checkpoint=previous,
        expected_previous_sha256=previous["checkpoint_sha256"],
    )
    assert checkpoint["sequence"] == 8
    assert checkpoint["previous_checkpoint_sha256"] == previous["checkpoint_sha256"]

    non_monotonic = _synthetic_checkpoint(release="P37", sequence=8, previous=previous["checkpoint_sha256"])
    with pytest.raises(ReleaseLineageError, match="rollback or non-monotonic"):
        advance_release_lineage(
            root=repo,
            channel="production",
            attestation=attestation,
            artifact_path=artifact,
            trusted_public_keys=public,
            trust_policy_path=policy,
            bundle=bundle,
            manifest=manifest,
            previous_checkpoint=non_monotonic,
            expected_previous_sha256=non_monotonic["checkpoint_sha256"],
        )


def test_checkpoint_tampering_wrong_channel_and_stale_head_fail_closed(tmp_path: Path) -> None:
    repo, manifest, bundle, artifact, public, policy, attestation = _valid_release(tmp_path)
    checkpoint = advance_release_lineage(
        root=repo,
        channel="production",
        attestation=attestation,
        artifact_path=artifact,
        trusted_public_keys=public,
        trust_policy_path=policy,
        bundle=bundle,
        manifest=manifest,
        allow_genesis=True,
    )
    tampered = copy.deepcopy(checkpoint)
    tampered["published_at"] = "2026-09-11T12:00:01+00:00"
    with pytest.raises(ReleaseLineageError, match="seal mismatch"):
        verify_lineage_checkpoint(tampered)
    with pytest.raises(ReleaseLineageError, match="expected channel"):
        verify_lineage_checkpoint(checkpoint, expected_channel="staging")
    with pytest.raises(ReleaseLineageError, match="trusted head"):
        verify_lineage_checkpoint(checkpoint, expected_head_sha256="0" * 64)


def test_lineage_verification_rejects_artifact_or_attestation_substitution(tmp_path: Path) -> None:
    repo, manifest, bundle, artifact, public, policy, attestation = _valid_release(tmp_path)
    checkpoint = advance_release_lineage(
        root=repo,
        channel="production",
        attestation=attestation,
        artifact_path=artifact,
        trusted_public_keys=public,
        trust_policy_path=policy,
        bundle=bundle,
        manifest=manifest,
        allow_genesis=True,
    )
    artifact.write_bytes(b"tampered artifact")
    assert not verify_release_against_lineage(
        root=repo,
        checkpoint=checkpoint,
        expected_head_sha256=checkpoint["checkpoint_sha256"],
        channel="production",
        attestation=attestation,
        artifact_path=artifact,
        trusted_public_keys=public,
        trust_policy_path=policy,
        bundle=bundle,
        manifest=manifest,
    )
    artifact.write_bytes(b"immutable P35 release bytes")
    changed = copy.deepcopy(attestation)
    changed["signatures"][0]["value_base64"] = "A" * 88
    assert not verify_release_against_lineage(
        root=repo,
        checkpoint=checkpoint,
        expected_head_sha256=checkpoint["checkpoint_sha256"],
        channel="production",
        attestation=changed,
        artifact_path=artifact,
        trusted_public_keys=public,
        trust_policy_path=policy,
        bundle=bundle,
        manifest=manifest,
    )


def test_minimum_release_floor_blocks_downgrade_even_with_trusted_head(tmp_path: Path) -> None:
    repo, manifest, bundle, artifact, public, policy, attestation = _valid_release(tmp_path)
    checkpoint = advance_release_lineage(
        root=repo,
        channel="production",
        attestation=attestation,
        artifact_path=artifact,
        trusted_public_keys=public,
        trust_policy_path=policy,
        bundle=bundle,
        manifest=manifest,
        allow_genesis=True,
    )
    assert not verify_release_against_lineage(
        root=repo,
        checkpoint=checkpoint,
        expected_head_sha256=checkpoint["checkpoint_sha256"],
        channel="production",
        attestation=attestation,
        artifact_path=artifact,
        trusted_public_keys=public,
        trust_policy_path=policy,
        bundle=bundle,
        manifest=manifest,
        minimum_release_number=38,
    )


def test_genesis_cannot_claim_a_predecessor_and_non_genesis_must_have_one() -> None:
    bad_genesis = _synthetic_checkpoint(release="P35", sequence=1, previous="c" * 64)
    with pytest.raises(ReleaseLineageError, match="genesis"):
        verify_lineage_checkpoint(bad_genesis)
    bad_non_genesis = _synthetic_checkpoint(release="P35", sequence=2, previous=None)
    with pytest.raises(ReleaseLineageError, match="previous_checkpoint_sha256"):
        verify_lineage_checkpoint(bad_non_genesis)
