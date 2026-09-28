-- Scheduled alert delivery for the Supabase compatibility runtime.
-- Creates a least-privilege cross-workspace dispatcher role, lease-based queue
-- operations, runtime telemetry, a Vault-backed invocation token and a one-minute
-- Cron -> Edge Function trigger. Outbound provider configuration remains in Edge
-- Function secrets and is never stored in application tables.

create extension if not exists pg_net;
create extension if not exists pg_cron;

grant rivexis_migrator to postgres with set true, inherit false;

do $$
begin
  if not exists(select 1 from pg_roles where rolname='rivexis_alert_dispatcher') then
    create role rivexis_alert_dispatcher
      nologin noinherit bypassrls nosuperuser nocreatedb nocreaterole noreplication;
  else
    alter role rivexis_alert_dispatcher
      nologin noinherit bypassrls nosuperuser nocreatedb nocreaterole noreplication;
  end if;
end
$$;

-- postgres receives SET ROLE only for the migration transaction so the security
-- definer can be created by its final NOLOGIN owner. The membership is revoked
-- before this migration commits.
grant rivexis_alert_dispatcher to postgres with set true, inherit false;

revoke all privileges on all tables in schema public from rivexis_alert_dispatcher;
revoke all privileges on all sequences in schema public from rivexis_alert_dispatcher;
revoke create on schema public from rivexis_alert_dispatcher;
grant usage on schema public to rivexis_alert_dispatcher;
grant usage on schema extensions to rivexis_alert_dispatcher;

set local role rivexis_migrator;

alter table public.alerts
  add column if not exists delivery_claim_token text,
  add column if not exists delivery_claimed_at timestamptz;

create index if not exists alerts_delivery_claim_idx
  on public.alerts(delivery_status,next_delivery_at,delivery_claimed_at);

create table if not exists public.alert_delivery_runtime(
  singleton_id smallint primary key default 1 check(singleton_id=1),
  dispatch_token_hash text not null,
  processor_status text not null default 'SCHEDULED_STARTING',
  sink_status text not null default 'UNKNOWN',
  last_run_at timestamptz,
  last_success_at timestamptz,
  last_error_code text,
  last_processed integer not null default 0 check(last_processed>=0),
  last_delivered integer not null default 0 check(last_delivered>=0),
  last_failed integer not null default 0 check(last_failed>=0),
  updated_at timestamptz not null default clock_timestamp()
);

alter table public.alert_delivery_runtime enable row level security;
revoke all on table public.alert_delivery_runtime from public, anon, authenticated, service_role;

insert into public.alert_delivery_runtime(singleton_id,dispatch_token_hash)
values(1,'PENDING_ROTATION')
on conflict(singleton_id) do nothing;

reset role;

grant select on table public.alerts to rivexis_alert_dispatcher;
grant update(
  delivery_status,delivery_attempts,next_delivery_at,last_delivery_error,
  delivered_at,dead_lettered_at,updated_at,delivery_claim_token,delivery_claimed_at
) on table public.alerts to rivexis_alert_dispatcher;
grant select(id,owner_user_id,name) on table public.workspaces to rivexis_alert_dispatcher;
grant select(id,email) on table public.users to rivexis_alert_dispatcher;
grant select,update on table public.alert_delivery_runtime to rivexis_alert_dispatcher;

grant create on schema public to rivexis_alert_dispatcher;
set local role rivexis_alert_dispatcher;

drop function if exists public.rivexis_edge_alert_dispatch(text,text,jsonb);

create function public.rivexis_edge_alert_dispatch(
  p_action text,
  p_token text,
  p_payload jsonb default '{}'::jsonb
) returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, extensions
as $$
declare
  v_expected_hash text;
  v_supplied_hash text;
  v_now timestamptz := clock_timestamp();
  v_limit integer;
  v_alert_id text;
  v_claim_token text;
  v_success boolean;
  v_error text;
  v_max_attempts integer;
  v_retry_base integer;
  v_attempts integer;
  v_next timestamptz;
  v_delivery_status text;
  v_processor_status text;
  v_sink_status text;
  v_processed integer;
  v_delivered integer;
  v_failed integer;
  result jsonb;
