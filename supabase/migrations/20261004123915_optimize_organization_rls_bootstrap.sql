GRANT rivexis_migrator TO postgres
WITH ADMIN FALSE, INHERIT FALSE, SET TRUE
GRANTED BY postgres;

SET LOCAL ROLE rivexis_migrator;

DROP POLICY IF EXISTS rivexis_tenant_isolation ON public.organizations;
DROP POLICY IF EXISTS rivexis_organizations_select ON public.organizations;
DROP POLICY IF EXISTS rivexis_organizations_update ON public.organizations;
DROP POLICY IF EXISTS rivexis_organizations_delete ON public.organizations;
DROP POLICY IF EXISTS rivexis_organization_bootstrap_insert ON public.organizations;

CREATE POLICY rivexis_organizations_select ON public.organizations
FOR SELECT
USING (
  id IN (
    SELECT organization_id
    FROM public.organization_members
    WHERE user_id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
  )
);

CREATE POLICY rivexis_organizations_update ON public.organizations
FOR UPDATE
USING (
  id IN (
    SELECT organization_id
    FROM public.organization_members
    WHERE user_id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
  )
)
WITH CHECK (
  id IN (
    SELECT organization_id
    FROM public.organization_members
    WHERE user_id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
  )
);

CREATE POLICY rivexis_organizations_delete ON public.organizations
FOR DELETE
USING (
  id IN (
    SELECT organization_id
    FROM public.organization_members
    WHERE user_id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
  )
);

CREATE POLICY rivexis_organization_bootstrap_insert ON public.organizations
FOR INSERT
WITH CHECK (
  id::text = NULLIF((SELECT current_setting('rivexis.organization_id', true)), '')
  AND NULLIF((SELECT current_setting('rivexis.organization_role', true)), '') = 'OWNER'
  AND EXISTS (
    SELECT 1
    FROM public.users
    WHERE users.id::text = NULLIF((SELECT current_setting('rivexis.user_id', true)), '')
  )
);

SET LOCAL ROLE NONE;

GRANT rivexis_migrator TO postgres
WITH ADMIN FALSE, INHERIT FALSE, SET FALSE
GRANTED BY postgres;
