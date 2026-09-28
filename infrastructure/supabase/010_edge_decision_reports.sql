grant rivexis_migrator to postgres with set true, inherit false;
set local role rivexis_migrator;

create or replace function public.rivexis_edge_decision_report(
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
  v_decision_id text;
  v_report_id text;
  v_format text;
  v_now timestamptz := clock_timestamp();
  v_count integer;
  v_workspace_count integer;
  v_ids jsonb;
begin
  if p_actor_user_id is null or length(p_actor_user_id) <> 36 then
    raise exception 'invalid actor';
  end if;
  if not exists(select 1 from public.users where id=p_actor_user_id) then
    raise exception 'actor is not provisioned';
  end if;
  perform set_config('rivexis.user_id', p_actor_user_id, true);

  if p_action = 'decision_inputs' then
    v_ids := coalesce(p_payload->'analysis_ids','[]'::jsonb);
    if jsonb_typeof(v_ids) <> 'array' or jsonb_array_length(v_ids) < 1 or jsonb_array_length(v_ids) > 10 then
      raise exception 'at least one and at most ten persisted engine results are required';
    end if;

    with requested as (
      select value as analysis_id, ordinality as ord
      from jsonb_array_elements_text(v_ids) with ordinality
    ), authorized as (
      select requested.ord,a.workspace_id,a.payload::jsonb as payload
      from requested
      join public.analyses a on a.id=requested.analysis_id
      join public.workspaces w on w.id=a.workspace_id
      where (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(
          select 1 from public.organization_members om
          where om.organization_id=w.organization_id and om.user_id=p_actor_user_id and om.role in ('OWNER','ADMIN','ANALYST')
        )
      )
    )
    select count(*),count(distinct workspace_id) into v_count,v_workspace_count from authorized;

    if v_count <> jsonb_array_length(v_ids) then
      raise exception 'one or more analysis results are unavailable';
    end if;
    if v_workspace_count <> 1 then
      raise exception 'a decision cannot combine analyses from different workspaces';
    end if;

    with requested as (
      select value as analysis_id, ordinality as ord
      from jsonb_array_elements_text(v_ids) with ordinality
    ), authorized as (
      select requested.ord,a.workspace_id,a.payload::jsonb as payload
      from requested
      join public.analyses a on a.id=requested.analysis_id
      join public.workspaces w on w.id=a.workspace_id
      where (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(
          select 1 from public.organization_members om
          where om.organization_id=w.organization_id and om.user_id=p_actor_user_id and om.role in ('OWNER','ADMIN','ANALYST')
        )
      )
    )
    select min(workspace_id),jsonb_agg(payload order by ord) into v_workspace_id,result from authorized;
    return jsonb_build_object('workspace_id',v_workspace_id,'items',result);
  end if;

  if p_action = 'save_decision' then
    v_workspace_id := nullif(p_payload->>'workspace_id','');
    result := p_payload->'decision';
    v_decision_id := nullif(result->>'decision_id','');
    if v_workspace_id is null or v_decision_id is null or length(v_decision_id) <> 36 then
      raise exception 'invalid decision payload';
    end if;
    if not exists(
      select 1 from public.workspaces w where w.id=v_workspace_id and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id and om.role in ('OWNER','ADMIN','ANALYST'))
      )
    ) then raise exception 'workspace write access required'; end if;

    insert into public.decisions(
      id,payload,created_at,owner_user_id,workspace_id,analysis_id,data_confidence,decision,decision_confidence,policy_version,recommended_action,risk_score,safer_option
    ) values(
      v_decision_id,result::text,v_now,p_actor_user_id,v_workspace_id,
      nullif(result->'analysis_ids'->>0,''),
      nullif(result->>'data_confidence','')::numeric,
      result->>'decision',nullif(result->>'decision_confidence','')::numeric,
      result->>'decision_methodology_version',result->>'recommended_action',nullif(result->>'overall_risk_score','')::numeric,result->>'safer_option'
    );
    return result;
  end if;

  if p_action = 'get_decision' then
    v_decision_id := nullif(p_payload->>'decision_id','');
    select d.payload::jsonb into result
    from public.decisions d join public.workspaces w on w.id=d.workspace_id
    where d.id=v_decision_id and (
      (w.organization_id is null and w.owner_user_id=p_actor_user_id)
      or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id)
    );
    if result is null then raise exception 'decision not found'; end if;
    return result;
  end if;

  if p_action = 'history' then
    v_workspace_id := nullif(p_payload->>'workspace_id','');
    if not exists(
      select 1 from public.workspaces w where w.id=v_workspace_id and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id)
      )
    ) then raise exception 'workspace not found'; end if;

    select coalesce(jsonb_agg(to_jsonb(h) order by h.created_at desc),'[]'::jsonb) into result
    from (
      select 'analysis'::text as type,a.id,a.workspace_id,a.engine_id,a.demo,a.created_at
      from public.analyses a where a.workspace_id=v_workspace_id
      union all
      select 'decision'::text as type,d.id,d.workspace_id,null::varchar as engine_id,null::boolean as demo,d.created_at
      from public.decisions d where d.workspace_id=v_workspace_id
      order by created_at desc
      limit least(greatest(coalesce((p_payload->>'limit')::int,50),1),200)
    ) h;
    return jsonb_build_object('items',result);
  end if;

  if p_action = 'create_report' then
    v_decision_id := nullif(p_payload->>'decision_id','');
    v_format := lower(coalesce(p_payload->>'format','html'));
    if v_format not in ('html','pdf','json') then raise exception 'MVP supports html, pdf and json'; end if;
    select d.workspace_id into v_workspace_id
    from public.decisions d join public.workspaces w on w.id=d.workspace_id
    where d.id=v_decision_id and (
      (w.organization_id is null and w.owner_user_id=p_actor_user_id)
      or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id)
    );
    if v_workspace_id is null then raise exception 'decision not found'; end if;
    v_report_id := gen_random_uuid()::text;
    insert into public.reports(id,workspace_id,decision_id,analysis_id,format,status,created_by_user_id,created_at,report_type,payload)
    values(v_report_id,v_workspace_id,v_decision_id,null,v_format,'generated',p_actor_user_id,v_now,'decision',null);
    return jsonb_build_object(
      'id',v_report_id,'workspace_id',v_workspace_id,'analysis_id',null,'decision_id',v_decision_id,'report_type','decision','format',v_format,
      'storage_ref',null,'status','generated','approved_by_user_id',null,'approved_at',null,'created_by_user_id',p_actor_user_id,'created_at',v_now
    );
  end if;

  if p_action = 'get_report' then
    v_report_id := nullif(p_payload->>'report_id','');
    select jsonb_build_object(
      'id',r.id,'workspace_id',r.workspace_id,'analysis_id',r.analysis_id,'decision_id',r.decision_id,'report_type',r.report_type,'format',r.format,
      'storage_ref',r.storage_ref,'status',r.status,'approved_by_user_id',r.approved_by_user_id,'approved_at',r.approved_at,
      'created_by_user_id',r.created_by_user_id,'created_at',r.created_at
    ) into result
    from public.reports r join public.workspaces w on w.id=r.workspace_id
    where r.id=v_report_id and (
      (w.organization_id is null and w.owner_user_id=p_actor_user_id)
      or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id)
    );
    if result is null then raise exception 'report not found'; end if;
    return result;
  end if;

  raise exception 'unsupported decision/report action';
end;
$$;

revoke all on function public.rivexis_edge_decision_report(text,text,jsonb) from public, anon, authenticated;
grant execute on function public.rivexis_edge_decision_report(text,text,jsonb) to service_role;
comment on function public.rivexis_edge_decision_report(text,text,jsonb) is
  'Service-role-only compatibility bridge for canonical persisted decision inputs, decision persistence/history, and decision report metadata. Authorization is re-evaluated against current workspace membership on every action.';

reset role;
revoke set option for rivexis_migrator from postgres granted by postgres;
