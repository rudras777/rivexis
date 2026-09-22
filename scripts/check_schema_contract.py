from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "apps" / "api"
SCHEMA = ROOT / "infrastructure" / "db" / "schema.sql"
SQL = SCHEMA.read_text()


def split_top(value: str) -> list[str]:
    out: list[str] = []
    start = 0
    depth = 0
    in_string = False
    for index, char in enumerate(value):
        if char == "'" and (index == 0 or value[index - 1] != "\\"):
            in_string = not in_string
        if in_string:
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            out.append(value[start:index].strip())
            start = index + 1
    out.append(value[start:].strip())
    return [item for item in out if item]


def table_blocks(sql: str):
    cursor = 0
    while True:
        match = re.search(r"CREATE TABLE\s+([A-Za-z_]\w*)\s*\(", sql[cursor:], re.I)
        if not match:
            return
        table = match.group(1)
        opening = cursor + match.end() - 1
        depth = 0
        in_string = False
        end = opening
        while end < len(sql):
            char = sql[end]
            if char == "'" and (end == 0 or sql[end - 1] != "\\"):
                in_string = not in_string
            if not in_string:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        break
            end += 1
        yield table, sql[opening + 1 : end]
        cursor = end + 1


expected_columns: dict[str, set[str]] = {}
expected_fks: set[tuple[str, str, str, str]] = set()
expected_uniques: set[tuple[str, tuple[str, ...]]] = set()

for table, body in table_blocks(SQL):
    expected_columns[table] = set()
    for item in split_top(body):
        if re.match(r"(?i)^PRIMARY\s+KEY\b", item):
            continue
        if re.match(r"(?i)^UNIQUE\b", item):
            match = re.search(r"\(([^)]+)\)", item)
            if match:
                expected_uniques.add((table, tuple(part.strip() for part in match.group(1).split(","))))
            continue
        if re.match(r"(?i)^CHECK\b", item):
            continue
        column = item.split()[0].strip('"')
        expected_columns[table].add(column)
        reference = re.search(r"(?i)REFERENCES\s+([A-Za-z_]\w*)\s*\(([^)]+)\)", item)
        if reference:
            for referred in [part.strip() for part in reference.group(2).split(",")]:
                expected_fks.add((table, column, reference.group(1), referred))
        if re.search(r"(?i)\bUNIQUE\b", item):
            expected_uniques.add((table, (column,)))

expected_indexes: set[tuple[str, str, tuple[str, ...]]] = set()
for match in re.finditer(
    r"(?im)^CREATE\s+(?:UNIQUE\s+)?INDEX\s+([A-Za-z_]\w*)\s+ON\s+([A-Za-z_]\w*)\s*\(([^;]+)\);",
    SQL,
):
    name, table, raw = match.groups()
    columns = tuple(re.sub(r"(?i)\s+(ASC|DESC)\b.*$", "", part.strip()) for part in split_top(raw))
    expected_indexes.add((name, table, columns))

assert len(expected_columns) == 53, f"Expected 53 tables, got {len(expected_columns)}"

with tempfile.TemporaryDirectory(prefix="rivexis-contract-") as tmp:
    db_path = Path(tmp) / "contract.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["PYTHONPATH"] = str(API)
    subprocess.run(["alembic", "upgrade", "head"], cwd=API, env=env, check=True, capture_output=True, text=True)

    with sqlite3.connect(db_path) as con:
        missing_columns: list[str] = []
        for table, required in expected_columns.items():
            actual = {row[1] for row in con.execute(f'PRAGMA table_info("{table}")')}
            for column in sorted(required - actual):
                missing_columns.append(f"{table}.{column}")
        assert not missing_columns, f"Missing blueprint columns: {missing_columns}"

        actual_fks: set[tuple[str, str, str, str]] = set()
        for table in expected_columns:
            for row in con.execute(f'PRAGMA foreign_key_list("{table}")'):
                actual_fks.add((table, row[3], row[2], row[4]))
        missing_fks = sorted(expected_fks - actual_fks)
        assert not missing_fks, f"Missing blueprint FK edges: {missing_fks}"

        actual_unique: set[tuple[str, tuple[str, ...]]] = set()
        for table in expected_columns:
            for idx in con.execute(f'PRAGMA index_list("{table}")'):
                if not idx[2]:
                    continue
                cols = tuple(row[2] for row in con.execute(f'PRAGMA index_info("{idx[1]}")'))
                if cols:
                    actual_unique.add((table, cols))
        missing_unique = sorted(expected_uniques - actual_unique)
        assert not missing_unique, f"Missing blueprint unique constraints: {missing_unique}"

        actual_indexes: set[tuple[str, str, tuple[str, ...]]] = set()
        for table in expected_columns:
            for idx in con.execute(f'PRAGMA index_list("{table}")'):
                name = idx[1]
                cols = tuple(row[2] for row in con.execute(f'PRAGMA index_info("{name}")'))
                actual_indexes.add((name, table, cols))
        missing_indexes = sorted(expected_indexes - actual_indexes)
        assert not missing_indexes, f"Missing explicit blueprint indexes: {missing_indexes}"

print(
    "Schema contract coverage: PASS "
    f"({sum(len(v) for v in expected_columns.values())} columns; "
    f"{len(expected_fks)} FK edges; {len(expected_uniques)} unique constraints; "
    f"{len(expected_indexes)} named indexes)"
)
