from __future__ import annotations

from sqlalchemy import text


def inspect_postgres_role_security_state(conn) -> dict[str, object]:
    """Inspect the effective PostgreSQL service identity, including SET ROLE paths."""
    role = conn.execute(text("""
        SELECT current_user,
               session_user,
               rolsuper,
               rolbypassrls,
               rolcreatedb,
               rolcreaterole,
               rolreplication,
               rolinherit,
               rolcanlogin
        FROM pg_roles
        WHERE rolname=current_user
    """)).mappings().one()
    memberships = [
        str(name)
        for name in conn.execute(text("""
            SELECT r.rolname
            FROM pg_roles r
            WHERE r.rolname <> current_user
              AND pg_has_role(current_user, r.oid, 'MEMBER')
            ORDER BY r.rolname
        """)).scalars().all()
    ]
    return {
        **dict(role),
        "parent_role_memberships": memberships,
        "database_create": bool(
            conn.execute(text("SELECT has_database_privilege(current_user, current_database(), 'CREATE')")).scalar()
        ),
        "schema_create": bool(
            conn.execute(text("SELECT has_schema_privilege(current_user, current_schema(), 'CREATE')")).scalar()
        ),
        "owned_relations": [
            str(name)
            for name in conn.execute(text("""
                SELECT c.relname
                FROM pg_class c
                JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname=current_schema()
                  AND c.relkind IN ('r','p','v','m','S','f')
                  AND c.relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)
                ORDER BY c.relname
            """)).scalars().all()
        ],
    }


def validate_standalone_service_role(
    state: dict[str, object], *, label: str, require_bypassrls: bool
) -> None:
    """Enforce a standalone, non-administrative service identity.

    Zero parent-role membership is deliberate: even a NOINHERIT login can use SET ROLE
    when it is a member of another role. Direct role attributes alone therefore do not
    prove the absence of an RLS/admin escalation path.
    """
    role = str(state["current_user"])
    if str(state["session_user"]) != role:
        raise RuntimeError(f"Rivexis {label} refuses altered session authorization / SET ROLE credentials")
    if bool(state["rolsuper"]):
        raise RuntimeError(f"Rivexis {label} refuses SUPERUSER database credentials")
    if bool(state["rolbypassrls"]) != require_bypassrls:
        expectation = "requires BYPASSRLS" if require_bypassrls else "must use NOBYPASSRLS"
        raise RuntimeError(f"Rivexis {label} {expectation}")
    for key, postgres_name in (
        ("rolcreatedb", "CREATEDB"),
        ("rolcreaterole", "CREATEROLE"),
        ("rolreplication", "REPLICATION"),
    ):
        if bool(state[key]):
            raise RuntimeError(f"Rivexis {label} refuses {postgres_name} database authority")
    if bool(state["rolinherit"]):
        raise RuntimeError(f"Rivexis {label} requires a NOINHERIT standalone database role")
    if not bool(state["rolcanlogin"]):
        raise RuntimeError(f"Rivexis {label} requires a LOGIN database role")
    memberships = list(state["parent_role_memberships"])
    if memberships:
        raise RuntimeError(f"Rivexis {label} refuses parent-role membership / SET ROLE escalation paths: {memberships}")
    if bool(state["database_create"]):
        raise RuntimeError(f"Rivexis {label} role must not have database CREATE privilege")
    if bool(state["schema_create"]):
        raise RuntimeError(f"Rivexis {label} role must not have schema CREATE privilege")
    owned = list(state["owned_relations"])
    if owned:
        raise RuntimeError(f"Rivexis {label} role must not own application relations: {owned}")
