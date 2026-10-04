-- Organization workspaces do not use workspaces.owner_user_id. Resolve their
-- transactional alert recipient to the earliest OWNER membership instead.
-- The dispatcher receives only the organization membership columns needed for
-- this lookup and remains a NOLOGIN service role.

grant select(organization_id,user_id,role,created_at)
  on table public.organization_members
  to rivexis_alert_dispatcher;

grant rivexis_alert_dispatcher to postgres with set true, inherit false;
grant create on schema public to rivexis_alert_dispatcher;
set local role rivexis_alert_dispatcher;

create or replace function public.rivexis_edge_alert_dispatch(
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
    left join lateral (
      select om.user_id
      from public.organization_members om
      where om.organization_id=w.organization_id
        and om.role='OWNER'
      order by om.created_at,om.user_id
      limit 1
    ) org_owner on w.owner_user_id is null and w.organization_id is not null
    left join public.users u on u.id=coalesce(w.owner_user_id,org_owner.user_id);

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

reset role;
revoke create on schema public from rivexis_alert_dispatcher;
revoke rivexis_alert_dispatcher from postgres;