begin
  select r.dispatch_token_hash into v_expected_hash
  from public.alert_delivery_runtime r
  where r.singleton_id=1;

  v_supplied_hash := encode(extensions.digest(coalesce(p_token,''),'sha256'),'hex');
  if v_expected_hash is null or v_expected_hash='PENDING_ROTATION' or v_supplied_hash<>v_expected_hash then
    raise exception 'dispatch authorization failed';
  end if;

  if p_action='claim' then
    v_limit:=least(greatest(coalesce((p_payload->>'limit')::integer,20),1),50);

    with candidates as (
      select a.id
      from public.alerts a
      where a.delivery_status in ('pending','retry')
        and (a.next_delivery_at is null or a.next_delivery_at<=v_now)
        and (a.delivery_claimed_at is null or a.delivery_claimed_at<=v_now-interval '2 minutes')
      order by coalesce(a.next_delivery_at,a.created_at),a.created_at
      for update skip locked
      limit v_limit
    ), claimed as (
      update public.alerts a
      set delivery_claim_token=gen_random_uuid()::text,
          delivery_claimed_at=v_now,
          next_delivery_at=v_now+interval '2 minutes',
          updated_at=v_now
      from candidates c
      where a.id=c.id
      returning a.*
    )
    select coalesce(jsonb_agg(jsonb_build_object(
      'id',c.id,
      'workspace_id',c.workspace_id,
      'workspace_name',w.name,
      'monitor_id',c.monitor_id,
      'analysis_id',c.analysis_id,
      'severity',c.severity,
      'status',c.status,
      'provider_id',c.provider_id,
      'occurrence_count',c.occurrence_count,
      'delivery_status',c.delivery_status,
      'delivery_attempts',c.delivery_attempts,
      'claim_token',c.delivery_claim_token,
      'payload',case when c.payload is null or c.payload='' then '{}'::jsonb else c.payload::jsonb end,
      'created_at',c.created_at,
      'recipient_email',u.email
    ) order by c.created_at),'[]'::jsonb)
    into result
    from claimed c
    left join public.workspaces w on w.id=c.workspace_id
    left join public.users u on u.id=w.owner_user_id;

    return jsonb_build_object('items',result,'lease_seconds',120);
  end if;

  if p_action='mark' then
    v_alert_id:=nullif(p_payload->>'alert_id','');
    v_claim_token:=nullif(p_payload->>'claim_token','');
    v_success:=coalesce((p_payload->>'success')::boolean,false);
    v_error:=lower(coalesce(nullif(p_payload->>'error_code',''),'delivery_error'));
    v_max_attempts:=least(greatest(coalesce((p_payload->>'max_attempts')::integer,5),1),20);
    v_retry_base:=least(greatest(coalesce((p_payload->>'retry_base_seconds')::integer,30),1),3600);

    if v_alert_id is null or v_claim_token is null then raise exception 'invalid delivery claim'; end if;
    if v_error !~ '^[a-z0-9_:-]{1,120}$' then v_error:='delivery_error'; end if;

    select a.delivery_attempts+1 into v_attempts
    from public.alerts a
    where a.id=v_alert_id and a.delivery_claim_token=v_claim_token
    for update;
    if not found then raise exception 'delivery claim not found'; end if;

    if v_success then
      update public.alerts
      set delivery_status='delivered',
          delivery_attempts=v_attempts,
          delivered_at=v_now,
          next_delivery_at=null,
          last_delivery_error=null,
          dead_lettered_at=null,
          delivery_claim_token=null,
          delivery_claimed_at=null,
          updated_at=v_now
      where id=v_alert_id and delivery_claim_token=v_claim_token
      returning delivery_status into v_delivery_status;
    else
      if v_attempts>=v_max_attempts then
        v_delivery_status:='dead_letter';
        v_next:=null;
      else
        v_delivery_status:='retry';
        v_next:=v_now+make_interval(secs=>least(v_retry_base*(2^greatest(v_attempts-1,0)),86400));
      end if;
      update public.alerts
      set delivery_status=v_delivery_status,
          delivery_attempts=v_attempts,
          next_delivery_at=v_next,
          last_delivery_error=v_error,
          dead_lettered_at=case when v_delivery_status='dead_letter' then v_now else null end,
          delivery_claim_token=null,
          delivery_claimed_at=null,
          updated_at=v_now
      where id=v_alert_id and delivery_claim_token=v_claim_token;
    end if;

    return jsonb_build_object(
      'id',v_alert_id,
      'delivery_status',v_delivery_status,
      'delivery_attempts',v_attempts,
      'next_delivery_at',v_next
    );
  end if;

  if p_action='heartbeat' then
    v_processor_status:=upper(coalesce(nullif(p_payload->>'processor_status',''),'DEGRADED'));
    v_sink_status:=upper(coalesce(nullif(p_payload->>'sink_status',''),'UNKNOWN'));
    v_error:=lower(coalesce(nullif(p_payload->>'error_code',''),''));
    v_processed:=greatest(coalesce((p_payload->>'processed')::integer,0),0);
    v_delivered:=greatest(coalesce((p_payload->>'delivered')::integer,0),0);
    v_failed:=greatest(coalesce((p_payload->>'failed')::integer,0),0);

    if v_processor_status not in ('SCHEDULED_STARTING','SCHEDULED_READY','SCHEDULED_NO_SINK','SCHEDULED_SANDBOX','DEGRADED') then
      v_processor_status:='DEGRADED';
    end if;
    if v_sink_status not in ('UNKNOWN','NOT_CONFIGURED','BREVO_READY','BREVO_SANDBOX','DEGRADED') then
      v_sink_status:='DEGRADED';
    end if;
    if v_error<>'' and v_error !~ '^[a-z0-9_:-]{1,120}$' then v_error:='delivery_error'; end if;

    update public.alert_delivery_runtime
    set processor_status=v_processor_status,
        sink_status=v_sink_status,
        last_run_at=v_now,
        last_success_at=case when v_processor_status in ('SCHEDULED_READY','SCHEDULED_SANDBOX') and v_failed=0 then v_now else last_success_at end,
        last_error_code=nullif(v_error,''),
        last_processed=v_processed,
        last_delivered=v_delivered,
        last_failed=v_failed,
        updated_at=v_now
    where singleton_id=1;

    return jsonb_build_object('status','recorded');
  end if;

  raise exception 'unsupported dispatch action';
