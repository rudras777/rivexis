import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.secret_scan import scan


class SecretScanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rivexis-secret-scan-")
        self.root = Path(self.temp.name).resolve()
        self.assertEqual(self.root.parent, Path(tempfile.gettempdir()).resolve())
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)

    def tearDown(self):
        self.temp.cleanup()

    def track(self, name, text):
        self.root.joinpath(name).write_text(text, encoding="utf-8")
        subprocess.run(["git", "add", "--", name], cwd=self.root, check=True)

    def test_untracked_recovery_file_is_not_read(self):
        self.track("safe.py", "print('safe')")
        self.root.joinpath("outputs").mkdir()
        self.root.joinpath("outputs/private.json").write_text("gh" + "p_" + "A" * 36)
        self.assertEqual(scan(self.root), [])

    def test_tracked_secret_has_location_and_type_without_value(self):
        token = "gh" + "p_" + "A" * 36
        self.track("unsafe.txt", token)
        self.assertEqual(scan(self.root), [("unsafe.txt", "github_token")])
        self.assertNotIn(token, str(scan(self.root)))

    def test_brevo_and_supabase_keys_are_detected(self):
        self.track("mail.txt", "xkey" + "sib-" + "A" * 40)
        self.track("db.txt", "sb_" + "secret_" + "B" * 32)
        self.assertEqual(len(scan(self.root)), 2)

    def test_python_optimization_cannot_disable_the_gate(self):
        self.track("unsafe.txt", "gh" + "p_" + "A" * 36)
        script = Path(__file__).with_name("secret_scan.py")
        result = subprocess.run([sys.executable, "-O", str(script), "--root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("github_token", result.stdout)


if __name__ == "__main__":
    unittest.main()
