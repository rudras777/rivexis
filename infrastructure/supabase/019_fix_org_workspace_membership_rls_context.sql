-- Fix the organization-workspace RPC so its membership lookup executes inside
-- the actor's FORCE-RLS context. Migration 018 intentionally used a
-- NOBYPASSRLS definer; the user context must therefore be established before
-- reading organization_members.

grant rivexis_migrator to postgres with set true, inherit false;
set local role rivexis_migrator;

create or replace function public.rivexis_edge_create_organization_workspace(
  p_actor_user_id text,
  p_payload jsonb default '{}'::jsonb
) returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_organization_id text := nullif(trim(coalesce(p_payload->>'organization_id','')), '');
  v_name text := trim(coalesce(p_payload->>'name',''));
  v_role text := coalesce(p_payload->>'role','');
  v_member_role text;
  v_workspace_id text;
  v_now timestamptz := clock_timestamp();
begin
  if p_actor_user_id is null or length(p_actor_user_id) <> 36 then
    raise exception 'invalid actor';
  end if;
  if v_organization_id is null or length(v_organization_id) <> 36 then
    raise exception 'organization is required';
  end if;
  if length(v_name) < 2 or length(v_name) > 120 then
    raise exception 'workspace name is invalid';
  end if;
  if v_role not in ('Individual','Fund','Treasury','Analyst') then
    raise exception 'invalid role';
  end if;

  perform set_config('rivexis.user_id',p_actor_user_id,true);
  if not exists(select 1 from public.users where id=p_actor_user_id) then
    raise exception 'actor is not provisioned';
  end if;

  select om.role into v_member_role
  from public.organization_members om
  where om.organization_id=v_organization_id
    and om.user_id=p_actor_user_id;

  if v_member_role is null then
    raise exception 'organization not found or access denied';
  end if;
  if v_member_role not in ('OWNER','ADMIN','ANALYST') then
    raise exception 'organization write access required';
  end if;

  perform set_config('rivexis.organization_id',v_organization_id,true);
  perform set_config('rivexis.organization_role',v_member_role,true);

  v_workspace_id:=gen_random_uuid()::text;
  insert into public.workspaces(
    id,owner_user_id,name,role,created_at,organization_id,role_context,settings,updated_at
  ) values(
    v_workspace_id,p_actor_user_id,v_name,v_role,v_now,v_organization_id,v_role,'{}'::jsonb,v_now
  );

  return jsonb_build_object(
    'id',v_workspace_id,
    'name',v_name,
    'role',v_role,
    'organization_id',v_organization_id,
    'access_role',v_member_role,
    'created_at',v_now
  );
end;
$$;

reset role;
revoke all on function public.rivexis_edge_create_organization_workspace(text,jsonb) from public;
revoke all on function public.rivexis_edge_create_organization_workspace(text,jsonb) from anon;
revoke all on function public.rivexis_edge_create_organization_workspace(text,jsonb) from authenticated;
grant execute on function public.rivexis_edge_create_organization_workspace(text,jsonb) to service_role;
