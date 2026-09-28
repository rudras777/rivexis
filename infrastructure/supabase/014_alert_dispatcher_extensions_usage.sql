-- Least-privilege pgcrypto schema access required by the NOLOGIN alert dispatcher.
-- The role receives USAGE only; it does not receive CREATE or raw table privileges.
grant usage on schema extensions to rivexis_alert_dispatcher;
