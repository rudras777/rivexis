-- SECURITY DEFINER functions receive EXECUTE for PUBLIC by default unless it is
-- revoked explicitly. Keep organization workspace creation behind the Edge API
-- cookie/session + CSRF boundary by allowing only service_role to invoke it.

set local role rivexis_migrator;

revoke all on function public.rivexis_edge_create_organization_workspace(text,jsonb) from public;
revoke all on function public.rivexis_edge_create_organization_workspace(text,jsonb) from anon;
revoke all on function public.rivexis_edge_create_organization_workspace(text,jsonb) from authenticated;
grant execute on function public.rivexis_edge_create_organization_workspace(text,jsonb) to service_role;

reset role;
