from collections import Counter
from pathlib import Path


def test_env_example_has_unique_active_keys() -> None:
    env_path = Path(__file__).resolve().parents[3] / ".env.example"
    keys = []
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        keys.append(line.split("=", 1)[0])

    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
    assert not duplicates, f"Duplicate active keys in .env.example: {duplicates}"
