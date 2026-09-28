grant rivexis_migrator to postgres with set true, inherit false;
drop function if exists public.rivexis_edge_alerts(text,text,jsonb);
set local role rivexis_migrator;

create function public.rivexis_edge_alerts(
  p_action text,
  p_actor_user_id text,
  p_payload jsonb default '{}'::jsonb
) returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  result jsonb;
  v_workspace_id text;
  v_alert_id text;
  v_status text;
  v_slo integer;
  v_now timestamptz := clock_timestamp();
  v_cutoff timestamptz;
begin
  if p_actor_user_id is null or length(p_actor_user_id) <> 36 then
    raise exception 'invalid actor';
  end if;
  if not exists(select 1 from public.users where id=p_actor_user_id) then
    raise exception 'actor is not provisioned';
  end if;
  perform set_config('rivexis.user_id',p_actor_user_id,true);
  v_workspace_id := nullif(p_payload->>'workspace_id','');

  if p_action in ('list','metrics') then
    if v_workspace_id is null or not exists(
      select 1 from public.workspaces w where w.id=v_workspace_id and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id)
      )
    ) then raise exception 'workspace not found'; end if;
  end if;

  if p_action='list' then
    select coalesce(jsonb_agg(jsonb_build_object(
      'id',a.id,'workspace_id',a.workspace_id,'monitor_id',a.monitor_id,'analysis_id',a.analysis_id,
      'severity',a.severity,'status',a.status,'provider_id',a.provider_id,'external_event_key',a.external_event_key,
      'occurrence_count',a.occurrence_count,'first_seen_at',a.first_seen_at,'last_seen_at',a.last_seen_at,
      'delivery_status',a.delivery_status,'delivery_attempts',a.delivery_attempts,'next_delivery_at',a.next_delivery_at,
      'last_delivery_error',a.last_delivery_error,'delivered_at',a.delivered_at,'dead_lettered_at',a.dead_lettered_at,
      'payload',case when a.payload is null or a.payload='' then '{}'::jsonb else a.payload::jsonb end,
      'created_at',a.created_at,'updated_at',a.updated_at
    ) order by a.created_at desc),'[]'::jsonb) into result
    from public.alerts a where a.workspace_id=v_workspace_id;
    return jsonb_build_object(
      'workspace_id',v_workspace_id,
      'items',result,
      'status','durable_alert_records_only; continuous_threat_stream_not_configured; automatic_delivery_processor_not_configured'
    );
  end if;

  if p_action='status' then
    v_alert_id:=nullif(p_payload->>'alert_id','');
    v_status:=lower(coalesce(p_payload->>'status',''));
    if v_status not in ('open','acknowledged','resolved') then raise exception 'invalid alert status'; end if;
    if not exists(
      select 1 from public.alerts a join public.workspaces w on w.id=a.workspace_id
      where a.id=v_alert_id and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id and om.role in ('OWNER','ADMIN','ANALYST'))
      )
    ) then raise exception 'alert not found or write access required'; end if;
    update public.alerts a set status=v_status,updated_at=v_now where a.id=v_alert_id
    returning jsonb_build_object(
      'id',a.id,'workspace_id',a.workspace_id,'monitor_id',a.monitor_id,'analysis_id',a.analysis_id,
      'severity',a.severity,'status',a.status,'delivery_status',a.delivery_status,'delivery_attempts',a.delivery_attempts,
      'next_delivery_at',a.next_delivery_at,'last_delivery_error',a.last_delivery_error,'dead_lettered_at',a.dead_lettered_at,
      'created_at',a.created_at,'updated_at',a.updated_at
    ) into result;
    return result;
  end if;

  if p_action='requeue' then
    v_alert_id:=nullif(p_payload->>'alert_id','');
    if not exists(
      select 1 from public.alerts a join public.workspaces w on w.id=a.workspace_id
      where a.id=v_alert_id and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id and om.role in ('OWNER','ADMIN'))
      )
    ) then raise exception 'alert not found or management access required'; end if;
    update public.alerts a set delivery_status='pending',delivery_attempts=0,next_delivery_at=null,last_delivery_error=null,dead_lettered_at=null,updated_at=v_now where a.id=v_alert_id
    returning jsonb_build_object(
      'id',a.id,'workspace_id',a.workspace_id,'status',a.status,'delivery_status',a.delivery_status,
      'delivery_attempts',a.delivery_attempts,'next_delivery_at',a.next_delivery_at,'last_delivery_error',a.last_delivery_error,
      'dead_lettered_at',a.dead_lettered_at,'updated_at',a.updated_at
    ) into result;
    return result;
  end if;

  if p_action='metrics' then
    v_slo:=least(greatest(coalesce((p_payload->>'slo_seconds')::integer,300),1),86400);
    v_cutoff:=v_now-interval '24 hours';
    select jsonb_build_object(
      'workspace_id',v_workspace_id,
      'window_hours',24,
      'slo_seconds',v_slo,
      'total',count(*),
      'pending',count(*) filter(where a.delivery_status in ('pending','retry')),
      'delivered',count(*) filter(where a.delivery_status='delivered'),
      'dead_letter',count(*) filter(where a.delivery_status='dead_letter'),
      'oldest_pending_age_seconds',coalesce(round(extract(epoch from (v_now-min(a.created_at) filter(where a.delivery_status in ('pending','retry'))))::numeric,3),0),
      'delivered_within_slo_percent',case
        when count(*) filter(where a.delivery_status='delivered' and a.delivered_at is not null)=0 then null
        else round(100.0*(count(*) filter(where a.delivery_status='delivered' and a.delivered_at is not null and extract(epoch from (a.delivered_at-a.created_at))<=v_slo))::numeric/(count(*) filter(where a.delivery_status='delivered' and a.delivered_at is not null)),2)
      end,
      'processor_status','NOT_CONFIGURED'
    ) into result
    from public.alerts a where a.workspace_id=v_workspace_id and a.created_at>=v_cutoff;
    return result;
  end if;

  raise exception 'unsupported alert action';
end;
$$;

revoke all on function public.rivexis_edge_alerts(text,text,jsonb) from public;
revoke all on function public.rivexis_edge_alerts(text,text,jsonb) from anon;
revoke all on function public.rivexis_edge_alerts(text,text,jsonb) from authenticated;
grant execute on function public.rivexis_edge_alerts(text,text,jsonb) to service_role;
reset role;
