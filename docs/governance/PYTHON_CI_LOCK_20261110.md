# Hash-verified Python CI dependencies

The 10 November verified release inventory from main CI42846852325 contains73 installed distributions: the checked-out project and72 third-party distributions. `apps/api/requirements-ci-py313-linux.txt` preserves those72 versions exactly and authorizes1,348 non-yanked PyPI wheel SHA-256 digests. No application dependency version, manifest range or financial model is changed.

## Installation boundary

The shared `.github/actions/setup-python-ci` action serves the API, invariant and PostgreSQL migration jobs. Each creates an isolated venv on the existing Ubuntu24.04 x86_64 / CPython3.13 runner. Pip installs the checked requirements with hash enforcement, forced reinstallation and binary-only selection. Source distributions and unlisted transitive dependencies cannot silently enter the environment.

The local project is installed separately from the protected Git checkout with `--no-index --no-deps --no-build-isolation`. This trusts reviewed source without permitting a second floating dependency resolution or network-fetched build backend. The pinned setuptools is already installed. `pip check` validates dependencies, and the standard-library verifier requires exactly the72 locked distributions plus the current project version; missing, extra, duplicate or changed distributions fail the job.

The source manifest retains its existing developer/platform flexibility. This requirements file is a scoped pip hash lock for these Linux CI jobs, not a universal Python/OS lock, a PEP751 document, an offline wheelhouse or a claim that every published wheel was independently audited. Pip chooses a compatible authorized wheel. Interpreter patch releases, the hosted runner image, system libraries and registry availability remain separate reproducibility limits. The existing current-advisory `pip-audit` gate remains mandatory; pinned versions are not assumed permanently vulnerability-free.

The existing Deno2.9.6 type check also uses `--frozen-lockfile`, so it rejects an out-of-date tracked Deno lock instead of silently extending it. This covers CI resolution, not an independent certification of managed production bundling.

## Reviewed regeneration

Use a newly reviewed installed release inventory after deliberate dependency changes, installation/tests and vulnerability checks. The generator validates its source manifest hash, project version, package identities and coverage, then reads exact public release metadata from `https://pypi.org`. It collects non-yanked wheel hashes only; missing wheels, invalid digests, identity mismatch or provider failure abort generation. It does not resolve or upgrade versions, install packages, execute downloaded code, read credentials or export arbitrary pip metadata.

```sh
python scripts/python_ci_lock.py --inventory /path/to/rivexis-python-inventory.json --source-ci 42846852325
python -m unittest scripts.test_python_ci_lock
# In the intended clean Linux/Python3.13 CI environment, after installation:
python scripts/python_ci_lock.py --verify-installed
```

The run ID above identifies this first accepted source inventory. Future updates must name their own reviewed run; CI artifacts have seven-day retention and do not substitute for independently retained recovery material. Review version/hash diffs and use all existing protected gates. Ordinary rollback is the preceding protected source tree; no production schema or account change is required.

Local verification: twelve lock tests plus twelve inventory tests pass. Tests cover mismatched source, package substitution, duplicates, missing hashes, source/yanked distributions, unsafe directives and environment drift. Real isolated pip26.3 dry runs accepted the correct public wheel and rejected a deliberately changed digest; neither installed a package. Complete clean Linux installation and protected release remain acceptance gates.

References: [pip secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/), [repeatable installs and platform limits](https://pip.pypa.io/en/stable/topics/repeatable-installs/), [release inventory scope](RELEASE_INVENTORY_20261110.md).
