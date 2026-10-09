-- Run as postgres after the guarded migration. No lasting data changes.
begin;
do $$
begin
  if exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind='r' and not c.relrowsecurity) then
    raise exception 'Public table without RLS';
  end if;
  if has_table_privilege('anon','public.users','SELECT,INSERT,UPDATE,DELETE') or has_table_privilege('authenticated','public.users','SELECT,INSERT,UPDATE,DELETE') then
    raise exception 'Client users grant widened';
  end if;
end $$;
set local role rivexis_app;
select count(*) as retained_runtime_user_read from public.users;
select count(*) as retained_runtime_source_read from public.data_sources;
set local role anon;
do $$
begin
  begin
    perform 1 from public.users;
    raise exception 'Anon user read unexpectedly succeeded';
  exception when insufficient_privilege then null;
  end;
end $$;
set local role authenticated;
do $$
begin
  begin
    perform 1 from public.users;
    raise exception 'Authenticated direct user read unexpectedly succeeded';
  exception when insufficient_privilege then null;
  end;
end $$;
reset role;
rollback;
