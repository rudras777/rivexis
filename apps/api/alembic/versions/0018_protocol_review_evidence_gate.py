from __future__ import annotations

from alembic import op

revision = "0018_protocol_review_evidence_gate"
down_revision = "0017_function_default_privileges"
branch_labels = None
depends_on = None


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _postgres():
        return
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.rivexis_guard_protocol_review_approval()
        RETURNS trigger
        LANGUAGE plpgsql
        SET search_path = public, pg_temp
        AS $$
        BEGIN
          IF NEW.report_type = 'protocol_configuration_review'
             AND NEW.status = 'approved'
             AND OLD.status IS DISTINCT FROM NEW.status THEN
            IF coalesce(NEW.payload->'deployment_identity'->>'verified', 'false') <> 'true'
               OR coalesce(jsonb_typeof(NEW.payload->'missing_data'), 'null') <> 'array'
               OR jsonb_array_length(coalesce(NEW.payload->'missing_data', '[]'::jsonb)) <> 0 THEN
              RAISE EXCEPTION 'protocol review cannot be approved without verified provider evidence'
                USING ERRCODE = '23514';
            END IF;
          END IF;
          RETURN NEW;
        END;
        $$;

        REVOKE ALL ON FUNCTION public.rivexis_guard_protocol_review_approval() FROM PUBLIC;

        DROP TRIGGER IF EXISTS rivexis_protocol_review_evidence_gate ON public.reports;
        CREATE TRIGGER rivexis_protocol_review_evidence_gate
        BEFORE UPDATE OF status, approved_by_user_id, approved_at ON public.reports
        FOR EACH ROW
        EXECUTE FUNCTION public.rivexis_guard_protocol_review_approval();
        """
    )


def downgrade() -> None:
    if not _postgres():
        return
    op.execute("DROP TRIGGER IF EXISTS rivexis_protocol_review_evidence_gate ON public.reports")
    op.execute("DROP FUNCTION IF EXISTS public.rivexis_guard_protocol_review_approval()")
