-- The standard Supabase revocations leave non-CRUD table privileges and
-- sequence UPDATE in this project's older default ACLs. Rivexis has no
-- direct Data API access, so remove those residual grants too.
alter default privileges for role postgres in schema public
  revoke all on tables from anon, authenticated, service_role;

alter default privileges for role postgres in schema public
  revoke all on sequences from anon, authenticated, service_role;
