import os
import unittest
from unittest.mock import patch

from backup_restore_guard import require_disposable_restore


class RestoreGuardTests(unittest.TestCase):
    source = 'postgresql://qa:secret@db.example.com/postgres'

    def test_valid_local_disposable_targets(self):
        with patch.dict(os.environ, {}, clear=True):
            for host in ('localhost', '127.0.0.1', '[::1]'):
                with self.subTest(host=host):
                    require_disposable_restore(self.source, f'postgresql://qa:secret@{host}/rivexis_restore_dr')

    def test_unsafe_target_scenarios(self):
        cases = [
            self.source,
            'postgresql://different:secret@db.example.com/postgres',
            'postgresql://qa:secret@db.example.com/rivexis_restore_dr',
            'postgresql://qa:secret@localhost/postgres',
            'postgresql://qa:secret@localhost/rivexis_restore_dr?host=db.example.com',
            'postgresql://qa:secret@localhost/rivexis_restore_dr?hostaddr=192.0.2.1',
            'postgresql://qa:secret@localhost/rivexis_restore_dr?service=production',
            'postgresql://qa:secret@localhost/rivexis_restore_dr?options=unsafe',
            'postgresql://qa:secret@localhost/rivexis_restore_dr?sslmode=bad',
            'postgresql://qa:secret@localhost/rivexis_restore_dr#ignored',
            'postgresql://qa:secret@localhost:bad/rivexis_restore_dr',
            'postgresql://qa:secret@localhost/rivexis_restore_dr%2Fextra',
            'mysql://qa:secret@localhost/rivexis_restore_dr',
        ]
        with patch.dict(os.environ, {}, clear=True):
            for target in cases:
                with self.subTest(target=target), self.assertRaises(SystemExit) as error:
                    require_disposable_restore(self.source, target)
                self.assertNotIn('secret', str(error.exception))

    def test_local_aliases_cannot_restore_source(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(SystemExit):
            require_disposable_restore('postgresql://qa:secret@localhost/rivexis_restore_dr',
                                       'postgres://other:secret@127.0.0.1:5432/rivexis_restore_dr')

    def test_inherited_routing_is_rejected(self):
        for key in ('PGHOSTADDR', 'PGSERVICE', 'PGSERVICEFILE', 'PGOPTIONS'):
            with self.subTest(key=key), patch.dict(os.environ, {key: 'unsafe'}, clear=True), self.assertRaises(SystemExit):
                require_disposable_restore(self.source, 'postgresql://qa:secret@localhost/rivexis_restore_dr')


if __name__ == '__main__':
    unittest.main()
