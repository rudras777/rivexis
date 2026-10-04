-- The normal application runtime has no supported delete operations for these
-- tenant/business records. Keep deletion authority only on datasets with an
-- explicit product delete action or approved retention path.

set local role rivexis_migrator;

revoke delete on table public.alerts from rivexis_app;
revoke delete on table public.analyses from rivexis_app;
revoke delete on table public.decisions from rivexis_app;
revoke delete on table public.organizations from rivexis_app;
revoke delete on table public.portfolios from rivexis_app;
revoke delete on table public.workspaces from rivexis_app;

reset role;
