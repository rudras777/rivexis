-- Rivexis uses Supabase as a private PostgreSQL service behind FastAPI.
-- Public Data API grants must be explicit, never inherited by new Alembic tables.
-- Run as the postgres role before the application Alembic migrations.
alter default privileges for role postgres in schema public
  revoke select, insert, update, delete on tables from anon, authenticated, service_role;

alter default privileges for role postgres in schema public
  revoke execute on functions from anon, authenticated, service_role;

alter default privileges for role postgres in schema public
  revoke usage, select on sequences from anon, authenticated, service_role;

alter default privileges for role postgres in schema public
  revoke execute on functions from public;
