# Rivexis Release Trust and Detached Signing Policy — P37

P37 preserves P36 dependency-certification integrity plus P35/P34 runtime hardening, detached signing, trust-policy, attestation and anti-rollback lineage semantics. P37 changes only staging child-result classification; no production private key, trust policy, detached signature or release-channel head belongs in the source repository.

## Current contracts

- Release: `P37` / API-package version `3.4.3`.
- External trust policy: schema v3.
- Signing request: schema v2.
- Detached signature envelope: schema v1.
- Final quorum attestation: schema v5.
- Release-lineage checkpoint: schema v1.
- Signature algorithm: Ed25519.

The external trust policy controls authorized key IDs, roles, public-key fingerprints, ACTIVE/REVOKED state, key validity, authorized release range, minimum signature quorum, required roles, signing-request TTL, maximum certification age and maximum allowed clock skew.

## Fail-closed prerequisites

A signing request is created only when the exact immutable artifact is outside the repository and `verify_release_bundle(..., require_complete=True)` succeeds against the exact P37 execution manifest/source tree. Signing refuses a private key or trust policy stored inside the repository. Each signer accepts exactly one private key. The coordinator assembles signatures using public keys only.

New signatures are rejected after request expiry or when certification has become too old. A historically valid attestation remains verifiable after the ceremony closes because verification proves each signature was created within its permitted time window.

## Production ceremony

```bash
python scripts/create_release_signing_request.py ../RIVEXIS_Production_MVP_P37.zip \
  --trust-policy ../rivexis-release-trust-v3.json \
  --bundle release-certification-bundle.json \
  --manifest certification-execution-manifest.json \
  --output ../P37-signing-request.json

python scripts/sign_release_request.py ../P37-signing-request.json ../RIVEXIS_Production_MVP_P37.zip \
  --key-id <authorized-key-id> \
  --private-key /external/secure/location/key.pem \
  --trust-policy ../rivexis-release-trust-v3.json \
  --bundle release-certification-bundle.json \
  --manifest certification-execution-manifest.json \
  --output ../P37-<authorized-key-id>-signature.json

python scripts/assemble_release_attestation.py ../P37-signing-request.json ../RIVEXIS_Production_MVP_P37.zip \
  --signature ../P37-release-engineering-signature.json \
  --signature ../P37-security-signature.json \
  --public-key rivexis-release-engineering=/external/release-public.pem \
  --public-key rivexis-security=/external/security-public.pem \
  --trust-policy ../rivexis-release-trust-v3.json \
  --bundle release-certification-bundle.json \
  --manifest certification-execution-manifest.json \
  --output ../RIVEXIS_Production_MVP_P37.zip.attestation.json

python scripts/verify_release_attestation.py ../RIVEXIS_Production_MVP_P37.zip.attestation.json ../RIVEXIS_Production_MVP_P37.zip \
  --public-key rivexis-release-engineering=/external/release-public.pem \
  --public-key rivexis-security=/external/security-public.pem \
  --trust-policy ../rivexis-release-trust-v3.json \
  --bundle release-certification-bundle.json \
  --manifest certification-execution-manifest.json
```

## Anti-rollback publication

After quorum attestation verifies, publish/advance the external channel checkpoint with `advance_release_lineage.py`. Non-genesis publication must provide the trusted previous checkpoint and its expected SHA-256; the new release number must be greater. Genesis requires explicit `--allow-genesis`. Deployment verification uses `verify_release_lineage.py` with the expected trusted head SHA-256 and, when policy requires it, a minimum accepted release number.

P37 does not treat a mutable repository file as a trust root. Organizational keys, trust policy and trusted release-channel head remain independently distributed operational state.

## P37 scope note

P37 preserves P35 telemetry confidentiality, provider diagnostic isolation and global authentication abuse controls while preserving P34 runtime tenant/session/provider/webhook boundaries but does not change the detached signing request, signature-envelope, quorum-attestation, trust-policy or release-lineage schemas. Signing must still refuse an incomplete certification bundle, in-repository trust roots/private keys, stale certification and rollback lineage.
