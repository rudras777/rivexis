"""Emit package-lock license metadata without installing packages or claiming legal clearance."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
lock = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))
components = []
for location, package in sorted(lock["packages"].items()):
    if not location or package.get("link"):
        continue
    name = package.get("name") or location.rsplit("node_modules/", 1)[-1]
    components.append({"location": location, "name": name, "version": package.get("version"), "licenseMetadata": package.get("license", "UNSPECIFIED"), "development": package.get("dev", False), "optional": package.get("optional", False)})
print(json.dumps({
    "source": "package-lock.json", "lockfileVersion": lock["lockfileVersion"],
    "scope": "Declared npm lock metadata, including optional platform packages; not an installed-tree or validated SPDX SBOM", 
    "limitations": ["License labels are upstream package metadata, not a legal review", "Native npm SBOM generation currently rejects override/optional-platform graph inconsistencies", "Python ranged dependencies and Deno lock require separate inventory", "No project license or IP assignment is inferred"],
    "componentCount": len(components), "components": components,
}, indent=2))
