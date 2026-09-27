grant rivexis_migrator to postgres with set true, inherit false;
drop function if exists public.rivexis_edge_bridge(text,text,jsonb);
set local role rivexis_migrator;

drop policy if exists rivexis_organization_bootstrap_insert on public.organizations;
create policy rivexis_organization_bootstrap_insert on public.organizations
for insert
with check (
  id = nullif(current_setting('rivexis.organization_id', true), '')
  and nullif(current_setting('rivexis.organization_role', true), '') = 'OWNER'
  and exists(
    select 1 from public.users
    where id = nullif(current_setting('rivexis.user_id', true), '')
  )
);

create function public.rivexis_edge_bridge(
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
  target_id text;
  v_workspace_id text;
  v_now timestamptz := clock_timestamp();
begin
  if p_actor_user_id is null or length(p_actor_user_id) <> 36 then
    raise exception 'invalid actor';
  end if;
  perform set_config('rivexis.user_id', p_actor_user_id, true);

  if p_action = 'ensure_user' then
    insert into public.users(id,email,password_hash,role,created_at,token_version,updated_at)
    values (
      p_actor_user_id,
      lower(trim(p_payload->>'email')),
      'supabase-auth-managed:' || p_actor_user_id,
      case when p_payload->>'role' in ('Individual','Fund','Treasury','Analyst') then p_payload->>'role' else 'Individual' end,
      v_now,0,v_now
    )
    on conflict (id) do update set email=excluded.email, updated_at=excluded.updated_at
    returning jsonb_build_object('id',users.id,'email',users.email,'role',users.role,'created_at',users.created_at) into result;
    return result;
  end if;

  if not exists(select 1 from public.users where id=p_actor_user_id) then
    raise exception 'actor is not provisioned';
  end if;

  if p_action = 'list_workspaces' then
    select coalesce(jsonb_agg(to_jsonb(w) order by w.created_at desc),'[]'::jsonb) into result
    from (
      select id,name,role,organization_id,created_at,'OWNER'::text as access_role
      from public.workspaces
      where owner_user_id=p_actor_user_id and organization_id is null
      union all
      select ws.id,ws.name,ws.role,ws.organization_id,ws.created_at,om.role as access_role
      from public.workspaces ws
      join public.organization_members om on om.organization_id=ws.organization_id
      where om.user_id=p_actor_user_id
    ) w;
    return jsonb_build_object('items',result);
  end if;

  if p_action = 'create_workspace' then
    if length(trim(coalesce(p_payload->>'name',''))) < 2 then raise exception 'workspace name is required'; end if;
    if coalesce(p_payload->>'role','') not in ('Individual','Fund','Treasury','Analyst') then raise exception 'invalid role'; end if;
    target_id := gen_random_uuid()::text;
    insert into public.workspaces(id,owner_user_id,name,role,created_at,organization_id,role_context,settings,updated_at)
    values(target_id,p_actor_user_id,trim(p_payload->>'name'),p_payload->>'role',v_now,null,p_payload->>'role','{}'::jsonb,v_now);
    return jsonb_build_object('id',target_id,'name',trim(p_payload->>'name'),'role',p_payload->>'role','organization_id',null,'access_role','OWNER','created_at',v_now);
  end if;

  if p_action = 'update_role' then
    if coalesce(p_payload->>'role','') not in ('Individual','Fund','Treasury','Analyst') then raise exception 'invalid role'; end if;
    update public.users set role=p_payload->>'role',updated_at=v_now where id=p_actor_user_id
    returning jsonb_build_object('id',users.id,'email',users.email,'role',users.role) into result;
    return result;
  end if;

  if p_action = 'list_organizations' then
    select coalesce(jsonb_agg(jsonb_build_object('id',o.id,'name',o.name,'created_at',o.created_at,'member_role',m.role) order by o.created_at desc),'[]'::jsonb)
    into result
    from public.organizations o join public.organization_members m on m.organization_id=o.id
    where m.user_id=p_actor_user_id;
    return jsonb_build_object('items',result);
  end if;

  if p_action = 'create_organization' then
    if length(trim(coalesce(p_payload->>'name',''))) < 2 then raise exception 'organization name is required'; end if;
    target_id := gen_random_uuid()::text;
    perform set_config('rivexis.organization_id', target_id, true);
    perform set_config('rivexis.organization_role', 'OWNER', true);
    insert into public.organizations(id,name,created_at,updated_at) values(target_id,trim(p_payload->>'name'),v_now,v_now);
    insert into public.organization_members(organization_id,user_id,role,created_at) values(target_id,p_actor_user_id,'OWNER',v_now);
    return jsonb_build_object('id',target_id,'name',trim(p_payload->>'name'),'created_at',v_now,'member_role','OWNER');
  end if;

  v_workspace_id := nullif(p_payload->>'workspace_id','');

  if p_action in ('history','saved_analyses','create_analysis','list_monitors','create_monitor') then
    if not exists(select 1 from public.workspaces where id=v_workspace_id) then raise exception 'workspace not found'; end if;
  end if;

  if p_action = 'history' then
    select coalesce(jsonb_agg(to_jsonb(h) order by h.created_at desc),'[]'::jsonb) into result
    from (
      select 'analysis'::text as type,id,workspace_id,engine_id,demo,created_at
      from public.analyses where analyses.workspace_id=v_workspace_id
      order by created_at desc limit least(greatest(coalesce((p_payload->>'limit')::int,50),1),200)
    ) h;
    return jsonb_build_object('items',result);
  end if;

  if p_action = 'analysis_detail' then
    select a.payload::jsonb into result
    from public.analyses a join public.workspaces w on w.id=a.workspace_id
    where a.id=p_payload->>'analysis_id'
      and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id)
      );
    if result is null then raise exception 'analysis not found'; end if;
    return result;
  end if;

  if p_action = 'saved_analyses' then
    select coalesce(jsonb_agg(jsonb_build_object('id',s.id,'workspace_id',s.workspace_id,'analysis_id',s.analysis_id,'title',s.title,'archived',s.archived,'created_at',s.created_at) order by s.created_at desc),'[]'::jsonb)
    into result from public.saved_analyses s
    where s.user_id=p_actor_user_id and s.workspace_id=v_workspace_id and s.archived=false;
    return jsonb_build_object('items',result);
  end if;

  if p_action = 'create_analysis' then
    if coalesce(p_payload->>'engine_id','') not in ('B1','B2','B3','B4','B5','F1','F2','F3','F4','F5') then raise exception 'invalid engine'; end if;
    target_id := p_payload->>'analysis_id';
    insert into public.analyses(id,engine_id,payload,demo,created_at,owner_user_id,workspace_id,status,updated_at)
    values(target_id,p_payload->>'engine_id',(p_payload->'result')::text,coalesce((p_payload->>'demo')::boolean,false),v_now,p_actor_user_id,v_workspace_id,p_payload->>'status',v_now);
    return p_payload->'result';
  end if;

  if p_action = 'list_monitors' then
    select coalesce(jsonb_agg(jsonb_build_object(
      'id',m.id,'workspace_id',m.workspace_id,'entity',m.entity,'chain',m.chain,'rules',m.rules::jsonb,'config',m.config::jsonb,
      'status',m.status,'last_analysis_id',m.last_analysis_id,'last_status',m.last_status,'created_at',m.created_at,'updated_at',m.updated_at
    ) order by m.created_at desc),'[]'::jsonb) into result
    from public.monitors m where m.workspace_id=v_workspace_id;
    return jsonb_build_object('items',result);
  end if;

  if p_action = 'create_monitor' then
    target_id := gen_random_uuid()::text;
    insert into public.monitors(id,workspace_id,created_by_user_id,entity,chain,rules,config,status,created_at,updated_at,enabled)
    values(target_id,v_workspace_id,p_actor_user_id,p_payload->>'entity',coalesce(p_payload->>'chain','ethereum'),coalesce(p_payload->'rules','[]'::jsonb)::text,coalesce(p_payload->'config','{}'::jsonb)::text,'active',v_now,v_now,true);
    return jsonb_build_object('id',target_id,'workspace_id',v_workspace_id,'entity',p_payload->>'entity','chain',coalesce(p_payload->>'chain','ethereum'),'rules',coalesce(p_payload->'rules','[]'::jsonb),'config',coalesce(p_payload->'config','{}'::jsonb),'status','active','last_analysis_id',null,'last_status',null,'created_at',v_now,'updated_at',v_now);
  end if;

  if p_action = 'get_monitor' then
    select jsonb_build_object('id',m.id,'workspace_id',m.workspace_id,'entity',m.entity,'chain',m.chain) into result
    from public.monitors m join public.workspaces w on w.id=m.workspace_id
    where m.id=p_payload->>'monitor_id'
      and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id)
      );
    if result is null then raise exception 'monitor not found'; end if;
    return result;
  end if;

  if p_action = 'update_monitor_result' then
    update public.monitors m set last_analysis_id=p_payload->>'analysis_id',last_status=p_payload->>'status',updated_at=v_now
    where m.id=p_payload->>'monitor_id'
      and exists(
        select 1 from public.workspaces w where w.id=m.workspace_id and (
          (w.organization_id is null and w.owner_user_id=p_actor_user_id)
          or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id and om.role in ('OWNER','ADMIN','ANALYST'))
        )
      )
    returning jsonb_build_object('id',m.id) into result;
    if result is null then raise exception 'monitor not found'; end if;
    return result;
  end if;

  if p_action = 'create_protocol_review' then
    v_workspace_id := nullif(p_payload->>'workspace_id','');
    if not exists(
      select 1 from public.workspaces w where w.id=v_workspace_id and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id and om.role in ('OWNER','ADMIN','ANALYST'))
      )
    ) then raise exception 'workspace write access required'; end if;
    target_id := gen_random_uuid()::text;
    insert into public.reports(id,workspace_id,decision_id,analysis_id,format,status,created_by_user_id,created_at,report_type,payload)
    values(target_id,v_workspace_id,null,null,'json','draft',p_actor_user_id,v_now,'protocol_configuration_review',coalesce(p_payload->'payload','{}'::jsonb));
    return jsonb_build_object('id',target_id,'workspace_id',v_workspace_id,'report_type','protocol_configuration_review','format','json','status','draft','payload',coalesce(p_payload->'payload','{}'::jsonb),'approved_by_user_id',null,'approved_at',null,'created_by_user_id',p_actor_user_id,'created_at',v_now);
  end if;

  if p_action in ('get_protocol_review','approve_protocol_review') then
    select jsonb_build_object(
      'id',r.id,'workspace_id',r.workspace_id,'report_type',r.report_type,'format',r.format,'status',r.status,'payload',r.payload,
      'approved_by_user_id',r.approved_by_user_id,'approved_at',r.approved_at,'created_by_user_id',r.created_by_user_id,'created_at',r.created_at
    ) into result
    from public.reports r join public.workspaces w on w.id=r.workspace_id
    where r.id=p_payload->>'report_id' and r.report_type='protocol_configuration_review'
      and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id)
      );
    if result is null then raise exception 'protocol review not found'; end if;
    if p_action = 'get_protocol_review' then return result; end if;
    if not exists(
      select 1 from public.reports r join public.workspaces w on w.id=r.workspace_id
      where r.id=p_payload->>'report_id' and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id and om.role in ('OWNER','ADMIN'))
      )
    ) then raise exception 'workspace manager access required'; end if;
    update public.reports r set status='approved',approved_by_user_id=p_actor_user_id,approved_at=v_now where r.id=p_payload->>'report_id'
    returning jsonb_build_object('id',r.id,'workspace_id',r.workspace_id,'report_type',r.report_type,'format',r.format,'status',r.status,'payload',r.payload,'approved_by_user_id',r.approved_by_user_id,'approved_at',r.approved_at,'created_by_user_id',r.created_by_user_id,'created_at',r.created_at) into result;
    return result;
  end if;

  if p_action = 'list_protocol_investigations' then
    v_workspace_id := nullif(p_payload->>'workspace_id','');
    if not exists(
      select 1 from public.workspaces w where w.id=v_workspace_id and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id)
      )
    ) then raise exception 'workspace access required'; end if;
    select coalesce(jsonb_agg(jsonb_build_object(
      'id',r.id,'workspace_id',r.workspace_id,'report_type',r.report_type,'format',r.format,'status',r.status,'payload',r.payload,
      'created_by_user_id',r.created_by_user_id,'created_at',r.created_at
    ) order by r.created_at desc),'[]'::jsonb) into result
    from public.reports r where r.workspace_id=v_workspace_id and r.report_type='protocol_investigation_case';
    return jsonb_build_object('workspace_id',v_workspace_id,'items',result);
  end if;

  if p_action = 'create_protocol_investigation' then
    v_workspace_id := nullif(p_payload->>'workspace_id','');
    if length(trim(coalesce(p_payload->>'title',''))) < 2 then raise exception 'investigation title is required'; end if;
    if not exists(
      select 1 from public.workspaces w where w.id=v_workspace_id and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id and om.role in ('OWNER','ADMIN','ANALYST'))
      )
    ) then raise exception 'workspace write access required'; end if;
    target_id := gen_random_uuid()::text;
    result := jsonb_build_object(
      'title',trim(p_payload->>'title'),'input',coalesce(p_payload->'input','{}'::jsonb),'timeline',coalesce(p_payload->'timeline','{}'::jsonb),
      'review_ids','[]'::jsonb,'disposition',null,'notes',coalesce(p_payload->>'notes',''),
      'status_history',jsonb_build_array(jsonb_build_object('status','open','at',v_now,'actor_user_id',p_actor_user_id))
    );
    insert into public.reports(id,workspace_id,decision_id,analysis_id,format,status,created_by_user_id,created_at,report_type,payload)
    values(target_id,v_workspace_id,null,null,'json','open',p_actor_user_id,v_now,'protocol_investigation_case',result);
    return jsonb_build_object('id',target_id,'workspace_id',v_workspace_id,'report_type','protocol_investigation_case','format','json','status','open','payload',result,'created_by_user_id',p_actor_user_id,'created_at',v_now);
  end if;

  if p_action in ('get_protocol_investigation','update_protocol_investigation','attach_protocol_review') then
    target_id := p_payload->>'case_id';
    select jsonb_build_object(
      'id',r.id,'workspace_id',r.workspace_id,'report_type',r.report_type,'format',r.format,'status',r.status,'payload',r.payload,
      'created_by_user_id',r.created_by_user_id,'created_at',r.created_at
    ) into result
    from public.reports r join public.workspaces w on w.id=r.workspace_id
    where r.id=target_id and r.report_type='protocol_investigation_case'
      and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id)
      );
    if result is null then raise exception 'protocol investigation not found'; end if;
    if p_action = 'get_protocol_investigation' then return result; end if;
    if not exists(
      select 1 from public.reports r join public.workspaces w on w.id=r.workspace_id
      where r.id=target_id and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(select 1 from public.organization_members om where om.organization_id=w.organization_id and om.user_id=p_actor_user_id and om.role in ('OWNER','ADMIN','ANALYST'))
      )
    ) then raise exception 'workspace write access required'; end if;
    if p_action = 'attach_protocol_review' then
      if not exists(select 1 from public.reports r, public.reports c where r.id=p_payload->>'review_id' and r.report_type='protocol_configuration_review' and c.id=target_id and r.workspace_id=c.workspace_id) then raise exception 'compatible review not found'; end if;
      update public.reports r set payload=jsonb_set(coalesce(r.payload,'{}'::jsonb),'{review_ids}',
        case when coalesce(r.payload->'review_ids','[]'::jsonb) ? (p_payload->>'review_id') then coalesce(r.payload->'review_ids','[]'::jsonb)
             else coalesce(r.payload->'review_ids','[]'::jsonb) || jsonb_build_array(p_payload->>'review_id') end,true)
      where r.id=target_id;
    else
      if coalesce(p_payload->>'status','') not in ('','open','in_review','closed') then raise exception 'invalid investigation status'; end if;
      if p_payload->>'status'='closed' and length(trim(coalesce(p_payload->>'disposition',result->'payload'->>'disposition',''))) = 0 then raise exception 'a disposition is required before closing'; end if;
      update public.reports r set
        status=coalesce(nullif(p_payload->>'status',''),r.status),
        payload=jsonb_set(
          jsonb_set(coalesce(r.payload,'{}'::jsonb),'{notes}',to_jsonb(coalesce(p_payload->>'notes',r.payload->>'notes','')),true),
          '{disposition}',case when p_payload ? 'disposition' then
            case when length(trim(coalesce(p_payload->>'disposition',''))) = 0 then 'null'::jsonb else to_jsonb(trim(p_payload->>'disposition')) end
            else coalesce(r.payload->'disposition','null'::jsonb) end,true
        )
      where r.id=target_id;
    end if;
    select jsonb_build_object('id',r.id,'workspace_id',r.workspace_id,'report_type',r.report_type,'format',r.format,'status',r.status,'payload',r.payload,'created_by_user_id',r.created_by_user_id,'created_at',r.created_at)
    into result from public.reports r where r.id=target_id;
    return result;
  end if;

  raise exception 'unsupported edge bridge action';
end;
$$;

revoke all on function public.rivexis_edge_bridge(text,text,jsonb) from public, anon, authenticated;
grant execute on function public.rivexis_edge_bridge(text,text,jsonb) to service_role;

comment on function public.rivexis_edge_bridge(text,text,jsonb) is
  'Narrow service-role bridge for the Rivexis Supabase Edge runtime. User identity is verified by Supabase Auth before invocation; all tenant reads remain constrained by the existing RLS session context.';

reset role;
revoke set option for rivexis_migrator from postgres;
