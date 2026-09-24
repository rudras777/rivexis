"""Harden PostgreSQL foreign-key and tenant-policy performance."""

from __future__ import annotations

import hashlib

from alembic import op
import sqlalchemy as sa


revision = "0012_postgres_performance_hardening"
down_revision = "0011_postgres_runtime_controls"
branch_labels = None
depends_on = None


REDUNDANT_INDEXES = (
    ("users", "ix_users_email", ("email",), True),
    ("workspaces", "ix_workspaces_owner_user_id", ("owner_user_id",), False),
)


def _index_name(table: str, columns: tuple[str, ...]) -> str:
    raw = f"ix_fk_{table}_{'_'.join(columns)}"
    if len(raw) <= 63:
        return raw
    digest = hashlib.sha256(raw.encode()).hexdigest()[:8]
    return f"{raw[:54]}_{digest}"


def _column_sets(inspector: sa.Inspector, table: str) -> list[tuple[str, ...]]:
    result: list[tuple[str, ...]] = []
    for index in inspector.get_indexes(table):
        columns = tuple(index.get("column_names") or ())
        if columns:
            result.append(columns)
    primary_key = tuple(inspector.get_pk_constraint(table).get("constrained_columns") or ())
    if primary_key:
        result.append(primary_key)
    for constraint in inspector.get_unique_constraints(table):
        columns = tuple(constraint.get("column_names") or ())
        if columns:
            result.append(columns)
    return result


def _add_missing_foreign_key_indexes() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table in sorted(inspector.get_table_names()):
        covering = _column_sets(inspector, table)
        foreign_keys = sorted(
            inspector.get_foreign_keys(table),
            key=lambda item: tuple(item.get("constrained_columns") or ()),
        )
        for foreign_key in foreign_keys:
            columns = tuple(foreign_key.get("constrained_columns") or ())
            if not columns or any(candidate[: len(columns)] == columns for candidate in covering):
                continue
            op.create_index(_index_name(table, columns), table, list(columns))
            covering.append(columns)


def _drop_redundant_indexes() -> None:
    inspector = sa.inspect(op.get_bind())
    for table, name, _, _ in REDUNDANT_INDEXES:
        if table not in inspector.get_table_names():
            continue
        if name in {item["name"] for item in inspector.get_indexes(table)}:
            op.drop_index(name, table_name=table)


def _cached_context(name: str) -> str:
    return f"NULLIF((SELECT current_setting('{name}', true)), '')"


def _replace_tenant_policies() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    actor = _cached_context("rivexis.user_id")
    organization = _cached_context("rivexis.organization_id")
    organization_role = _cached_context("rivexis.organization_role")
    policies = {
        "workspaces": (
            f"((organization_id IS NULL AND owner_user_id::text = {actor}) OR "
            f"(organization_id IS NOT NULL AND organization_id IN "
            f"(SELECT organization_id FROM organization_members WHERE user_id::text = {actor})))"
        ),
        "organizations": (
            f"(id IN (SELECT organization_id FROM organization_members WHERE user_id::text = {actor}))"
        ),
        "organization_members": (
            f"(user_id::text = {actor} OR "
            f"(organization_id::text = {organization} AND {organization_role} IN ('OWNER','ADMIN')))"
        ),
        "profiles": f"(user_id::text = {actor})",
    }
    for table, policy in policies.items():
        op.execute(sa.text(f'DROP POLICY IF EXISTS rivexis_tenant_isolation ON "{table}"'))
        op.execute(
            sa.text(
                f'CREATE POLICY rivexis_tenant_isolation ON "{table}" '
                f"USING {policy} WITH CHECK {policy}"
            )
        )


def upgrade() -> None:
    _add_missing_foreign_key_indexes()
    _drop_redundant_indexes()
    _replace_tenant_policies()


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table in sorted(inspector.get_table_names()):
        for index in inspector.get_indexes(table):
            name = str(index.get("name") or "")
            if name.startswith("ix_fk_"):
                op.drop_index(name, table_name=table)
    for table, name, columns, unique in REDUNDANT_INDEXES:
        if table in sa.inspect(bind).get_table_names():
            op.create_index(name, table, list(columns), unique=unique)
    if bind.dialect.name == "postgresql":
        actor = "NULLIF(current_setting('rivexis.user_id', true), '')"
        organization = "NULLIF(current_setting('rivexis.organization_id', true), '')"
        organization_role = "NULLIF(current_setting('rivexis.organization_role', true), '')"
        policies = {
            "workspaces": (
                f"((organization_id IS NULL AND owner_user_id::text = {actor}) OR "
                f"(organization_id IS NOT NULL AND organization_id IN "
                f"(SELECT organization_id FROM organization_members WHERE user_id::text = {actor})))"
            ),
            "organizations": (
                f"(id IN (SELECT organization_id FROM organization_members WHERE user_id::text = {actor}))"
            ),
            "organization_members": (
                f"(user_id::text = {actor} OR "
                f"(organization_id::text = {organization} AND {organization_role} IN ('OWNER','ADMIN')))"
            ),
            "profiles": f"(user_id::text = {actor})",
        }
        for table, policy in policies.items():
            op.execute(sa.text(f'DROP POLICY IF EXISTS rivexis_tenant_isolation ON "{table}"'))
            op.execute(
                sa.text(
                    f'CREATE POLICY rivexis_tenant_isolation ON "{table}" '
                    f"USING {policy} WITH CHECK {policy}"
                )
            )
