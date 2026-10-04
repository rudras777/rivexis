from __future__ import annotations

from alembic import op

revision = "0019_investigation_review_evidence_links"
down_revision = "0018_protocol_review_evidence_gate"
branch_labels = None
depends_on = None


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _postgres():
        return

    # Correct legacy approvals created before the 0018 evidence gate. Preserve the
    # review artifact and any historical investigation reference, but remove the
    # approval claim when the payload itself says evidence is unavailable.
    op.execute(
        """
        UPDATE public.reports
        SET status = 'draft', approved_by_user_id = NULL, approved_at = NULL
        WHERE report_type = 'protocol_configuration_review'
          AND status = 'approved'
          AND (
            coalesce(payload->'deployment_identity'->>'verified', 'false') <> 'true'
            OR coalesce(jsonb_typeof(payload->'missing_data'), 'null') <> 'array'
            OR jsonb_array_length(coalesce(payload->'missing_data', '[]'::jsonb)) <> 0
          )
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.rivexis_guard_investigation_review_links()
        RETURNS trigger
        LANGUAGE plpgsql
        SET search_path = public, pg_temp
        AS $$
        DECLARE
          v_review_id text;
          v_old_ids jsonb := CASE
            WHEN TG_OP = 'UPDATE' AND jsonb_typeof(OLD.payload->'review_ids') = 'array'
              THEN OLD.payload->'review_ids'
            ELSE '[]'::jsonb
          END;
          v_new_ids jsonb := CASE
            WHEN jsonb_typeof(NEW.payload->'review_ids') = 'array'
              THEN NEW.payload->'review_ids'
            ELSE '[]'::jsonb
          END;
        BEGIN
          IF NEW.report_type <> 'protocol_investigation_case' THEN
            RETURN NEW;
          END IF;

          IF NEW.payload ? 'review_ids' AND jsonb_typeof(NEW.payload->'review_ids') <> 'array' THEN
            RAISE EXCEPTION 'investigation review references must be an array'
              USING ERRCODE = '23514';
          END IF;

          FOR v_review_id IN SELECT jsonb_array_elements_text(v_new_ids)
          LOOP
            -- Preserve historical references exactly as they were. Only newly added
            -- links must satisfy the stronger post-0019 evidence contract.
            IF v_old_ids ? v_review_id THEN
              CONTINUE;
            END IF;

            IF NOT EXISTS (
              SELECT 1
              FROM public.reports r
              WHERE r.id = v_review_id
                AND r.workspace_id = NEW.workspace_id
                AND r.report_type = 'protocol_configuration_review'
                AND r.status = 'approved'
                AND coalesce(r.payload->'deployment_identity'->>'verified', 'false') = 'true'
                AND jsonb_typeof(r.payload->'missing_data') = 'array'
                AND jsonb_array_length(r.payload->'missing_data') = 0
            ) THEN
              RAISE EXCEPTION 'only approved protocol reviews with verified provider evidence can be attached'
                USING ERRCODE = '23514';
            END IF;
          END LOOP;

          RETURN NEW;
        END;
        $$;

        REVOKE ALL ON FUNCTION public.rivexis_guard_investigation_review_links() FROM PUBLIC;

        DROP TRIGGER IF EXISTS rivexis_investigation_review_evidence_gate ON public.reports;
        CREATE TRIGGER rivexis_investigation_review_evidence_gate
        BEFORE INSERT OR UPDATE OF payload ON public.reports
        FOR EACH ROW
        EXECUTE FUNCTION public.rivexis_guard_investigation_review_links();
        """
    )


def downgrade() -> None:
    if not _postgres():
        return
    op.execute("DROP TRIGGER IF EXISTS rivexis_investigation_review_evidence_gate ON public.reports")
    op.execute("DROP FUNCTION IF EXISTS public.rivexis_guard_investigation_review_links()")
