import hashlib
import json
import unittest

from scripts.python_ci_lock import parse_lock, render_lock, reviewed_packages, verify_versions, wheel_hashes

MANIFEST = b'[project]\nname="rivexis-api"\nversion="1.0"\n'
DIGEST = "a" * 64


def inventory():
    return {"format": "rivexis-release-inventory-1", "ecosystem": "python", "manifestSha256": hashlib.sha256(MANIFEST).hexdigest(), "componentCount": 2, "components": [{"name": "rivexis-api", "version": "1.0"}, {"name": "test-package", "version": "2.0"}]}


def release():
    return {"info": {"name": "test-package", "version": "2.0"}, "urls": [{"packagetype": "bdist_wheel", "yanked": False, "digests": {"sha256": DIGEST}}]}


class PythonCiLockTests(unittest.TestCase):
    def test_versions_are_taken_unchanged_from_reviewed_inventory(self):
        self.assertEqual(reviewed_packages(inventory(), MANIFEST), {"test-package": "2.0"})

    def test_mismatched_source_manifest_fails(self):
        with self.assertRaises(ValueError):
            reviewed_packages(inventory(), MANIFEST + b"# changed\n")

    def test_missing_project_and_duplicate_identity_fail(self):
        for components in ([{"name": "test-package", "version": "2.0"}], [{"name": "rivexis-api", "version": "1.0"}] * 2):
            value = inventory()
            value.update(components=components, componentCount=len(components))
            with self.subTest(components=components), self.assertRaises(ValueError):
                reviewed_packages(value, MANIFEST)

    def test_private_urls_cannot_be_package_identities(self):
        value = inventory()
        value["components"][1]["name"] = "https://private.example/secret"
        with self.assertRaises(ValueError):
            reviewed_packages(value, MANIFEST)

    def test_sources_and_yanked_wheels_are_excluded(self):
        value = release()
        value["urls"] += [{"packagetype": "sdist", "digests": {"sha256": "b" * 64}}, {"packagetype": "bdist_wheel", "yanked": True, "digests": {"sha256": "c" * 64}}]
        self.assertEqual(wheel_hashes(value, "test-package", "2.0"), [DIGEST])

    def test_wrong_pypi_identity_fails(self):
        with self.assertRaises(ValueError):
            wheel_hashes(release(), "another-package", "2.0")

    def test_invalid_digest_and_missing_wheels_fail(self):
        for urls in ([], [{"packagetype": "sdist"}], [{"packagetype": "bdist_wheel", "digests": {"sha256": "invalid"}}]):
            value = release()
            value["urls"] = urls
            with self.subTest(urls=urls), self.assertRaises(ValueError):
                wheel_hashes(value, "test-package", "2.0")

    def test_rendering_is_deterministic_and_round_trips_all_versions(self):
        packages = {"test-package": "2.0"}
        text = render_lock(packages, {"test-package": release()}, "123")
        self.assertEqual(text, render_lock(packages, {"test-package": json.loads(json.dumps(release()))}, "123"))
        self.assertEqual(parse_lock(text), packages)

    def test_unsafe_lock_directives_and_unhashed_requirements_fail(self):
        for text in ("--extra-index-url https://private.example/", "test-package==2.0", "test-package @ file:/private/pkg", "", "--hash=sha256:" + DIGEST):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_lock(text)

    def test_missing_hash_on_earlier_entry_and_duplicates_fail(self):
        for text in ("first==1\nsecond==2\n --hash=sha256:" + DIGEST, ("first==1\n --hash=sha256:" + DIGEST + "\n") * 2):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_lock(text)

    def test_installed_versions_must_match_without_missing_or_extra_packages(self):
        expected = {"test-package": "2.0"}
        verify_versions(expected, [("Test_Package", "2.0")])
        for actual in ([], [("test-package", "3.0")], [("test-package", "2.0"), ("extra", "1")], [("test-package", "2.0"), ("Test_Package", "2.0")]):
            with self.subTest(actual=actual), self.assertRaises(ValueError):
                verify_versions(expected, actual)

    def test_source_run_cannot_inject_lock_content(self):
        with self.assertRaises(ValueError):
            render_lock({"test-package": "2.0"}, {"test-package": release()}, "123\n--extra-index-url https://private.example/")


if __name__ == "__main__":
    unittest.main()