end;
$$;

revoke all on function public.rivexis_edge_alert_dispatch(text,text,jsonb) from public, anon, authenticated;
grant execute on function public.rivexis_edge_alert_dispatch(text,text,jsonb) to service_role;

reset role;
revoke create on schema public from rivexis_alert_dispatcher;
revoke rivexis_alert_dispatcher from postgres;

drop function if exists public.rivexis_edge_alert_delivery_runtime();

set local role rivexis_migrator;

create function public.rivexis_edge_alert_delivery_runtime()
returns jsonb
language sql
security definer
set search_path = pg_catalog, public
as $$
  select jsonb_build_object(
    'processor_status',r.processor_status,
    'sink_status',r.sink_status,
    'last_run_at',r.last_run_at,
    'last_success_at',r.last_success_at,
    'last_error_code',r.last_error_code,
    'last_processed',r.last_processed,
    'last_delivered',r.last_delivered,
    'last_failed',r.last_failed,
    'schedule','every_minute'
  )
  from public.alert_delivery_runtime r
  where r.singleton_id=1
$$;

revoke all on function public.rivexis_edge_alert_delivery_runtime() from public, anon, authenticated;
grant execute on function public.rivexis_edge_alert_delivery_runtime() to service_role;

reset role;

do $$
declare
  v_token text:=encode(extensions.gen_random_bytes(32),'hex');
  v_secret_id uuid;
begin
  perform set_config('rivexis.dispatch_token_hash',encode(extensions.digest(v_token,'sha256'),'hex'),false);
  select s.id into v_secret_id from vault.secrets s where s.name='rivexis_alert_dispatch_token' limit 1;
  if v_secret_id is null then
    perform vault.create_secret(v_token,'rivexis_alert_dispatch_token','Rivexis internal Cron to alert-dispatch token');
  else
    perform vault.update_secret(v_secret_id,v_token,'rivexis_alert_dispatch_token','Rivexis internal Cron to alert-dispatch token');
  end if;
end
$$;

set local role rivexis_migrator;
update public.alert_delivery_runtime
set dispatch_token_hash=current_setting('rivexis.dispatch_token_hash'),
    processor_status='SCHEDULED_STARTING',
    sink_status='UNKNOWN',
    last_error_code=null,
    updated_at=clock_timestamp()
where singleton_id=1;
reset role;
select set_config('rivexis.dispatch_token_hash','',false);

do $$
declare
  v_job_id bigint;
begin
  for v_job_id in select jobid from cron.job where jobname='rivexis-alert-dispatch'
  loop
    perform cron.unschedule(v_job_id);
  end loop;
end
$$;

select cron.schedule(
  'rivexis-alert-dispatch',
  '* * * * *',
  $cron$
    select net.http_post(
      url:='https://ivszvufdonfgwjpfgwii.supabase.co/functions/v1/rivexis-alert-dispatch',
      headers:=jsonb_build_object(
        'Content-Type','application/json',
        'x-rivexis-dispatch-token',(
          select decrypted_secret
          from vault.decrypted_secrets
          where name='rivexis_alert_dispatch_token'
          limit 1
        )
      ),
      body:=jsonb_build_object('source','supabase-cron'),
      timeout_milliseconds:=15000
    ) as request_id;
  $cron$
);
