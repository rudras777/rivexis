GRANT rivexis_migrator TO postgres
WITH ADMIN FALSE, INHERIT FALSE, SET TRUE
GRANTED BY postgres;

SET LOCAL ROLE rivexis_migrator;

DROP POLICY IF EXISTS rivexis_organization_bootstrap_insert ON public.organizations;

CREATE POLICY rivexis_organization_bootstrap_insert ON public.organizations
FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1
    FROM public.users
    WHERE users.id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
  )
  AND (
    (
      NULLIF((SELECT current_setting('rivexis.organization_id', true)), '') IS NULL
      AND NULLIF((SELECT current_setting('rivexis.organization_role', true)), '') IS NULL
    )
    OR (
      id::text = NULLIF((SELECT current_setting('rivexis.organization_id', true)), '')
      AND NULLIF((SELECT current_setting('rivexis.organization_role', true)), '') = 'OWNER'
    )
  )
);

SET LOCAL ROLE NONE;

GRANT rivexis_migrator TO postgres
WITH ADMIN FALSE, INHERIT FALSE, SET FALSE
GRANTED BY postgres;
