-- Safe, replayable bootstrap for the owner-scoped migration role.
-- Historical production bootstrap temporarily used a login credential; that
-- credential material is intentionally not reproduced in source control.
-- All normal migrations assume postgres can SET ROLE into this NOLOGIN role.

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'rivexis_migrator') then
    create role rivexis_migrator
      nologin
      nosuperuser
      nocreatedb
      nocreaterole
      noinherit
      nobypassrls
      noreplication;
  else
    alter role rivexis_migrator
      nologin
      nosuperuser
      nocreatedb
      nocreaterole
      noinherit
      nobypassrls
      noreplication;
  end if;
end
$$;

grant usage, create on schema public to rivexis_migrator;
