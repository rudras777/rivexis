-- Login and provider telemetry need global SELECT/INSERT/UPDATE on these
-- non-tenant-scoped tables, but the runtime has no supported delete path for
-- either object. Remove unused destructive capability from rivexis_app.

set local role rivexis_migrator;

revoke delete on table public.users from rivexis_app;
revoke delete on table public.data_sources from rivexis_app;

reset role;
