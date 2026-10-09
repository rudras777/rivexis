-- Defense in depth for legacy server-only tables. Preserve owners, grants,
-- existing data and table-owner behavior; do not FORCE RLS or add client policies.
-- rivexis_app keeps its existing server-only users/data_sources access. These
-- permissive runtime policies do not grant any new SQL privileges.
-- Fail closed if production has acquired client access since the audited baseline.
set lock_timeout='3s';
set statement_timeout='15s';
do $$
declare
  target text;
  targets text[]:=array['alembic_version','assets','chains','contracts','data_sources','entities','entity_labels','oracle_feeds','oracle_observations','prices','protocol_metrics','protocols','provider_health_checks','route_steps','tokens','transaction_traces','transactions','transfers','users'];
begin
  -- Existing production tables belong to the migration role; PostgreSQL's
  -- statement transaction keeps this role switch local and the batch atomic.
  perform set_config('role','rivexis_migrator',true);
  if pg_has_role('anon','rivexis_app','USAGE') or pg_has_role('authenticated','rivexis_app','USAGE') then
    raise exception 'Client inherits trusted runtime role; review required';
  end if;
  foreach target in array targets loop
    if to_regclass(format('public.%I',target)) is null then
      raise exception 'Expected private table is missing: %',target;
    end if;
    if has_table_privilege('anon',format('public.%I',target),'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
       or has_table_privilege('authenticated',format('public.%I',target),'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') then
      raise exception 'Client access changed; review required before enabling RLS: %',target;
    end if;
  end loop;
  foreach target in array targets loop
    execute format('alter table public.%I enable row level security',target);
  end loop;
  create policy rivexis_server_users on public.users to rivexis_app using (true) with check (true);
  create policy rivexis_server_data_sources on public.data_sources to rivexis_app using (true) with check (true);
  execute 'reset role';
end $$;
reset lock_timeout;
reset statement_timeout;
