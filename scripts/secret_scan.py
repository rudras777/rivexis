from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_NAMES = {"MASTER_BUILD_SPEC.txt"}
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "openai_like_key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
}
SUFFIXES={".py",".ts",".tsx",".js",".mjs",".json",".md",".yml",".yaml",".toml",".ini",".env",".example",".sql",".sh"}
hits=[]
for p in ROOT.rglob("*"):
    if not p.is_file() or p.name in EXCLUDE_NAMES or ".pytest_cache" in p.parts or "node_modules" in p.parts:
        continue
    if p.suffix.lower() not in SUFFIXES and p.name not in {".env.example","Dockerfile"}:
        continue
    try:text=p.read_text(errors="ignore")
    except OSError:continue
    for name,pattern in PATTERNS.items():
        if pattern.search(text):hits.append((str(p.relative_to(ROOT)),name))
assert not hits, f"Potential secrets detected: {hits}"
print("Repository secret-pattern scan: PASS")
