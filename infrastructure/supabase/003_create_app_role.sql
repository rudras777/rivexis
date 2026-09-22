-- Run as postgres after the Alembic schema has been applied.
-- NOLOGIN is intentional until a secure backend runtime and secret store exist.
create role rivexis_app nologin nosuperuser nocreatedb nocreaterole noinherit nobypassrls;
grant connect on database postgres to rivexis_app;
grant usage on schema public to rivexis_app;
