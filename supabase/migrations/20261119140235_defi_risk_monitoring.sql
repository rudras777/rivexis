-- Additive candidate only. Does not schedule a job, enable delivery, enroll a
-- user, or alter existing tables/authentication mail. Apply to fixtures first.
begin;
create table public.rivexis_defi_monitor_runtime (
  singleton boolean primary key default true check(singleton),
  last_cycle_at timestamptz, evaluation_enabled boolean not null default false,
  email_enabled boolean not null default false, last_cleanup_at timestamptz
);
insert into public.rivexis_defi_monitor_runtime(singleton) values(true);
create table public.rivexis_defi_monitor_rules (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null unique references auth.users(id) on delete cascade,
  wallet text not null check(wallet ~ '^0x[0-9a-f]{40}$' and wallet <> '0x0000000000000000000000000000000000000000'),
  coverage text not null check(coverage in ('aave','morpho-wbtc','combined')),
  threshold_raw text not null check(threshold_raw ~ '^[0-9]{19}$' and threshold_raw::numeric between 1000000000000000000 and 3000000000000000000),
  recovery_raw text not null check(recovery_raw ~ '^[0-9]{19}$' and recovery_raw::numeric between 1050000000000000000 and 4000000000000000000),
  enabled boolean not null default false, email_opt_in boolean not null default false,
  version bigint not null default 1, episode bigint not null default 0,
  condition text not null default 'UNKNOWN' check(condition in ('UNKNOWN','CLEAR','BREACH')),
  last_status text not null default 'NEVER_EVALUATED',
  last_attempt_at timestamptz, last_success_at timestamptz,
  block_number text, block_hash text, block_timestamp bigint, health_raw text,
  lease_token uuid, lease_until timestamptz, next_evaluation_at timestamptz not null default now(),
  failures integer not null default 0,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  check(recovery_raw::numeric >= threshold_raw::numeric + 50000000000000000)
);
create index rivexis_defi_monitor_due on public.rivexis_defi_monitor_rules(next_evaluation_at) where enabled;
create table public.rivexis_defi_monitor_events (
  id uuid primary key default gen_random_uuid(),
  rule_id uuid not null references public.rivexis_defi_monitor_rules(id) on delete cascade,
  owner_id uuid not null references auth.users(id) on delete cascade,
  episode bigint not null, kind text not null check(kind in ('BREACH','RECOVERY')),
  rule_version bigint not null, block_number text not null, block_hash text not null,
  created_at timestamptz not null default now(), expires_at timestamptz not null default(now()+interval '1 hour'),
  state text not null default 'QUEUED' check(state in ('QUEUED','SENDING','ACCEPTED','DELIVERED','BOUNCED','FAILED','UNKNOWN','EXPIRED','CANCELLED','INVALIDATED')),
  message_id text, attempts integer not null default 0, next_attempt_at timestamptz not null default now(),
  delivery_token uuid, delivery_started_at timestamptz, updated_at timestamptz not null default now(),
  error_code text, unique(rule_id,episode,kind)
);
create index rivexis_defi_monitor_outbox on public.rivexis_defi_monitor_events(next_attempt_at) where state='QUEUED';
create index rivexis_defi_monitor_owner_events on public.rivexis_defi_monitor_events(owner_id,created_at desc);
alter table public.rivexis_defi_monitor_runtime enable row level security;
alter table public.rivexis_defi_monitor_rules enable row level security;
alter table public.rivexis_defi_monitor_events enable row level security;
revoke all on public.rivexis_defi_monitor_runtime,public.rivexis_defi_monitor_rules,public.rivexis_defi_monitor_events from public,anon,authenticated;
grant select(id,owner_id,wallet,coverage,threshold_raw,recovery_raw,enabled,email_opt_in,version,episode,condition,last_status,last_attempt_at,last_success_at,block_number,block_hash,block_timestamp,health_raw,next_evaluation_at,failures,created_at,updated_at) on public.rivexis_defi_monitor_rules to authenticated;
grant select(id,rule_id,owner_id,episode,kind,rule_version,block_number,block_hash,created_at,expires_at,state,message_id,attempts,next_attempt_at,updated_at,error_code) on public.rivexis_defi_monitor_events to authenticated;
create policy defi_monitor_owner_read on public.rivexis_defi_monitor_rules for select to authenticated using(owner_id=(select auth.uid()));
create policy defi_monitor_event_owner_read on public.rivexis_defi_monitor_events for select to authenticated using(owner_id=(select auth.uid()));
grant all on public.rivexis_defi_monitor_runtime,public.rivexis_defi_monitor_rules,public.rivexis_defi_monitor_events to service_role;

