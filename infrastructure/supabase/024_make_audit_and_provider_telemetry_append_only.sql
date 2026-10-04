-- Normal runtime code appends audit/provider telemetry and approved retention
-- maintenance may delete expired rows, but no supported path rewrites existing
-- records. Remove UPDATE so evidence cannot be silently mutated in place.

set local role rivexis_migrator;

revoke update on table public.audit_logs from rivexis_app;
revoke update on table public.provider_requests from rivexis_app;

reset role;
