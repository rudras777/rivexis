"""Allowlisted release inventories; never export pip cache paths or direct URLs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "apps/api/pyproject.toml"
DENO_LOCK = ROOT / "supabase/functions/rivexis-api/deno.lock"


def python_inventory(inspect: dict, manifest: dict) -> dict:
    if inspect.get("version") != "1" or not isinstance(inspect.get("installed"), list) or not inspect["installed"]:
        raise ValueError("Unsupported pip inspect document")
    components = {}
    for distribution in inspect["installed"]:
        if not isinstance(distribution, dict) or not isinstance(distribution.get("metadata"), dict):
            raise ValueError("Invalid installed package record")
        metadata = distribution.get("metadata", {})
        name, version = metadata.get("name"), metadata.get("version")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}", name):
            raise ValueError("Invalid installed package identity")
        if not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.!+_-]{0,199}", version):
            raise ValueError("Invalid installed package version")
        name = re.sub(r"[-_.]+", "-", name).lower()
        if name in components:
            raise ValueError("Duplicate installed package identity")
        # No direct_url, metadata_location, environment, home page, author,
        # arbitrary license text or cache path can enter the public artifact.
        components[name] = {"name": name, "version": version}
    project = manifest["project"]
    declarations = project["dependencies"] + [value for group in project.get("optional-dependencies", {}).values() for value in group]
    if any(not isinstance(value, str) or "://" in value for value in declarations):
        raise ValueError("Review direct package URLs before publishing a Python inventory")
    return {
        "format": "rivexis-release-inventory-1",
        "ecosystem": "python",
        "scope": "Installed CI distributions, including development and audit tools; not a production-only lock",
        "project": {"name": project["name"], "version": project["version"]},
        "declaredRequirements": project["dependencies"],
        "declaredExtras": project.get("optional-dependencies", {}),
        "componentCount": len(components),
        "components": [components[name] for name in sorted(components)],
        "limitations": [
            "Dependency ranges remain; this inventory does not create a reproducible Python lock",
            "No dependency-edge, license-clearance or vulnerability-free claim is inferred",
            "The existing pip-audit gate remains separate and fail-closed",
        ],
    }


def deno_inventory(lock: dict) -> dict:
    if lock.get("version") != "5":
        raise ValueError("Unsupported Deno lock format")
    components = []
    for registry in ("jsr", "npm", "remote"):
        entries = lock.get(registry, {})
        if not isinstance(entries, dict):
            raise ValueError("Invalid Deno registry map")
        for identifier, data in sorted(entries.items()):
            if registry == "remote":
                parsed = urlsplit(identifier)
                if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
                    raise ValueError("Remote dependency is not a public versioned HTTPS identifier")
                integrity, dependencies = data, []
            else:
                if not re.fullmatch(r"(?:@[a-z0-9._-]+/)?[a-z0-9._-]+@[A-Za-z0-9@._+-]+", identifier):
                    raise ValueError("Invalid Deno package identity")
                if not isinstance(data, dict):
                    raise ValueError("Invalid Deno package record")
                integrity, dependencies = data.get("integrity"), data.get("dependencies", [])
            if not isinstance(integrity, str) or not integrity:
                raise ValueError("Missing Deno package integrity")
            if not isinstance(dependencies, list) or any(not isinstance(value, str) for value in dependencies):
                raise ValueError("Invalid Deno dependency keys")
            components.append({"registry": registry, "identifier": identifier, "integrity": integrity, "dependencyKeys": dependencies})
    if not components:
        raise ValueError("Deno lock has no dependency records")
    return {
        "format": "rivexis-release-inventory-1", "ecosystem": "deno", "lockVersion": lock["version"],
        "scope": "Every JSR, npm and remote entry in the tracked Deno lock, including type-only/transitive records",
        "componentCount": len(components), "components": components,
        "limitations": [
            "Dependency keys preserve Deno lock notation; they are not a normalized reachability graph",
            "Lock inventory does not prove the exact graph bundled by a managed production runtime",
            "No SPDX/CycloneDX validation, license clearance or vulnerability-free claim is inferred",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ecosystem", choices=("python", "deno"))
    parser.add_argument("--input", type=Path, help="pip inspect JSON from the intended isolated environment")
    args = parser.parse_args()
    try:
        if args.ecosystem == "python":
            if args.input is None:
                parser.error("python inventory requires --input")
            manifest_bytes = MANIFEST.read_bytes()
            result = python_inventory(json.loads(args.input.read_text(encoding="utf-8-sig")), tomllib.loads(manifest_bytes.decode()))
            result["manifestSha256"] = hashlib.sha256(manifest_bytes).hexdigest()
        else:
            lock_bytes = DENO_LOCK.read_bytes()
            result = deno_inventory(json.loads(lock_bytes))
            result["lockSha256"] = hashlib.sha256(lock_bytes).hexdigest()
    except (ValueError, KeyError, TypeError, OSError):
        print("Release inventory failed validation; no input contents were exported", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