-- Service-only invoker functions. The Edge API supplies the verified auth user;
-- client roles cannot pass an arbitrary owner or mutate evaluation evidence.
create function public.rivexis_defi_monitor_manage(p_owner uuid,p_action text,p_payload jsonb default '{}')
returns jsonb language plpgsql security invoker set search_path='' as $$
declare r public.rivexis_defi_monitor_rules; rt public.rivexis_defi_monitor_runtime; events jsonb; active boolean;
begin
  select * into rt from public.rivexis_defi_monitor_runtime where singleton;
  active := rt.evaluation_enabled and rt.last_cycle_at>now()-interval '15 minutes';
  if p_action='save' then
    -- Serialize global admission as well as same-owner saves.
    perform 1 from public.rivexis_defi_monitor_runtime where singleton for update;
    if not active and (p_payload->>'enabled')::boolean then raise exception 'Monitoring runtime is inactive'; end if;
    if not exists(select 1 from auth.users where id=p_owner and email_confirmed_at is not null) then raise exception 'Verified owner required'; end if;
    if (p_payload->>'enabled')::boolean and
      (select count(*) from public.rivexis_defi_monitor_rules where enabled and owner_id<>p_owner)>=3 then raise exception 'Bounded monitoring capacity reached'; end if;
    insert into public.rivexis_defi_monitor_rules(owner_id,wallet,coverage,threshold_raw,recovery_raw,enabled,email_opt_in)
    values(p_owner,p_payload->>'wallet',p_payload->>'coverage',p_payload->>'threshold_raw',p_payload->>'recovery_raw',(p_payload->>'enabled')::boolean,(p_payload->>'email_opt_in')::boolean)
    on conflict(owner_id) do update set wallet=excluded.wallet,coverage=excluded.coverage,threshold_raw=excluded.threshold_raw,recovery_raw=excluded.recovery_raw,enabled=excluded.enabled,email_opt_in=excluded.email_opt_in,
      version=public.rivexis_defi_monitor_rules.version+1,condition='UNKNOWN',last_status='NEVER_EVALUATED',last_success_at=null,block_number=null,block_hash=null,block_timestamp=null,health_raw=null,
      failures=0,lease_token=null,lease_until=null,next_evaluation_at=now(),updated_at=now()
    where (public.rivexis_defi_monitor_rules.wallet,public.rivexis_defi_monitor_rules.coverage,public.rivexis_defi_monitor_rules.threshold_raw,public.rivexis_defi_monitor_rules.recovery_raw,public.rivexis_defi_monitor_rules.enabled,public.rivexis_defi_monitor_rules.email_opt_in)
      is distinct from (excluded.wallet,excluded.coverage,excluded.threshold_raw,excluded.recovery_raw,excluded.enabled,excluded.email_opt_in) returning * into r;
    -- Changing consent or a rule invalidates pending jobs. An in-flight send may
    -- already have been accepted; keep it UNKNOWN for reconciliation, never replay.
    if r.id is not null then
      update public.rivexis_defi_monitor_events set state=case when state='SENDING' then 'UNKNOWN' else 'CANCELLED' end,updated_at=now()
      where owner_id=p_owner and state in ('QUEUED','SENDING');
    end if;
  elsif p_action<>'read' then raise exception 'Unsupported action'; end if;
  select * into r from public.rivexis_defi_monitor_rules where owner_id=p_owner;
  select coalesce(jsonb_agg(x),'[]') into events from (
    select id,kind,state,created_at,updated_at,block_number,block_hash,error_code from public.rivexis_defi_monitor_events where owner_id=p_owner order by created_at desc,id limit 20
  ) x;
  return jsonb_build_object('runtime',jsonb_build_object('state',case when active then 'SCHEDULED' else 'INACTIVE' end,'email',active and rt.email_enabled,'interval_minutes',30,'last_cycle_at',rt.last_cycle_at),
    'rule',case when r.id is null then null else to_jsonb(r)-'lease_token'-'lease_until' end,'events',events);
