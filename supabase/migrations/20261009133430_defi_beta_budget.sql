-- Additive only. No existing tables, grants, auth or user data are modified.
create table if not exists public.rivexis_defi_budget (
  scope text primary key, count integer not null check (count >= 0), expires_at timestamptz not null
);
alter table public.rivexis_defi_budget enable row level security;
revoke all on public.rivexis_defi_budget from public, anon, authenticated;
grant select,insert,update,delete on public.rivexis_defi_budget to service_role;
create or replace function public.rivexis_defi_quota(p_wallet text) returns boolean
language plpgsql security invoker set search_path = pg_catalog, public as $$
declare n integer; daily text; wallet_minute text;
begin
  if p_wallet !~ '^0x[0-9a-f]{40}$' then return false; end if;
  daily := 'global:' || to_char(now() at time zone 'UTC','YYYY-MM-DD');
  wallet_minute := 'wallet:' || p_wallet || ':' || to_char(now() at time zone 'UTC','YYYY-MM-DD-HH24-MI');
  delete from public.rivexis_defi_budget where expires_at < now();
  insert into public.rivexis_defi_budget(scope,count,expires_at) values(daily,1,now()+interval '1 day')
    on conflict(scope) do update set count=rivexis_defi_budget.count+1 where rivexis_defi_budget.count<300 returning count into n;
  if n is null then return false; end if;
  n := null;
  insert into public.rivexis_defi_budget(scope,count,expires_at) values(wallet_minute,1,now()+interval '2 minutes')
    on conflict(scope) do update set count=rivexis_defi_budget.count+1 where rivexis_defi_budget.count<4 returning count into n;
  return n is not null;
end $$;
revoke all on function public.rivexis_defi_quota(text) from public,anon,authenticated;
grant execute on function public.rivexis_defi_quota(text) to service_role;

create table if not exists public.rivexis_defi_reports (
  id uuid primary key default gen_random_uuid(), owner_id uuid not null references auth.users(id),
  created_at timestamptz not null default now(), receipt jsonb not null check (octet_length(receipt::text)<=100000)
);
alter table public.rivexis_defi_reports enable row level security;
revoke all on public.rivexis_defi_reports from public,anon,authenticated;
grant select,insert,delete on public.rivexis_defi_reports to service_role;
create index if not exists rivexis_defi_reports_owner on public.rivexis_defi_reports(owner_id,created_at);
create or replace function public.rivexis_defi_save_report(p_owner uuid,p_receipt jsonb) returns uuid
language plpgsql security invoker set search_path=pg_catalog,public as $$
declare report_id uuid;
begin
  perform pg_advisory_xact_lock(hashtextextended(p_owner::text,0));
  if (select count(*) from public.rivexis_defi_reports where owner_id=p_owner)>=20 then raise exception 'Report limit reached: 20 per account'; end if;
  insert into public.rivexis_defi_reports(owner_id,receipt) values(p_owner,p_receipt) returning id into report_id;
  return report_id;
end $$;
revoke all on function public.rivexis_defi_save_report(uuid,jsonb) from public,anon,authenticated;
grant execute on function public.rivexis_defi_save_report(uuid,jsonb) to service_role;
