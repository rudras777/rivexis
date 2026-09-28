grant rivexis_migrator to postgres with set true, inherit false;
set local role rivexis_migrator;

create or replace function public.rivexis_edge_organization_membership(
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
  v_org_id text := nullif(p_payload->>'organization_id','');
  v_actor_role text;
  v_target_user_id text;
  v_target_email text;
  v_target_role text;
  v_existing_role text;
  v_owner_count bigint;
  v_claim_id text;
  v_claim_hash text;
  v_now timestamptz := clock_timestamp();
  v_expires_at timestamptz;
begin
  if p_actor_user_id is null or length(p_actor_user_id) <> 36 then
    raise exception 'invalid actor';
  end if;
  if not exists(select 1 from public.users where id=p_actor_user_id) then
    raise exception 'actor is not provisioned';
  end if;
  perform set_config('rivexis.user_id', p_actor_user_id, true);

  if v_org_id is null then raise exception 'organization not found'; end if;

  select om.role into v_actor_role
  from public.organization_members om
  where om.organization_id=v_org_id and om.user_id=p_actor_user_id;

  if p_action = 'list' then
    if v_actor_role is null then raise exception 'organization not found'; end if;
    select coalesce(jsonb_agg(jsonb_build_object(
      'user_id',u.id,
      'email',u.email,
      'role',om.role,
      'created_at',om.created_at
    ) order by om.created_at),'[]'::jsonb)
    into result
    from public.organization_members om
    join public.users u on u.id=om.user_id
    where om.organization_id=v_org_id;
    return jsonb_build_object('items',result,'member_role',v_actor_role);
  end if;

  if p_action = 'create_claim' then
    v_claim_hash := lower(coalesce(p_payload->>'token_hash',''));
    if v_claim_hash !~ '^[0-9a-f]{64}$' then raise exception 'invalid claim hash'; end if;
    delete from public.edge_organization_membership_claims
      where (expires_at <= v_now or consumed_at is not null)
         or (organization_id=v_org_id and user_id=p_actor_user_id and consumed_at is null);
    v_claim_id := gen_random_uuid()::text;
    v_expires_at := v_now + interval '15 minutes';
    begin
      insert into public.edge_organization_membership_claims(id,organization_id,user_id,token_hash,created_at,expires_at)
      values(v_claim_id,v_org_id,p_actor_user_id,v_claim_hash,v_now,v_expires_at);
    exception when foreign_key_violation then
      raise exception 'organization not found';
    end;
    return jsonb_build_object('organization_id',v_org_id,'claim_id',v_claim_id,'expires_at',v_expires_at,'expires_in_seconds',900);
  end if;

  if v_actor_role not in ('OWNER','ADMIN') then
    raise exception 'organization administration required';
  end if;

  if p_action = 'update_existing' then
    v_target_role := coalesce(p_payload->>'role','');
    if v_target_role not in ('OWNER','ADMIN','ANALYST','VIEWER') then raise exception 'invalid organization role'; end if;
    v_target_email := lower(trim(coalesce(p_payload->>'email','')));
    select u.id into v_target_user_id from public.users u where lower(u.email)=v_target_email;
    if v_target_user_id is null then raise exception 'user must already have a Rivexis account'; end if;
    select om.role into v_existing_role from public.organization_members om
      where om.organization_id=v_org_id and om.user_id=v_target_user_id;
    if v_existing_role is null then raise exception 'new organization members require an authenticated membership claim'; end if;

    if v_actor_role <> 'OWNER' and (v_target_role='OWNER' or v_existing_role='OWNER') then
      raise exception 'only an organization owner may grant or modify OWNER membership';
    end if;
    if v_existing_role='OWNER' and v_target_role<>'OWNER' then
      select count(*) into v_owner_count from public.organization_members
        where organization_id=v_org_id and role='OWNER';
      if v_owner_count <= 1 then raise exception 'cannot demote the last organization owner'; end if;
    end if;

    update public.organization_members set role=v_target_role
      where organization_id=v_org_id and user_id=v_target_user_id;
    return jsonb_build_object('organization_id',v_org_id,'user_id',v_target_user_id,'email',v_target_email,'role',v_target_role);
  end if;

  if p_action = 'accept_claim' then
    v_target_role := coalesce(p_payload->>'role','');
    if v_target_role not in ('OWNER','ADMIN','ANALYST','VIEWER') then raise exception 'invalid organization role'; end if;
    v_claim_hash := lower(coalesce(p_payload->>'token_hash',''));
    if v_claim_hash !~ '^[0-9a-f]{64}$' then raise exception 'invalid membership claim'; end if;

    select c.id,c.user_id into v_claim_id,v_target_user_id
    from public.edge_organization_membership_claims c
    where c.organization_id=v_org_id
      and c.token_hash=v_claim_hash
      and c.consumed_at is null
      and c.expires_at>v_now
    for update;
    if v_claim_id is null then raise exception 'membership claim is invalid or expired'; end if;

    select om.role into v_existing_role from public.organization_members om
      where om.organization_id=v_org_id and om.user_id=v_target_user_id;
    if v_actor_role <> 'OWNER' and (v_target_role='OWNER' or v_existing_role='OWNER') then
      raise exception 'only an organization owner may grant or modify OWNER membership';
    end if;
    if v_existing_role='OWNER' and v_target_role<>'OWNER' then
      select count(*) into v_owner_count from public.organization_members
        where organization_id=v_org_id and role='OWNER';
      if v_owner_count <= 1 then raise exception 'cannot demote the last organization owner'; end if;
    end if;

    insert into public.organization_members(organization_id,user_id,role,created_at)
    values(v_org_id,v_target_user_id,v_target_role,v_now)
    on conflict (organization_id,user_id) do update set role=excluded.role;
    update public.edge_organization_membership_claims set consumed_at=v_now where id=v_claim_id;
    select u.email into v_target_email from public.users u where u.id=v_target_user_id;
    return jsonb_build_object('organization_id',v_org_id,'user_id',v_target_user_id,'email',v_target_email,'role',v_target_role);
  end if;

  if p_action = 'delete' then
    v_target_user_id := nullif(p_payload->>'user_id','');
    if v_target_user_id is null then return jsonb_build_object('deleted',false); end if;
    select om.role into v_existing_role from public.organization_members om
      where om.organization_id=v_org_id and om.user_id=v_target_user_id;
    if v_existing_role is null then return jsonb_build_object('deleted',false); end if;
    if v_existing_role='OWNER' then
      if v_actor_role<>'OWNER' then raise exception 'only an organization owner may remove OWNER membership'; end if;
      select count(*) into v_owner_count from public.organization_members
        where organization_id=v_org_id and role='OWNER';
      if v_owner_count<=1 then raise exception 'cannot remove the last organization owner'; end if;
    end if;
    delete from public.organization_members where organization_id=v_org_id and user_id=v_target_user_id;
    return jsonb_build_object('deleted',true,'user_id',v_target_user_id);
  end if;

  raise exception 'unsupported organization membership action';
end;
$$;

revoke all on function public.rivexis_edge_organization_membership(text,text,jsonb) from public, anon, authenticated;
grant execute on function public.rivexis_edge_organization_membership(text,text,jsonb) to service_role;
comment on function public.rivexis_edge_organization_membership(text,text,jsonb) is
  'Service-role-only compatibility bridge for organization membership list, existing-member role updates, opaque claim acceptance, and removal. Non-members may create short-lived opaque claims for a target organization; every privileged mutation rechecks current OWNER/ADMIN membership and last-owner invariants.';

reset role;
revoke set option for rivexis_migrator from postgres granted by postgres;
