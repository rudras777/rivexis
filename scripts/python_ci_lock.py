"""Pin the reviewed Linux/Python 3.13 CI inventory to PyPI wheel hashes."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import sys
import sysconfig
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "apps/api/requirements-ci-py313-linux.txt"
MANIFEST = ROOT / "apps/api/pyproject.toml"
NAME = r"[a-z0-9][a-z0-9-]*"
VERSION = r"[A-Za-z0-9][A-Za-z0-9.!+_-]*"


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def reviewed_packages(inventory: dict, manifest_bytes: bytes) -> dict[str, str]:
    manifest = tomllib.loads(manifest_bytes.decode())["project"]
    if inventory.get("format") != "rivexis-release-inventory-1" or inventory.get("ecosystem") != "python":
        raise ValueError("Unsupported inventory")
    if inventory.get("manifestSha256") != hashlib.sha256(manifest_bytes).hexdigest():
        raise ValueError("Inventory does not match the current manifest")
    packages = {}
    for component in inventory["components"]:
        name, version = component["name"], component["version"]
        if not re.fullmatch(NAME, name) or not re.fullmatch(VERSION, version) or name in packages:
            raise ValueError("Invalid or duplicate package identity")
        packages[name] = version
    if inventory.get("componentCount") != len(packages) or not packages:
        raise ValueError("Inventory coverage mismatch")
    if packages.pop(normalize(manifest["name"]), None) != manifest["version"]:
        raise ValueError("Reviewed project version is missing")
    return dict(sorted(packages.items()))


def wheel_hashes(release: dict, name: str, version: str) -> list[str]:
    if normalize(release["info"]["name"]) != name or release["info"]["version"] != version:
        raise ValueError("PyPI identity does not match the reviewed package")
    hashes = set()
    for file in release["urls"]:
        if file.get("yanked") or file.get("packagetype") != "bdist_wheel":
            continue
        digest = file.get("digests", {}).get("sha256", "")
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Invalid PyPI wheel digest")
        hashes.add(digest)
    if not hashes:
        raise ValueError("No non-yanked wheels for a reviewed package")
    return sorted(hashes)


def render_lock(packages: dict[str, str], releases: dict, source_ci: str) -> str:
    if not re.fullmatch(r"\d+", source_ci):
        raise ValueError("A numeric reviewed CI run is required")
    lines = [
        "# Ubuntu 24.04 x86_64 / CPython 3.13 / dev + full CI dependencies.",
        "# Reviewed inventory: GitHub Actions run " + source_ci,
        "# Exact existing versions; only non-yanked PyPI wheels are authorized.",
        "# Regenerate using scripts/python_ci_lock.py and a newly reviewed inventory.",
        "# Install with --require-hashes --only-binary=:all: in a fresh CI venv.",
        "",
    ]
    for name, version in sorted(packages.items()):
        hashes = wheel_hashes(releases[name], name, version)
        lines.append(f"{name}=={version} \\")
        for i, digest in enumerate(hashes):
            lines.append("    --hash=sha256:" + digest + (" \\" if i < len(hashes) - 1 else ""))
        lines.append("")
    return "\n".join(lines)


def parse_lock(text: str) -> dict[str, str]:
    packages, current, hashes = {}, None, 0
    for raw in text.splitlines():
        line = raw.strip().removesuffix("\\").strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(f"({NAME})==({VERSION})", line)
        if match:
            if current is not None and hashes == 0:
                raise ValueError("Package lacks hashes")
            current, version = match.groups()
            if current in packages:
                raise ValueError("Duplicate locked package")
            packages[current], hashes = version, 0
        elif re.fullmatch(r"--hash=sha256:[a-f0-9]{64}", line) and current is not None:
            hashes += 1
        else:
            raise ValueError("Unsupported lock directive or identity")
    if not packages or hashes == 0:
        raise ValueError("Empty or incomplete lock")
    return packages


def verify_versions(expected: dict[str, str], installed: list[tuple[str, str]]) -> None:
    actual = {}
    for name, version in installed:
        name = normalize(name)
        if name in actual:
            raise ValueError("Duplicate installed package")
        actual[name] = version
    if actual != expected:
        raise ValueError("Installed CI distributions differ from the reviewed lock")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--source-ci")
    parser.add_argument("--output", type=Path, default=LOCK)
    parser.add_argument("--verify-installed", action="store_true")
    args = parser.parse_args()
    try:
        manifest_bytes = MANIFEST.read_text(encoding="utf-8").encode()
        if args.verify_installed:
            if sys.platform != "linux" or sys.version_info[:2] != (3, 13) or platform.machine() != "x86_64" or sys.prefix == sys.base_prefix:
                raise ValueError("CI lock verification requires Linux x86_64 / Python 3.13")
            expected = parse_lock(LOCK.read_text())
            project = tomllib.loads(manifest_bytes.decode())["project"]
            expected[normalize(project["name"])] = project["version"]
            # Inspect installed venv metadata only. Editable source egg-info on
            # sys.path is not a second installed distribution.
            site_paths = sorted({sysconfig.get_path("purelib"), sysconfig.get_path("platlib")})
            verify_versions(expected, [(d.metadata["Name"], d.version) for d in importlib.metadata.distributions(path=site_paths)])
            print(f"Verified {len(expected)} exact installed CI distributions")
        else:
            if args.inventory is None or args.source_ci is None:
                parser.error("generation requires --inventory and --source-ci")
            packages = reviewed_packages(json.loads(args.inventory.read_text(encoding="utf-8-sig")), manifest_bytes)

            def fetch_release(item):
                name, version = item
                url = f"https://pypi.org/pypi/{quote(name, safe='')}/{quote(version, safe='')}/json"
                with urlopen(url, timeout=20) as response:
                    return name, json.load(response)

            with ThreadPoolExecutor(max_workers=6) as pool:
                releases = dict(pool.map(fetch_release, packages.items()))
            text = render_lock(packages, releases, args.source_ci)
            if parse_lock(text) != packages:
                raise ValueError("Rendered lock coverage mismatch")
            args.output.write_text(text, encoding="utf-8", newline="\n")
            print(f"Locked {len(packages)} unchanged third-party versions with wheel hashes")
    except (ValueError, KeyError, TypeError, OSError):
        print("Python CI lock validation failed; no input contents exported", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
