-- Repair dispatcher object grants under the actual application-table owner.
-- PostgreSQL permits a non-owner GRANT to complete with a warning and no ACL
-- change when the grantor lacks grant options. Running these grants explicitly as
-- rivexis_migrator makes the intended least-privilege ACL durable.

set local role rivexis_migrator;

grant select on table public.alerts to rivexis_alert_dispatcher;
grant update(
  delivery_status,delivery_attempts,next_delivery_at,last_delivery_error,
  delivered_at,dead_lettered_at,updated_at,delivery_claim_token,delivery_claimed_at
) on table public.alerts to rivexis_alert_dispatcher;

grant select(id,owner_user_id,name) on table public.workspaces to rivexis_alert_dispatcher;
grant select(id,email) on table public.users to rivexis_alert_dispatcher;
grant select,update on table public.alert_delivery_runtime to rivexis_alert_dispatcher;

reset role;
