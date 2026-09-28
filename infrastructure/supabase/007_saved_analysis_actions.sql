create or replace function public.rivexis_edge_saved_analysis(
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
  v_analysis_id text;
  v_title text;
  v_include_archived boolean := coalesce((p_payload->>'include_archived')::boolean, false);
  v_archived boolean := coalesce((p_payload->>'archived')::boolean, true);
  v_now timestamptz := clock_timestamp();
begin
  if p_actor_user_id is null or length(p_actor_user_id) <> 36 then
    raise exception 'invalid actor';
  end if;
  if not exists(select 1 from public.users where id=p_actor_user_id) then
    raise exception 'actor is not provisioned';
  end if;

  perform set_config('rivexis.user_id', p_actor_user_id, true);
  v_workspace_id := nullif(p_payload->>'workspace_id','');

  if p_action = 'list' then
    if v_workspace_id is null or not exists(
      select 1 from public.workspaces w
      where w.id=v_workspace_id and (
        (w.organization_id is null and w.owner_user_id=p_actor_user_id)
        or exists(
          select 1 from public.organization_members om
          where om.organization_id=w.organization_id and om.user_id=p_actor_user_id
        )
      )
    ) then raise exception 'workspace access required'; end if;

    select coalesce(jsonb_agg(jsonb_build_object(
      'id',s.id,
      'workspace_id',s.workspace_id,
      'analysis_id',s.analysis_id,
      'title',s.title,
      'archived',s.archived,
      'created_at',s.created_at
    ) order by s.created_at desc),'[]'::jsonb)
    into result
    from public.saved_analyses s
    where s.user_id=p_actor_user_id
      and s.workspace_id=v_workspace_id
      and (v_include_archived or s.archived=false);
    return jsonb_build_object('items',result);
  end if;

  if p_action = 'create' then
    v_analysis_id := nullif(p_payload->>'analysis_id','');
    v_title := trim(coalesce(p_payload->>'title',''));
    if v_analysis_id is null or length(v_title) < 1 then
      raise exception 'analysis id and title are required';
    end if;

    select a.workspace_id into v_workspace_id
    from public.analyses a
    join public.workspaces w on w.id=a.workspace_id
    where a.id=v_analysis_id and (
      (w.organization_id is null and w.owner_user_id=p_actor_user_id)
      or exists(
        select 1 from public.organization_members om
        where om.organization_id=w.organization_id and om.user_id=p_actor_user_id
      )
    );
    if v_workspace_id is null then return null; end if;

    target_id := gen_random_uuid()::text;
    insert into public.saved_analyses(id,user_id,analysis_id,title,archived,created_at,workspace_id)
    values(target_id,p_actor_user_id,v_analysis_id,v_title,false,v_now,v_workspace_id)
    on conflict (user_id,analysis_id) do update set
      title=excluded.title,
      archived=false,
      workspace_id=excluded.workspace_id
    returning jsonb_build_object(
      'id',saved_analyses.id,
      'workspace_id',saved_analyses.workspace_id,
      'analysis_id',saved_analyses.analysis_id,
      'title',saved_analyses.title,
      'archived',saved_analyses.archived,
      'created_at',saved_analyses.created_at
    ) into result;
    return result;
  end if;

  if p_action = 'archive' then
    target_id := nullif(p_payload->>'saved_id','');
    if target_id is null then return null; end if;
    update public.saved_analyses s set archived=v_archived
    where s.id=target_id
      and s.user_id=p_actor_user_id
      and exists(
        select 1 from public.workspaces w
        where w.id=s.workspace_id and (
          (w.organization_id is null and w.owner_user_id=p_actor_user_id)
          or exists(
            select 1 from public.organization_members om
            where om.organization_id=w.organization_id and om.user_id=p_actor_user_id
          )
        )
      )
    returning jsonb_build_object(
      'id',s.id,
      'workspace_id',s.workspace_id,
      'analysis_id',s.analysis_id,
      'title',s.title,
      'archived',s.archived,
      'created_at',s.created_at
    ) into result;
    return result;
  end if;

  if p_action = 'delete' then
    target_id := nullif(p_payload->>'saved_id','');
    if target_id is null then return jsonb_build_object('deleted',false); end if;
    delete from public.saved_analyses s
    where s.id=target_id
      and s.user_id=p_actor_user_id
      and exists(
        select 1 from public.workspaces w
        where w.id=s.workspace_id and (
          (w.organization_id is null and w.owner_user_id=p_actor_user_id)
          or exists(
            select 1 from public.organization_members om
            where om.organization_id=w.organization_id and om.user_id=p_actor_user_id
          )
        )
      )
    returning s.id into target_id;
    return jsonb_build_object('deleted',target_id is not null);
  end if;

  raise exception 'unsupported saved analysis action';
end;
$$;

alter function public.rivexis_edge_saved_analysis(text,text,jsonb) owner to rivexis_migrator;
revoke all on function public.rivexis_edge_saved_analysis(text,text,jsonb) from public, anon, authenticated;
grant execute on function public.rivexis_edge_saved_analysis(text,text,jsonb) to service_role;

comment on function public.rivexis_edge_saved_analysis(text,text,jsonb) is
  'Service-role bridge for user-owned saved analysis references. Supabase Auth verifies the actor before invocation and every read/write rechecks workspace membership.';
