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
LEADING_LINE_COMMENTS = r"^([ \t\n]*--[^\r\n]*(\n|$))*"
HEADER_NORMALIZATION = "Strict normalization, then remove leading -- line comments and outer whitespace only"


def normalized_source(text: str) -> str:
    return text.replace("\r\n", "\n").strip(" \t\r\n")


def source_digest(text: str) -> str:
    return hashlib.sha256(normalized_source(text).encode("utf-8")).hexdigest()


def leading_comment_source(text: str) -> str:
    return re.sub(LEADING_LINE_COMMENTS, "", normalized_source(text), count=1).strip(" \t\r\n")


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
    header = register.get("leadingCommentComparison")
    if header is not None:
        if header["normalization"] != HEADER_NORMALIZATION:
            raise ValueError("Unrecognized header comparison normalization")
        additional_versions: set[str] = set()
        for match in header["additionalMatches"]:
            version = match["version"]
            row = ledger.get(version)
            if match["file"] not in sources or row is None:
                raise ValueError("Unknown header source or production identity")
            if row["requires_sensitive_statement_review"]:
                raise ValueError("Sensitive historical entry cannot be compared here")
            if version in matched_versions or version in additional_versions:
                raise ValueError("Header comparison repeats an already counted identity")
            if row["name"] != match["name"] or row["statement_count"] != match["statement_count"]:
                raise ValueError("Header production identity differs from observation")
            additional_versions.add(version)
        covered = len(matched_versions | additional_versions)
        if covered != header["matchedProductionEntries"] or len(ledger) - covered != header["unreconciledProductionEntries"]:
            raise ValueError("Header comparison coverage count is incorrect")
    return sources


def comparison_query(register: dict, root: Path = ROOT, *, ignore_leading_comments: bool = False) -> str:
    sources = verify(register, root)
    def literal(value: str) -> str:
        # Explicit escape strings are independent of standard_conforming_strings.
        escaped = value.replace("\\", "\\\\").replace("'", "''")
        # Keep source newlines inside SQL escape sequences: Windows stdout must
        # not expand already-preserved CRLF into CRCRLF inside literal data.
        return "E'" + escaped.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t") + "'"
    values = ",\n".join(f"({literal(name)}, {literal(text)})" for name, text in sorted(sources.items()))
    def normalization(expression: str) -> str:
        strict = f"btrim(replace({expression},E'\\r\\n',E'\\n'),E' \\t\\r\\n')"
        if ignore_leading_comments:
            return f"btrim(regexp_replace({strict},{literal(LEADING_LINE_COMMENTS)},''),E' \\t\\r\\n')"
        return strict
    # Source bodies are string literals, never executed. Historical SQL stays server-side.
    return """WITH local_sources(file, sql_text) AS (VALUES
""" + values + """
), compared AS (
 SELECT l.file, m.version, m.name, cardinality(m.statements) AS statement_count,
 """ + normalization("array_to_string(m.statements,E'\\n')") + " = " + normalization("l.sql_text") + """ AS exact_text_match
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
    parser.add_argument("--ignore-leading-comments", action="store_true", help="With --comparison-query only: compare bodies after leading -- headers; preserve all internal content")
    args = parser.parse_args()
    if args.ignore_leading_comments and not args.comparison_query:
        parser.error("--ignore-leading-comments requires --comparison-query")
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    if args.comparison_query:
        print(comparison_query(register, ignore_leading_comments=args.ignore_leading_comments), end="")
    else:
        sources = verify(register)
        print(f"Verified {len(sources)} public SQL source digests; dated production coverage: {register['sourceComparison']['matchedProductionEntries']}/{len(register['migrations'])}. Not an executable baseline.")
        if "leadingCommentComparison" in register:
            print(f"Including separately verified leading-comment matches: {register['leadingCommentComparison']['matchedProductionEntries']}/{len(register['migrations'])}.")


if __name__ == "__main__":
    main()
