# Reproducible npm dependency SBOM — 5 November 2026

The prior native SBOM failure was reproduced without changing the project. npm 11.13.0 rejected intentional security overrides and four missing optional WASM dependency edges. An isolated npm 11.21.2 generator correctly recognized the overrides, then exposed the missing records and the private root manifest's absent version, which prevented a valid root package URL.

## Narrow repair

- Root package metadata now has version `0.1.0`, matching existing workspace metadata. It remains private; no website branding, product title or version suffix was added.
- Four registry-resolved optional development records complete the already-declared Tailwind WASM dependency graph: `@emnapi/core` 1.11.3, `@emnapi/wasi-threads` 1.2.3, `@napi-rs/wasm-runtime` 1.2.7 and `@tybys/wasm-util` 0.10.4. Their transitive runtime/tslib requirements reuse existing compatible records. No existing package record, version, integrity hash or security override was changed or removed.
- A manifest/lock-only candidate and a separate four-dependency resolver were used. The resolver's unrelated newer `tslib` selection was rejected; the existing 2.8.1 satisfies the declared range. Foreign-platform installation failures were not bypassed with force flags or by running WASM code.
- `npm run --silent sbom:npm` pins npm 11.21.2, uses the complete lock including optional packages, and emits CycloneDX 1.5 JSON. It does not install application packages, run application scripts, mutate the lock or require a paid service. The first use needs public registry access or a populated tool cache.
- Existing CI generates the document and preserves only that named public-dependency file using the immutable official upload action. Artifact names distinguish run/attempt; retention is seven days. No customer data, recovery file, credential directory or broad output glob is uploaded.

## Regenerate and interpret

```sh
npm ci
npm run --silent sbom:npm > rivexis-npm.cdx.json
```

The existing npm version remains usable for installation. Use the pinned command for SBOM generation; an older plain `npm sbom` can still misinterpret overrides. Do not downgrade patched packages to satisfy that older generator.

The location inventory is regenerated with `python scripts/dependency_inventory.py`; it is distinct from the native deduplicated component graph. Counts can differ because the same package/version appears at several lock locations. License fields are upstream metadata, not legal clearance. This npm document does not cover Python/Deno components, certify a standard SPDX document, assign a project license, or establish institutional security/transfer readiness.

Local validation passed: clean locked installation, full npm audit with zero known findings, official CycloneDX 1.5 schema validation (including international IRI/IDN formats), 367 dependency components/368 graph nodes, all 374 lock locations covered, zero unknown edges and zero duplicate identifiers. The schema snapshot is pinned to official commit `c320fc0f0b46873864927d9d5684eea7ba439728`. Initial validation lacked international-format support; that incomplete check was superseded using isolated pinned Ajv 8.20.0, ajv-formats 3.0.1 and ajv-formats-draft2019 1.6.1. The isolated validator is not a product dependency.

Release results are recorded in the protected PR and current checkpoint; do not infer deployment solely from generation success. Remaining owner MFA and full managed-service reconstruction gates are independent of this repair.

References: [npm SBOM command](https://docs.npmjs.com/cli/v11/commands/npm-sbom/), [official CycloneDX 1.5 schema](https://github.com/CycloneDX/specification/blob/c320fc0f0b46873864927d9d5684eea7ba439728/schema/bom-1.5.schema.json), [official artifact action v7.0.2](https://github.com/actions/upload-artifact/releases/tag/v7.0.2).

## Verified release

PR128 merged as `ab35d2b492cd799a686402bbb8a0824c93e9819b`. All six required source checks and main CI passed; 349 fixture cases per Chromium/Firefox/WebKit and 37 actual-public cases per hostname passed with zero failures, skips or flakes. Actual CI artifact `npm-sbom-42032657022-1` (ID13416134307, seven-day retention through 12 November) was downloaded, independently schema-validated and semantically compared with the local Windows graph. All 367 dependency components/368 graph nodes match; timestamps and document UUIDs need not match byte-for-byte. [Exact release receipt](../evidence/governance-sbom-release-20261105.json).
