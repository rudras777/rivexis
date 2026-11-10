"""Verify public migration evidence; emit only an opt-in, read-only comparison query.

No database connection, historical SQL export, migration execution or ledger repair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs/governance/PRODUCTION_MIGRATION_REGISTER.json"
SOURCE_PATH = re.compile(r"(?:supabase/migrations/[0-9]{14}_[a-z0-9_]+|infrastructure/supabase/[0-9]{3}_[a-z0-9_]+)\.sql\Z")
VERSION = re.compile(r"[0-9]{14}\Z")


def normalized_source(text: str) -> str:
    return text.replace("\r\n", "\n").strip(" \t\r\n")


def source_digest(text: str) -> str:
    return hashlib.sha256(normalized_source(text).encode("utf-8")).hexdigest()


def verify(register: dict, root: Path = ROOT) -> dict[str, str]:
    comparison = register["sourceComparison"]
    if comparison["normalization"] != "CRLF to LF; trim outer space, tab, CR and LF only":
        raise ValueError("Unrecognized comparison normalization")
    ledger = {row["version"]: row for row in register["migrations"]}
    if len(ledger) != len(register["migrations"]):
        raise ValueError("Duplicate ledger version")
    for row in ledger.values():
        if not VERSION.fullmatch(row["version"]) or type(row["requires_sensitive_statement_review"]) is not bool:
            raise ValueError("Invalid ledger identity or sensitive-review flag")
    if set(comparison["sensitiveVersionsExcluded"]) != {row["version"] for row in ledger.values() if row["requires_sensitive_statement_review"]}:
        raise ValueError("Sensitive exclusion set differs from ledger")
    sources: dict[str, str] = {}
    matched_versions: set[str] = set()
    for entry in comparison["sources"]:
        name = entry["file"]
        if not SOURCE_PATH.fullmatch(name) or name in sources:
            raise ValueError("Invalid or duplicate public source path")
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Public source resolves outside repository")
        text = path.read_bytes().decode("utf-8")
        if source_digest(text) != entry["normalizedSha256"]:
            raise ValueError(f"Public source changed; fresh comparison required: {name}")
        sources[name] = text
        for match in entry["exactMatches"]:
            version = match["version"]
            row = ledger.get(version)
            if not VERSION.fullmatch(version) or row is None:
                raise ValueError("Unknown production version")
            if row["requires_sensitive_statement_review"]:
                raise ValueError("Sensitive historical entry cannot be compared here")
            if match["name"] != row["name"] or match["statement_count"] != row["statement_count"]:
                raise ValueError("Production identity differs from observation")
            matched_versions.add(version)
    actual_sources = {p.relative_to(root).as_posix() for directory in ("supabase/migrations", "infrastructure/supabase") for p in (root / directory).glob("*.sql")}
    if set(sources) != actual_sources:
        raise ValueError("Public SQL source coverage changed; review the register")
    if len(matched_versions) != comparison["matchedProductionEntries"]:
        raise ValueError("Matched production count is incorrect")
    if len(ledger) - len(matched_versions) != comparison["unreconciledProductionEntries"]:
        raise ValueError("Unreconciled production count is incorrect")
    return sources


def comparison_query(register: dict, root: Path = ROOT) -> str:
    sources = verify(register, root)
    def literal(value: str) -> str:
        # Explicit escape strings are independent of standard_conforming_strings.
        return "E'" + value.replace("\\", "\\\\").replace("'", "''") + "'"
    values = ",\n".join(f"({literal(name)}, {literal(text)})" for name, text in sorted(sources.items()))
    # Source bodies are string literals, never executed. Historical SQL stays server-side.
    return """WITH local_sources(file, sql_text) AS (VALUES
""" + values + """
), compared AS (
 SELECT l.file, m.version, m.name, cardinality(m.statements) AS statement_count,
 btrim(replace(array_to_string(m.statements, E'\\n'), E'\\r\\n', E'\\n'), E' \\t\\r\\n') =
 btrim(replace(l.sql_text, E'\\r\\n', E'\\n'), E' \\t\\r\\n') AS exact_text_match
 FROM local_sources l CROSS JOIN supabase_migrations.schema_migrations m
 WHERE NOT m.version = ANY(ARRAY[""" + ",".join(literal(row["version"]) for row in register["migrations"] if row["requires_sensitive_statement_review"]) + """]::text[])
)
SELECT l.file, coalesce(jsonb_agg(jsonb_build_object('version', c.version, 'name', c.name,
 'statement_count', c.statement_count)) FILTER (WHERE c.exact_text_match), '[]'::jsonb) AS exact_matches
FROM local_sources l LEFT JOIN compared c USING(file) GROUP BY l.file ORDER BY l.file;
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison-query", action="store_true", help="Print a SELECT query containing reviewed public source; never connects or executes")
    args = parser.parse_args()
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    if args.comparison_query:
        print(comparison_query(register), end="")
    else:
        sources = verify(register)
        print(f"Verified {len(sources)} public SQL source digests; dated production coverage: {register['sourceComparison']['matchedProductionEntries']}/{len(register['migrations'])}. Not an executable baseline.")


if __name__ == "__main__":
    main()
