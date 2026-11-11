import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.migration_provenance import HEADER_NORMALIZATION, REGISTER, comparison_query, leading_comment_source, normalized_source, source_digest, verify


class MigrationProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.file = "supabase/migrations/20261009133430_example.sql"
        (self.root / self.file).parent.mkdir(parents=True)
        (self.root / self.file).write_text("SELECT 'quoted value';\n", encoding="utf-8")
        self.register = {
            "migrations": [{"version": "20261009135602", "name": "example", "statement_count": 1, "requires_sensitive_statement_review": False}],
            "sourceComparison": {
                "normalization": "CRLF to LF; trim outer space, tab, CR and LF only",
                "matchedProductionEntries": 1, "unreconciledProductionEntries": 0,
                "sensitiveVersionsExcluded": [],
                "sources": [{"file": self.file, "normalizedSha256": source_digest("SELECT 'quoted value';"), "exactMatches": [{"version": "20261009135602", "name": "example", "statement_count": 1}]}],
            },
        }

    def test_current_public_register_and_sources_verify(self):
        self.assertEqual(len(verify(json.loads(REGISTER.read_text()))), 29)

    def test_timestamp_alias_preserves_actual_applied_identity(self):
        self.assertEqual(list(verify(self.register, self.root)), [self.file])
        self.assertNotEqual(self.file.split('/')[-1][:14], self.register['migrations'][0]['version'])

    def test_only_line_endings_and_outer_whitespace_are_normalized(self):
        self.assertEqual(normalized_source(" \t\r\nSELECT 1;\r\n"), "SELECT 1;")
        self.assertNotEqual(source_digest("SELECT 'a b';"), source_digest("SELECT 'ab';"))
        self.assertNotEqual(source_digest("-- review\nSELECT 1;"), source_digest("SELECT 1;"))
        self.assertNotEqual(source_digest("SELECT\r1;"), source_digest("SELECT\n1;"))
        (self.root / self.file).write_bytes(b"SELECT\r'quoted value';\n")
        with self.assertRaisesRegex(ValueError, "fresh comparison"):
            verify(self.register, self.root)

    def test_modified_source_fails_closed(self):
        (self.root / self.file).write_text("SELECT 2;", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "fresh comparison"):
            verify(self.register, self.root)

    def test_extra_unreviewed_source_fails(self):
        (self.root / self.file).with_name("20261009133431_extra.sql").write_text("SELECT 2;")
        with self.assertRaisesRegex(ValueError, "coverage"):
            verify(self.register, self.root)

    def test_path_traversal_and_absolute_paths_fail_before_read(self):
        for path in ("../private.sql", "/private.sql", "supabase/migrations/../private.sql"):
            with self.subTest(path=path):
                self.register['sourceComparison']['sources'][0]['file'] = path
                with self.assertRaisesRegex(ValueError, "source path"):
                    verify(self.register, self.root)

    def test_duplicate_sources_fail(self):
        self.register['sourceComparison']['sources'] *= 2
        with self.assertRaisesRegex(ValueError, "duplicate public"):
            verify(self.register, self.root)

    def test_unknown_and_duplicate_production_versions_fail(self):
        original = copy.deepcopy(self.register)
        self.register['sourceComparison']['sources'][0]['exactMatches'][0]['version'] = '20261009135603'
        with self.assertRaisesRegex(ValueError, "Unknown"):
            verify(self.register, self.root)
        original['migrations'] *= 2
        with self.assertRaisesRegex(ValueError, "Duplicate ledger"):
            verify(original, self.root)

    def test_sensitive_entry_never_certified(self):
        self.register['migrations'][0]['requires_sensitive_statement_review'] = True
        self.register['sourceComparison']['sensitiveVersionsExcluded'] = ['20261009135602']
        with self.assertRaisesRegex(ValueError, "Sensitive"):
            verify(self.register, self.root)

    def test_identity_and_coverage_counts_must_match(self):
        for target, key, value in ((self.register['sourceComparison'], 'matchedProductionEntries', 2),
                                   (self.register['sourceComparison'], 'unreconciledProductionEntries', 1),
                                   (self.register['sourceComparison']['sources'][0]['exactMatches'][0], 'name', 'different')):
            old = target[key]
            target[key] = value
            with self.assertRaises(ValueError):
                verify(self.register, self.root)
            target[key] = old

    def test_query_quotes_public_source_without_executing_it(self):
        query = comparison_query(self.register, self.root)
        self.assertTrue(query.startswith('WITH local_sources'))
        self.assertIn("'SELECT ''quoted value'';", query)
        self.assertIn("ARRAY[]::text[]", query)
        self.assertNotIn('pg_read_file', query)
        self.assertNotIn('SELECT m.statements', query)
        text = "SELECT E'back\\\\slash'; -- 'quoted'\n"
        (self.root / self.file).write_bytes(text.encode())
        self.register['sourceComparison']['sources'][0]['normalizedSha256'] = source_digest(text)
        self.assertIn("E'SELECT E''back\\\\\\\\slash''; -- ''quoted''", comparison_query(self.register, self.root))

    def test_sensitive_exclusion_is_explicit_and_invalid_ledger_rejected(self):
        self.register['migrations'].append({'version': '20260922162311', 'name': 'sensitive', 'statement_count': 1, 'requires_sensitive_statement_review': True})
        self.register['sourceComparison']['unreconciledProductionEntries'] = 1
        self.register['sourceComparison']['sensitiveVersionsExcluded'] = ['20260922162311']
        self.assertIn("ARRAY[E'20260922162311']", comparison_query(self.register, self.root))
        self.register['migrations'][-1]['version'] = "bad'); SELECT 1; --"
        with self.assertRaisesRegex(ValueError, "Invalid ledger"):
            comparison_query(self.register, self.root)

    def test_windows_console_cannot_expand_source_crlf_inside_literals(self):
        text = "SELECT 'quoted value';\r\n\t-- final header\r\n"
        (self.root / self.file).write_bytes(text.encode())
        self.register['sourceComparison']['sources'][0]['normalizedSha256'] = source_digest(text)
        query = comparison_query(self.register, self.root)
        literal = "E'SELECT ''quoted value'';\\r\\n\\t-- final header\\r\\n'"
        self.assertIn(literal, query)
        self.assertIn(literal, query.replace('\n', '\r\n'))

    def test_leading_headers_only_and_internal_comments_are_preserved(self):
        cases = [
            ("-- heading\n SELECT 1;", "SELECT 1;"),
            (" \t-- one\r\n\n -- two\n SELECT 1;", "SELECT 1;"),
            ("-- only", ""),
            ("SELECT '-- literal'; -- internal", "SELECT '-- literal'; -- internal"),
            ("/* block */ SELECT 1;", "/* block */ SELECT 1;"),
            ("-- heading\nDO $$ BEGIN -- internal\n NULL; END $$;", "DO $$ BEGIN -- internal\n NULL; END $$;"),
            ("-- heading\rSELECT 1;", "-- heading\rSELECT 1;"),
            ("SELECT 1;\n-- trailing", "SELECT 1;\n-- trailing"),
            ("-- header\nSELECT 'a b';", "SELECT 'a b';"),
            ("-- header\nSELECT E'\\n';", "SELECT E'\\n';"),
        ]
        for original, expected in cases:
            with self.subTest(original=original):
                self.assertEqual(leading_comment_source(original), expected)

    def header_register(self):
        self.register['migrations'].append({'version': '20261009135603', 'name': 'header', 'statement_count': 1, 'requires_sensitive_statement_review': False})
        self.register['sourceComparison']['unreconciledProductionEntries'] = 1
        self.register['leadingCommentComparison'] = {
            'normalization': HEADER_NORMALIZATION, 'matchedProductionEntries': 2, 'unreconciledProductionEntries': 0,
            'additionalMatches': [{'file': self.file, 'version': '20261009135603', 'name': 'header', 'statement_count': 1}],
        }
        return self.register['leadingCommentComparison']

    def test_header_observation_requires_verified_public_source_digest(self):
        self.header_register()
        verify(self.register, self.root)
        (self.root / self.file).write_text('SELECT 3;')
        with self.assertRaisesRegex(ValueError, 'fresh comparison'):
            verify(self.register, self.root)

    def test_header_observation_does_not_double_count_strict_matches(self):
        header = self.header_register()
        header['additionalMatches'][0].update(version='20261009135602', name='example')
        with self.assertRaisesRegex(ValueError, 'already counted'):
            verify(self.register, self.root)

    def test_header_observation_rejects_unknown_source_or_identity(self):
        header = self.header_register()
        for key, invalid in (('file', '../private.sql'), ('version', '20261009135604'), ('name', 'wrong'), ('statement_count', 2)):
            target = header['additionalMatches'][0]
            old = target[key]
            target[key] = invalid
            with self.assertRaises(ValueError):
                verify(self.register, self.root)
            target[key] = old

    def test_header_observation_cannot_certify_sensitive_history(self):
        self.header_register()
        self.register['migrations'][-1]['requires_sensitive_statement_review'] = True
        self.register['sourceComparison']['sensitiveVersionsExcluded'] = ['20261009135603']
        with self.assertRaisesRegex(ValueError, 'Sensitive'):
            verify(self.register, self.root)

    def test_header_duplicate_and_wrong_coverage_fail(self):
        header = self.header_register()
        header['additionalMatches'] *= 2
        with self.assertRaisesRegex(ValueError, 'already counted'):
            verify(self.register, self.root)
        header['additionalMatches'].pop()
        header['matchedProductionEntries'] = 3
        with self.assertRaisesRegex(ValueError, 'coverage'):
            verify(self.register, self.root)

    def test_header_normalization_is_explicit_and_opt_in(self):
        header = self.header_register()
        self.assertNotIn('regexp_replace', comparison_query(self.register, self.root))
        self.assertIn('regexp_replace', comparison_query(self.register, self.root, ignore_leading_comments=True))
        header['normalization'] = 'remove all whitespace and comments'
        with self.assertRaisesRegex(ValueError, 'normalization'):
            verify(self.register, self.root)


if __name__ == '__main__':
    unittest.main()
