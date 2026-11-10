import json
import unittest

from scripts.release_dependency_inventory import deno_inventory, python_inventory

MANIFEST = {"project": {"name": "test-project", "version": "1", "dependencies": ["test-package>=1"], "optional-dependencies": {"dev": ["test-tool>=1"]}}}


def inspection(*packages):
    return {"version": "1", "installed": [{"metadata": {"name": name, "version": version}} for name, version in packages]}


class ReleaseInventoryTests(unittest.TestCase):
    def test_python_inventory_covers_sorted_installed_versions_and_declared_ranges(self):
        result = python_inventory(inspection(("Other_Package", "2.1"), ("test-package", "1.0")), MANIFEST)
        self.assertEqual(result["componentCount"], 2)
        self.assertEqual(result["components"], [{"name": "other-package", "version": "2.1"}, {"name": "test-package", "version": "1.0"}])
        self.assertEqual(result["declaredRequirements"], ["test-package>=1"])
        self.assertEqual(result["declaredExtras"], {"dev": ["test-tool>=1"]})

    def test_pip_paths_credentials_and_arbitrary_metadata_never_enter_artifact(self):
        source = inspection(("test-package", "1"))
        source["environment"] = {"secret": "DO_NOT_EXPORT"}
        source["installed"][0].update(metadata_location="DO_NOT_EXPORT", direct_url={"url": "https://DO_NOT_EXPORT@private.example/"})
        source["installed"][0]["metadata"].update(author="DO_NOT_EXPORT", license="DO_NOT_EXPORT", requires_dist=["DO_NOT_EXPORT"])
        self.assertNotIn("DO_NOT_EXPORT", json.dumps(python_inventory(source, MANIFEST)))

    def test_duplicate_normalized_python_names_fail(self):
        with self.assertRaises(ValueError):
            python_inventory(inspection(("a_b", "1"), ("a-b", "2")), MANIFEST)

    def test_missing_python_identity_fails(self):
        with self.assertRaises(ValueError):
            python_inventory({"version": "1", "installed": [{"metadata": {"name": "test"}}]}, MANIFEST)

    def test_unsupported_pip_format_fails(self):
        with self.assertRaises(ValueError):
            python_inventory({"version": "2", "installed": []}, MANIFEST)

    def test_deno_inventory_preserves_all_registries_integrity_and_dependency_keys(self):
        result = deno_inventory({"version": "5", "jsr": {"@test/pkg@1.2.3": {"integrity": "abc", "dependencies": ["npm:other"]}}, "npm": {"other@2.0.0_peer@1.0.0": {"integrity": "sha512-test"}}, "remote": {"https://example.test/v1/mod.ts": "def"}})
        self.assertEqual(result["componentCount"], 3)
        self.assertEqual(result["components"][0]["dependencyKeys"], ["npm:other"])
        self.assertEqual(result["components"][1]["identifier"], "other@2.0.0_peer@1.0.0")

    def test_unsupported_deno_lock_fails(self):
        with self.assertRaises(ValueError):
            deno_inventory({"version": "6"})

    def test_missing_integrity_fails(self):
        with self.assertRaises(ValueError):
            deno_inventory({"version": "5", "npm": {"test@1": {}}})

    def test_malformed_dependency_records_fail(self):
        with self.assertRaises(ValueError):
            deno_inventory({"version": "5", "npm": {"test@1": {"integrity": "a", "dependencies": "not-an-array"}}})

    def test_private_remote_identifiers_are_not_exported(self):
        for url in ("http://example.test/v1.ts", "https://user:secret@example.test/v1.ts", "https://example.test/v1.ts?token=secret", "https://example.test/v1.ts#secret"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                deno_inventory({"version": "5", "remote": {url: "a"}})

    def test_empty_inventories_cannot_masquerade_as_complete(self):
        for operation in (lambda: python_inventory(inspection(), MANIFEST), lambda: deno_inventory({"version": "5"})):
            with self.assertRaises(ValueError):
                operation()

    def test_direct_manifest_urls_require_review_instead_of_public_export(self):
        manifest = {"project": {"name": "test", "version": "1", "dependencies": ["test @ https://secret@private.example/pkg"]}}
        with self.assertRaises(ValueError):
            python_inventory(inspection(("test", "1")), manifest)


if __name__ == "__main__":
    unittest.main()
