-- Disposable database ONLY. Intentionally fails if auth already exists.
create schema auth;
create table auth.users(id uuid primary key,email text,email_confirmed_at timestamptz);
do $$begin
 if not exists(select 1 from pg_roles where rolname='anon') then create role anon nologin;end if;
 if not exists(select 1 from pg_roles where rolname='authenticated') then create role authenticated nologin;end if;
 if not exists(select 1 from pg_roles where rolname='service_role') then create role service_role nologin bypassrls;end if;
 if exists(select 1 from pg_roles where rolname in ('anon','authenticated') and (rolsuper or rolbypassrls or rolcanlogin)) then raise exception 'Unsafe fixture roles';end if;
end$$;
create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
grant usage on schema auth to authenticated,service_role;
grant select on auth.users to service_role;
grant execute on function auth.uid() to authenticated;
insert into auth.users values
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','first@example.invalid',now()),
 ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','second@example.invalid',now()),
 ('cccccccc-cccc-4ccc-8ccc-cccccccccccc','third@example.invalid',now()),
 ('dddddddd-dddd-4ddd-8ddd-dddddddddddd','fourth@example.invalid',now());
