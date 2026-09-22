-- Run as the owner of the Alembic-created Rivexis tables.
-- Grant only tables mapped by the current operational SQLAlchemy model.
-- New tables require an explicit reviewed grant in a later migration.
grant select, insert, update, delete on table
  public.alerts,
  public.analyses,
  public.audit_logs,
  public.data_sources,
  public.decisions,
  public.monitors,
  public.organization_members,
  public.organizations,
  public.portfolios,
  public.provider_requests,
  public.reports,
  public.saved_analyses,
  public.users,
  public.workspaces
to rivexis_app;
