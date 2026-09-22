-- Local/staging development role split. Production should source credentials from a secret manager.
-- rivexis_admin owns/migrates schema objects; rivexis_app is runtime-only and cannot bypass RLS.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rivexis_app') THEN
    CREATE ROLE rivexis_app LOGIN PASSWORD 'rivexis_app_dev' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT NOBYPASSRLS;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rivexis_alert_worker') THEN
    CREATE ROLE rivexis_alert_worker LOGIN PASSWORD 'rivexis_alert_worker_dev' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT BYPASSRLS;
  END IF;
END $$;

GRANT CONNECT ON DATABASE rivexis TO rivexis_alert_worker;
GRANT USAGE ON SCHEMA public TO rivexis_alert_worker;

GRANT CONNECT ON DATABASE rivexis TO rivexis_app;
GRANT USAGE ON SCHEMA public TO rivexis_app;

-- Existing objects (harmless on a fresh database) and future objects created by
-- the local migration owner receive only runtime DML/sequence privileges.
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO rivexis_app;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO rivexis_app;
ALTER DEFAULT PRIVILEGES FOR ROLE rivexis_admin IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rivexis_app;
ALTER DEFAULT PRIVILEGES FOR ROLE rivexis_admin IN SCHEMA public
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO rivexis_app;
