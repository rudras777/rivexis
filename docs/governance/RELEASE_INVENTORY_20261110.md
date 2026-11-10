# Python and Deno release inventories

The existing npm CycloneDX artifact remains unchanged. CI now also prepares two narrowly scoped JSON inventories using the standard-library exporter `scripts/release_dependency_inventory.py`. Protected CI artifact publication and independent readback are acceptance gates; implementation alone is not verified publication.

## Scope and regeneration

Python inventory runs after the existing API installation, tests and `pip-audit --skip-editable` gate. It reads `pip inspect --local` from that isolated CI environment, retains only normalized distribution names and installed versions, and records project requirements/extras and the source manifest hash. Development, audit and bootstrap packages are included. Paths, direct URLs, authors, arbitrary license text, environment fields and unrelated metadata are excluded. Empty inventories, duplicate normalized names, unsupported input formats and direct manifest URLs fail closed without echoing their contents. The raw inspection file is temporary and is never uploaded.

```sh
python -m pip inspect --local > /tmp/rivexis-python-inspect.json
python scripts/release_dependency_inventory.py python --input /tmp/rivexis-python-inspect.json > /tmp/rivexis-python-inventory.json
python scripts/release_dependency_inventory.py deno > /tmp/rivexis-deno-inventory.json
python -m unittest scripts.test_release_dependency_inventory
```

Use pip23 or newer (stable inspect format1) and run the Python commands in the intended isolated application environment. The laptop default pip22.3 produced legacy format0 and was correctly rejected; an isolated pip26.3 tool environment is a local smoke check only, not application coverage. The default laptop environment is not evidence of the CI or production dependency set. Python requirements remain ranged; an installed inventory does not provide a reproducible Python lock or a full dependency graph.

Deno inventory reads only the tracked `supabase/functions/rivexis-api/deno.lock`, supports its explicit format5, preserves every JSR/npm/remote identity, integrity and raw dependency key, and records the lock hash. The current source contains60 entries:59 npm and1 JSR. Unknown formats, missing integrity and unsafe remote URLs fail closed. This includes transitive/type-only records and does not certify exactly which modules a managed production runtime bundles. The lock and existing dependency versions are not modified.

CI uploads only the exact sanitized files with the existing immutable official upload action. Artifact names include run/attempt IDs, retention is seven days, and missing output is an error. No broad output directory, pip inspection input, credentials or recovery material is uploaded. These custom inventories do not claim SPDX/CycloneDX validation, license clearance or absence of vulnerabilities. The existing npm standard SBOM and Python vulnerability gates remain separate.

References: [official pip inspect format](https://pip.pypa.io/en/stable/reference/inspect-report/), [Deno dependency management and lockfiles](https://docs.deno.com/runtime/packages/), [existing npm SBOM acceptance](DEPENDENCY_SBOM_20261105.md).
