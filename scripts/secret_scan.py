from __future__ import annotations

import re
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "openai_like_key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "supabase_secret_key": re.compile(r"\bsb_secret_[A-Za-z0-9_-]{16,}\b"),
    "brevo_key": re.compile(r"\b(?:xkeysib|xsmtpsib)-[A-Za-z0-9_-]{30,}\b"),
}
SUFFIXES={".py",".ts",".tsx",".js",".mjs",".json",".md",".yml",".yaml",".toml",".ini",".env",".example",".sql",".sh"}
SUFFIXES.update({".txt", ".pem", ".key"})


def scan(root: Path) -> list[tuple[str, str]]:
    """Inspect tracked working-tree bytes; never traverse local recovery outputs."""
    root = root.resolve()
    names = subprocess.check_output(["git", "ls-files", "--cached", "-z"], cwd=root)
    hits = []
    for relative in names.decode("utf-8").split("\0"):
        if not relative:
            continue
        path = root / relative
        if path.is_symlink() or not path.is_file():
            continue
        if path.suffix.lower() not in SUFFIXES and path.name not in {".env.example", "Dockerfile"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for kind, pattern in PATTERNS.items():
            if pattern.search(text):
                hits.append((relative, kind))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan tracked source, excluding untracked local credentials and recovery artifacts")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        hits = scan(args.root)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Secret scan could not complete: {type(error).__name__}")
        return 1
    if hits:
        print(f"Potential secrets detected: {hits}")  # Locations/types only; never values.
        return 1
    print("Tracked-source secret-pattern scan: PASS (untracked local files excluded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
