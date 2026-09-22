#!/usr/bin/env python3
from __future__ import annotations
import hashlib, os, shutil, sqlite3, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];API=ROOT/'apps'/'api'

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def sqlite_certification():
    with tempfile.TemporaryDirectory(prefix='rivexis-backup-') as tmp:
        tmp=Path(tmp);source=tmp/'source.db';backup=tmp/'backup.db';restore=tmp/'restore.db'
        env=os.environ.copy();env['DATABASE_URL']=f'sqlite:///{source}';env['PYTHONPATH']=str(API)
        subprocess.run(['alembic','upgrade','head'],cwd=API,env=env,check=True,capture_output=True,text=True)
        with sqlite3.connect(source) as con:
            con.execute("INSERT INTO users(id,email,password_hash,role,token_version,created_at) VALUES(?,?,?,?,?,datetime('now'))",('backup-marker','backup-cert@rivexis.local','marker','Analyst',0));con.commit()
        with sqlite3.connect(source) as src, sqlite3.connect(backup) as dst:src.backup(dst)
        shutil.copy2(backup,restore)
        with sqlite3.connect(restore) as con:
            integrity=con.execute('PRAGMA integrity_check').fetchone()[0]
            marker=con.execute("SELECT count(*) FROM users WHERE id='backup-marker'").fetchone()[0]
            tables=con.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name!='alembic_version'").fetchone()[0]
        assert integrity=='ok' and marker==1 and tables==53,(integrity,marker,tables)
        print(f'Backup/restore certification: PASS (SQLite procedural gate; 53 tables; sha256={sha256(backup)})')

def postgres_certification():
    src=os.getenv('RIVEXIS_BACKUP_SOURCE_DATABASE_URL','').strip();dst=os.getenv('RIVEXIS_BACKUP_RESTORE_DATABASE_URL','').strip()
    if not (src and dst):
        print('SKIP PostgreSQL backup/restore certification: set RIVEXIS_BACKUP_SOURCE_DATABASE_URL and RIVEXIS_BACKUP_RESTORE_DATABASE_URL')
        return
    if os.getenv('RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY','false').lower() not in {'1','true','yes','on'}:
        print('SKIP PostgreSQL backup/restore certification: set RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY=true only for an approved disposable restore target')
        return
    if not shutil.which('pg_dump') or not shutil.which('pg_restore'):
        raise SystemExit('PostgreSQL backup certification requires pg_dump and pg_restore')
    with tempfile.TemporaryDirectory(prefix='rivexis-pg-backup-') as tmp:
        dump=Path(tmp)/'rivexis.dump'
        subprocess.run(['pg_dump','--format=custom','--no-owner','--file',str(dump),src],check=True)
        subprocess.run(['pg_restore','--clean','--if-exists','--no-owner','--dbname',dst,str(dump)],check=True)
        print(f'PostgreSQL backup/restore certification: PASS (sha256={sha256(dump)})')

sqlite_certification();postgres_certification()
