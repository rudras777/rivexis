-- ACTIVATION RECIPE, NOT AN APPLIED MIGRATION. Requires specific production approval.
-- Review the exact deployed source, additive schema, quotas, RPC rights and
-- inactive template first. Store the matching worker token privately in Vault
-- as rivexis_defi_monitor_token; never put its value in SQL/source/chat.
-- The independent worker application token authenticates every invocation.
select cron.schedule(
  'rivexis-defi-monitor-v1',
  '*/5 * * * *',
  $cron$
  select net.http_post(
    url:='https://ivszvufdonfgwjpfgwii.supabase.co/functions/v1/rivexis-defi-monitor',
    headers:=jsonb_build_object('Content-Type','application/json','x-rivexis-monitor-token',
      (select decrypted_secret from vault.decrypted_secrets where name='rivexis_defi_monitor_token')),
    body:='{}'::jsonb,
    timeout_milliseconds:=60000
  );
  $cron$
);
-- Worker must be deployed with gateway verify_jwt=false and its own mandatory
-- token check. This recipe neither disables existing JWT settings nor modifies
-- the existing legacy alert scheduler. No schedule is installed automatically.
