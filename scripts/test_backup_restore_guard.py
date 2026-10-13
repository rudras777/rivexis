import os
import io
import runpy
import subprocess
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch

from backup_restore_guard import require_disposable_restore, run_postgres_tool


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

    def test_both_drills_deny_production_before_invoking_tools(self):
        scripts = Path(__file__).resolve().parent
        env = {
            'RIVEXIS_BACKUP_SOURCE_DATABASE_URL': self.source,
            'RIVEXIS_BACKUP_RESTORE_DATABASE_URL': self.source,
            'RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY': 'true',
        }
        with patch.dict(os.environ, env, clear=True), patch('subprocess.run') as run:
            with self.assertRaises(SystemExit):
                runpy.run_path(str(scripts / 'certify_postgres_dr.py'))
            run.assert_not_called()
            legacy = runpy.run_path(str(scripts / 'certify_backup_restore.py'))
            with self.assertRaises(SystemExit):
                legacy['postgres_certification']()
            run.assert_not_called()

    def test_tools_preserve_connections_without_credentials_in_argv(self):
        source = 'postgresql://qa%40user:secret%3Avalue@db.example.com:6543/postgres?sslmode=require'
        target = 'postgresql://restore:local-secret@127.0.0.1:5433/rivexis_restore_dr'
        inherited = {'PGHOST': 'wrong', 'PGPORT': '1', 'PGDATABASE': 'wrong',
                     'PGPASSWORD': 'wrong', 'PGUSER': 'wrong',
                     'RIVEXIS_BACKUP_SOURCE_DATABASE_URL': source,
                     'RIVEXIS_BACKUP_RESTORE_DATABASE_URL': target}
        with patch.dict(os.environ, inherited, clear=True), patch('subprocess.run') as run:
            require_disposable_restore(source, target)
            for tool in ('pg_dump', 'pg_restore', 'psql'):
                connection = source if tool == 'pg_dump' else target
                with self.subTest(tool=tool):
                    run_postgres_tool(tool, ['--version'], connection)
                    argv = run.call_args.args[0]
                    env = run.call_args.kwargs['env']
                    self.assertNotIn(connection, argv)
                    self.assertNotIn('secret', ' '.join(argv))
                    self.assertNotIn('RIVEXIS_BACKUP_SOURCE_DATABASE_URL', env)
                    self.assertNotIn('RIVEXIS_BACKUP_RESTORE_DATABASE_URL', env)
                    if tool == 'pg_dump':
                        self.assertEqual((env['PGHOST'], env['PGPORT'], env['PGUSER'], env['PGPASSWORD'], env['PGSSLMODE']),
                                         ('db.example.com', '6543', 'qa@user', 'secret:value', 'require'))
                    else:
                        self.assertEqual((env['PGHOST'], env['PGPORT'], env['PGDATABASE'], env['PGPASSWORD']),
                                         ('127.0.0.1', '5433', 'rivexis_restore_dr', 'local-secret'))
                    if tool == 'pg_restore':
                        self.assertEqual(argv[2:4], ['--dbname', 'rivexis_restore_dr'])

    def test_command_failures_do_not_include_sensitive_output(self):
        failures = [subprocess.CalledProcessError(1, ['pg_dump', self.source],
                                                 output=self.source, stderr='secret'),
                    subprocess.TimeoutExpired(['pg_dump', self.source], 900, output='secret'),
                    OSError('secret'), ValueError(self.source)]
        with patch.dict(os.environ, {}, clear=True):
            for failure in failures:
                with self.subTest(failure=type(failure).__name__), patch('subprocess.run', side_effect=failure):
                    with self.assertRaises(SystemExit) as error:
                        run_postgres_tool('pg_dump', [], self.source)
                    self.assertNotIn('secret', str(error.exception))
                    self.assertNotIn(self.source, str(error.exception))

    def test_both_real_drills_use_secret_safe_commands(self):
        scripts = Path(__file__).resolve().parent
        target = 'postgresql://restore:local-secret@localhost/rivexis_restore_dr'
        env = {'RIVEXIS_BACKUP_SOURCE_DATABASE_URL': self.source,
               'RIVEXIS_BACKUP_RESTORE_DATABASE_URL': target,
               'RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY': 'true'}

        def fake_command(argv, **kwargs):
            self.assertNotIn('secret', ' '.join(argv))
            self.assertNotIn(self.source, argv)
            self.assertNotIn(target, argv)
            if argv[0] == 'pg_dump':
                Path(argv[argv.index('--file') + 1]).write_bytes(b'fixture archive')
                self.assertEqual(kwargs['env']['PGHOST'], 'db.example.com')
            elif kwargs['env']['PGHOST'] == 'localhost':
                self.assertEqual(kwargs['env']['PGDATABASE'], 'rivexis_restore_dr')
            return subprocess.CompletedProcess(argv, 0, stdout='55\n', stderr='')

        with patch.dict(os.environ, env, clear=True), patch('shutil.which', return_value='fixture-tool'), patch('subprocess.run', side_effect=fake_command) as run, redirect_stdout(io.StringIO()):
            runpy.run_path(str(scripts / 'certify_postgres_dr.py'))
            self.assertEqual([call.args[0][0] for call in run.call_args_list], ['psql', 'pg_dump', 'pg_restore', 'psql'])
            run.reset_mock()
            legacy = runpy.run_path(str(scripts / 'certify_backup_restore.py'))
            legacy['postgres_certification']()
            self.assertEqual([call.args[0][0] for call in run.call_args_list], ['pg_dump', 'pg_restore'])


if __name__ == '__main__':
    unittest.main()