end $$;

create function public.rivexis_defi_monitor_job(p_action text,p_payload jsonb default '{}')
returns jsonb language plpgsql security invoker set search_path='' as $$
declare r public.rivexis_defi_monitor_rules; e public.rivexis_defi_monitor_events; t uuid; result jsonb; next_condition text; expected_condition text; event_kind text; new_episode bigint; cap integer; recipient text;
begin
  if p_action='heartbeat' then
    update public.rivexis_defi_monitor_events set state='UNKNOWN',error_code='WORKER_OUTCOME_UNKNOWN',updated_at=now() where state='SENDING' and delivery_started_at<now()-interval '2 minutes';
    update public.rivexis_defi_monitor_events set state='EXPIRED',updated_at=now() where state='QUEUED' and expires_at<=now();
    if exists(select 1 from public.rivexis_defi_monitor_runtime where singleton and (last_cleanup_at is null or last_cleanup_at<now()-interval '1 day')) then
      delete from public.rivexis_defi_monitor_events where created_at<now()-interval '90 days' and state not in ('UNKNOWN','SENDING');
      update public.rivexis_defi_monitor_runtime set last_cleanup_at=now() where singleton;
    end if;
    update public.rivexis_defi_monitor_runtime set last_cycle_at=now(),evaluation_enabled=coalesce((p_payload->>'evaluation_enabled')::boolean,false),email_enabled=coalesce((p_payload->>'email_enabled')::boolean,false) where singleton;
    return '{}'::jsonb;
  elsif p_action='claim' then
    if not exists(select 1 from public.rivexis_defi_monitor_runtime where singleton and evaluation_enabled and last_cycle_at>now()-interval '15 minutes') then return 'null'::jsonb; end if;
    select * into r from public.rivexis_defi_monitor_rules where enabled and next_evaluation_at<=now() and (lease_until is null or lease_until<=now()) order by next_evaluation_at,id for update skip locked limit 1;
    if r.id is null then return 'null'::jsonb; end if;
    t:=gen_random_uuid();
    update public.rivexis_defi_monitor_rules set lease_token=t,lease_until=now()+interval '90 seconds',last_attempt_at=now() where id=r.id returning * into r;
    return to_jsonb(r);
  elsif p_action in ('complete','unavailable','reorg') then
    select * into r from public.rivexis_defi_monitor_rules where id=(p_payload->>'id')::uuid and lease_token=(p_payload->>'lease_token')::uuid and version=(p_payload->>'version')::bigint and lease_until>now() and enabled for update;
    if r.id is null then return jsonb_build_object('committed',false); end if;
    if p_action='unavailable' then
      update public.rivexis_defi_monitor_rules set last_status='UNAVAILABLE',failures=least(failures+1,4),next_evaluation_at=now()+interval '30 minutes'*power(2,least(failures,3)),lease_token=null,lease_until=null where id=r.id;
      return jsonb_build_object('committed',true);
    elsif p_action='reorg' then
      update public.rivexis_defi_monitor_events set state='INVALIDATED',updated_at=now() where rule_id=r.id and block_hash=r.block_hash;
      update public.rivexis_defi_monitor_rules set condition='UNKNOWN',last_status='INVALIDATED',last_success_at=null,lease_token=null,lease_until=null,next_evaluation_at=now()+interval '30 minutes' where id=r.id;
      return jsonb_build_object('committed',true);
    end if;
    result:=p_payload->'result'; next_condition:=result->>'condition';
    if next_condition is null or next_condition not in ('BREACH','CLEAR') or result->>'block_hash' is null or result->>'block_number' is null or result->>'coverage' is null or result->>'block_timestamp' is null
      or (result->>'health_raw' is not null and (result->>'health_raw')!~'^[0-9]{1,78}$')
      or (result->>'block_hash')!~'^0x[0-9a-f]{64}$' or (result->>'block_number')!~'^[0-9]{1,20}$' or result->>'coverage'<>r.coverage
      or (result->>'block_timestamp')::bigint<extract(epoch from now())-180 or (result->>'block_timestamp')::bigint>extract(epoch from now())+30 then raise exception 'Invalid evaluation evidence'; end if;
    if r.block_number is not null and (result->>'block_number')::numeric<r.block_number::numeric then raise exception 'Older evidence rejected'; end if;
    expected_condition:=case when result->>'health_raw' is null then 'CLEAR'
      when (result->>'health_raw')::numeric<=r.threshold_raw::numeric then 'BREACH'
      when (result->>'health_raw')::numeric>=r.recovery_raw::numeric then 'CLEAR'
      when r.condition='BREACH' then 'BREACH' else 'CLEAR' end;
    if next_condition<>expected_condition then raise exception 'Inconsistent threshold evaluation';end if;
    new_episode:=r.episode; event_kind:=null;
    if next_condition='BREACH' and r.condition<>'BREACH' then new_episode:=new_episode+1;event_kind:='BREACH';
    elsif next_condition='CLEAR' and r.condition='BREACH' then event_kind:='RECOVERY'; end if;
    update public.rivexis_defi_monitor_rules set condition=next_condition,episode=new_episode,last_status='VERIFIED',last_success_at=now(),block_number=result->>'block_number',block_hash=result->>'block_hash',block_timestamp=(result->>'block_timestamp')::bigint,health_raw=result->>'health_raw',failures=0,lease_token=null,lease_until=null,next_evaluation_at=now()+interval '30 minutes' where id=r.id;
    update public.rivexis_defi_monitor_events set state='CANCELLED',updated_at=now() where rule_id=r.id and state='QUEUED'
      and (episode<>new_episode or (next_condition='BREACH' and kind='RECOVERY') or (next_condition='CLEAR' and kind='BREACH'));
    -- Recovery cancels an unsent breach for the same episode.
    if event_kind='RECOVERY' then update public.rivexis_defi_monitor_events set state='CANCELLED',updated_at=now() where rule_id=r.id and episode=new_episode and kind='BREACH' and state='QUEUED'; end if;
    if event_kind is not null and r.email_opt_in then
      insert into public.rivexis_defi_monitor_events(rule_id,owner_id,episode,kind,rule_version,block_number,block_hash)
      values(r.id,r.owner_id,new_episode,event_kind,r.version,result->>'block_number',result->>'block_hash') on conflict(rule_id,episode,kind) do nothing;
    end if;
    return jsonb_build_object('committed',true);
  elsif p_action='claim_delivery' then
    if not exists(select 1 from public.rivexis_defi_monitor_runtime where singleton and evaluation_enabled and email_enabled and last_cycle_at>now()-interval '15 minutes') then return 'null'::jsonb; end if;
    -- Crash after dispatch has an unknown outcome. Never reclaim it as queued.
    update public.rivexis_defi_monitor_events set state='UNKNOWN',error_code='WORKER_OUTCOME_UNKNOWN',updated_at=now() where state='SENDING' and delivery_started_at<now()-interval '2 minutes';
    update public.rivexis_defi_monitor_events set state='EXPIRED',updated_at=now() where state='QUEUED' and expires_at<=now();
    -- Serialize the daily email cap across concurrent cron invocations.
    perform 1 from public.rivexis_defi_monitor_runtime where singleton for update;
    select count(*) into cap from public.rivexis_defi_monitor_events where delivery_started_at>=date_trunc('day',now() at time zone 'UTC') at time zone 'UTC';
    if cap>=10 then return 'null'::jsonb; end if;
    select ev.* into e from public.rivexis_defi_monitor_events ev join public.rivexis_defi_monitor_rules ru on ru.id=ev.rule_id
      where ev.state='QUEUED' and ev.next_attempt_at<=now() and ev.expires_at>now() and ru.enabled and ru.email_opt_in and ru.version=ev.rule_version and ru.last_status='VERIFIED' and ru.last_success_at>now()-interval '35 minutes'
      and ev.episode=ru.episode and ((ev.kind='BREACH' and ru.condition='BREACH') or (ev.kind='RECOVERY' and ru.condition='CLEAR'))
      and not exists(select 1 from public.rivexis_defi_monitor_events prior where prior.rule_id=ev.rule_id and prior.kind=ev.kind and prior.id<>ev.id and prior.delivery_started_at>now()-interval '1 hour' and prior.state in ('SENDING','ACCEPTED','DELIVERED','UNKNOWN'))
      order by ev.created_at,ev.id for update of ev,ru skip locked limit 1;
    if e.id is null then return 'null'::jsonb; end if;
    select email into recipient from auth.users where id=e.owner_id and email_confirmed_at is not null;
    if recipient is null then update public.rivexis_defi_monitor_events set state='CANCELLED' where id=e.id;return 'null'::jsonb;end if;
    t:=gen_random_uuid();update public.rivexis_defi_monitor_events set state='SENDING',delivery_token=t,delivery_started_at=now(),attempts=attempts+1,updated_at=now() where id=e.id returning * into e;
    return to_jsonb(e)||jsonb_build_object('recipient',recipient);
  elsif p_action='mark_delivery' then
    select * into e from public.rivexis_defi_monitor_events where id=(p_payload->>'id')::uuid and delivery_token=(p_payload->>'delivery_token')::uuid and state='SENDING' for update;
    if e.id is null then return jsonb_build_object('committed',false); end if;
    if p_payload->>'state' not in ('ACCEPTED','FAILED','UNKNOWN','RETRY') then raise exception 'Invalid delivery state'; end if;
    update public.rivexis_defi_monitor_events set state=case when p_payload->>'state'='RETRY' then case when attempts<3 and expires_at>now()+interval '5 minutes' then 'QUEUED' else 'FAILED' end else p_payload->>'state' end,
      message_id=case when p_payload->>'state'='ACCEPTED' then left(p_payload->>'message_id',300) else null end,
      error_code=case p_payload->>'error_code' when 'RATE_LIMITED' then 'RATE_LIMITED' when 'PROVIDER_REJECTED' then 'PROVIDER_REJECTED' when 'ACCEPTANCE_UNCONFIRMED' then 'ACCEPTANCE_UNCONFIRMED' else null end,
      next_attempt_at=now()+interval '5 minutes',updated_at=now() where id=e.id;
    return jsonb_build_object('committed',true);
  elsif p_action='receipt' then
    -- Trusted provider-event ingestion only; no public webhook is enabled by
    -- this migration. API acceptance alone cannot set DELIVERED or BOUNCED.
    if p_payload->>'state' not in ('DELIVERED','BOUNCED') then raise exception 'Invalid receipt';end if;
    update public.rivexis_defi_monitor_events set state=p_payload->>'state',updated_at=now() where id=(p_payload->>'id')::uuid and message_id=p_payload->>'message_id' and state='ACCEPTED';
    return '{}'::jsonb;
  end if;
  raise exception 'Unsupported job action';
end $$;
revoke all on function public.rivexis_defi_monitor_manage(uuid,text,jsonb),public.rivexis_defi_monitor_job(text,jsonb) from public,anon,authenticated;
grant execute on function public.rivexis_defi_monitor_manage(uuid,text,jsonb),public.rivexis_defi_monitor_job(text,jsonb) to service_role;
commit;
