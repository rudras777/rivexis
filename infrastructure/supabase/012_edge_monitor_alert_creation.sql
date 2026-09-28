grant rivexis_migrator to postgres with set true, inherit false;
set local role rivexis_migrator;

drop trigger if exists trg_rivexis_edge_monitor_alert on public.monitors;
drop function if exists public.rivexis_edge_monitor_alert_from_analysis();

create function public.rivexis_edge_monitor_alert_from_analysis()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_analysis public.analyses%rowtype;
  v_payload jsonb;
  v_runtime text;
  v_status text;
  v_severity text;
  v_signals_count integer := 0;
  v_blockers_count integer := 0;
  v_event_key text;
  v_alert_payload jsonb;
  v_now timestamptz := clock_timestamp();
begin
  if new.last_analysis_id is null or new.last_analysis_id is not distinct from old.last_analysis_id then
    return new;
  end if;

  select a.* into v_analysis
  from public.analyses a
  where a.id = new.last_analysis_id
    and a.workspace_id = new.workspace_id
    and a.engine_id = 'B3';

  if not found then
    return new;
  end if;

  begin
    v_payload := v_analysis.payload::jsonb;
  exception when others then
    return new;
  end;

  v_runtime := coalesce(v_payload #>> '{metrics,runtime}','');
  if v_runtime not like 'supabase-edge%' then
    return new;
  end if;

  v_status := upper(coalesce(v_payload->>'status','UNKNOWN'));
  v_severity := lower(coalesce(v_payload->>'severity','unknown'));

  -- Missing provider evidence is a data-availability state, never a threat event.
  if v_status = 'UNKNOWN'
     or (jsonb_typeof(v_payload->'hard_blockers')='array' and (v_payload->'hard_blockers') ? 'NO_VERIFIED_PROVIDER_EVIDENCE') then
    return new;
  end if;

  if jsonb_typeof(v_payload->'signals')='array' then
    v_signals_count := jsonb_array_length(v_payload->'signals');
  end if;
  if jsonb_typeof(v_payload->'hard_blockers')='array' then
    v_blockers_count := jsonb_array_length(v_payload->'hard_blockers');
  end if;

  -- Match the provider-capable FastAPI monitor materiality contract, while
  -- explicitly excluding UNKNOWN/missing-evidence states above.
  if v_signals_count = 0
     and v_blockers_count = 0
     and v_severity not in ('moderate','high','critical') then
    return new;
  end if;

  v_event_key := 'monitor-result:' || new.id || ':' || md5(
    jsonb_build_object(
      'severity',v_severity,
      'status',v_status,
      'risk_score',v_payload->'risk_score',
      'signals',coalesce(v_payload->'signals','[]'::jsonb),
      'hard_blockers',coalesce(v_payload->'hard_blockers','[]'::jsonb),
      'warnings',coalesce(v_payload->'warnings','[]'::jsonb)
    )::text
  );

  v_alert_payload := jsonb_build_object(
    'source','monitor_result',
    'analysis_id',v_analysis.id,
    'analysis_status',v_status,
    'analysis_demo',coalesce(v_analysis.demo,false),
    'evidence_mode',case when coalesce(v_analysis.demo,false) then 'SYNTHETIC_DEMO' else 'VERIFIED_COMPATIBILITY_RESULT' end,
    'risk_score',v_payload->'risk_score',
    'signals',coalesce(v_payload->'signals','[]'::jsonb),
    'hard_blockers',coalesce(v_payload->'hard_blockers','[]'::jsonb),
    'warnings',coalesce(v_payload->'warnings','[]'::jsonb),
    'provider_consensus',v_payload->'provider_consensus',
    'data_freshness',v_payload->'data_freshness'
  );

  insert into public.alerts(
    id,workspace_id,monitor_id,analysis_id,severity,status,payload,created_at,updated_at,
    title,detail,provider_id,external_event_key,occurrence_count,first_seen_at,last_seen_at,
    delivery_status,delivery_attempts
  ) values (
    gen_random_uuid()::text,new.workspace_id,new.id,v_analysis.id,v_severity,'open',v_alert_payload::text,v_now,v_now,
    case when coalesce(v_analysis.demo,false) then 'Synthetic B3 monitor result' else 'B3 monitor material result' end,
    case when coalesce(v_analysis.demo,false)
      then 'Synthetic demonstration evidence. Not a live threat claim.'
      else 'Material result derived from a persisted normalized compatibility analysis.' end,
    'rivexis-monitor',v_event_key,1,v_now,v_now,'pending',0
  )
  on conflict (workspace_id,provider_id,external_event_key)
  do update set
    occurrence_count = public.alerts.occurrence_count + 1,
    last_seen_at = excluded.last_seen_at,
    updated_at = excluded.updated_at,
    analysis_id = excluded.analysis_id,
    severity = excluded.severity,
    payload = excluded.payload,
    title = excluded.title,
    detail = excluded.detail;

  return new;
end;
$$;

revoke all on function public.rivexis_edge_monitor_alert_from_analysis() from public;
revoke all on function public.rivexis_edge_monitor_alert_from_analysis() from anon;
revoke all on function public.rivexis_edge_monitor_alert_from_analysis() from authenticated;
revoke all on function public.rivexis_edge_monitor_alert_from_analysis() from service_role;

create trigger trg_rivexis_edge_monitor_alert
after update of last_analysis_id on public.monitors
for each row
when (new.last_analysis_id is distinct from old.last_analysis_id and new.last_analysis_id is not null)
execute function public.rivexis_edge_monitor_alert_from_analysis();

reset role;
