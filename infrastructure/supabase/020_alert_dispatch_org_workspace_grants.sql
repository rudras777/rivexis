-- Organization-aware alert delivery needs two additional read scopes that were
-- introduced after the original dispatcher object grants. Apply them explicitly
-- as the application-table owner so the ACL change is durable and auditable.

set local role rivexis_migrator;

grant select(organization_id)
  on table public.workspaces
  to rivexis_alert_dispatcher;

grant select(organization_id,user_id,role,created_at)
  on table public.organization_members
  to rivexis_alert_dispatcher;

reset role;
