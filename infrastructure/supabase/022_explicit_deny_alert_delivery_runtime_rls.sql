-- alert_delivery_runtime is an internal scheduler/control table. Keep its RLS
-- contract explicitly deny-by-default for ordinary roles instead of relying on
-- the absence of policies. The dedicated dispatcher role and service role use
-- their intentionally scoped BYPASSRLS/service paths.

set local role rivexis_migrator;

do $policy$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname='public'
      and tablename='alert_delivery_runtime'
      and policyname='alert_delivery_runtime_deny_public'
  ) then
    create policy alert_delivery_runtime_deny_public
      on public.alert_delivery_runtime
      for all
      to public
      using (false)
      with check (false);
  end if;
end
$policy$;

reset role;
