from __future__ import annotations

from typing import Any

from .version import RELEASE_CODENAME

GATE_SPECS: dict[str, dict[str, Any]] = {
    "otlp-local": {
        "command": ["python", "scripts/certify_otlp_export.py"],
        "prerequisites": [],
        "activation": "always",
        "destructive": False,
        "purpose": "Local W3C trace and OTLP/HTTP protobuf export contract.",
    },
    "postgres-rls": {
        "command": ["python", "scripts/certify_postgres_rls.py"],
        "prerequisites": ["RIVEXIS_RLS_ADMIN_DATABASE_URL", "RIVEXIS_RLS_APP_DATABASE_URL", "RIVEXIS_RLS_WORKER_DATABASE_URL"],
        "activation": "all_prerequisites",
        "destructive": False,
        "purpose": "Adversarial PostgreSQL RLS verification with separate admin, non-bypass API, and least-privilege BYPASSRLS alert-worker roles.",
    },
    "postgres-dr": {
        "command": ["python", "scripts/certify_postgres_dr.py"],
        "prerequisites": [
            "RIVEXIS_BACKUP_SOURCE_DATABASE_URL",
            "RIVEXIS_BACKUP_RESTORE_DATABASE_URL",
            "RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY",
        ],
        "activation": "all_prerequisites",
        "destructive": True,
        "purpose": "Approved disposable PostgreSQL backup/restore disaster-recovery drill with measured RTO.",
    },
    "redis-distributed": {
        "command": ["python", "scripts/certify_redis_distributed.py"],
        "prerequisites": ["REDIS_URL"],
        "activation": "all_prerequisites",
        "destructive": False,
        "purpose": "Shared Redis atomic budget/circuit behavior and latency under concurrent workers.",
    },
    "registry-upstream": {
        "command": ["python", "scripts/certify_registry_upstream.py"],
        "prerequisites": ["RIVEXIS_CERTIFY_REGISTRY_UPSTREAM"],
        "activation": "truthy:RIVEXIS_CERTIFY_REGISTRY_UPSTREAM",
        "destructive": False,
        "purpose": "Re-certify pinned protocol deployment registry evidence against approved upstream sources.",
    },
    "live-providers": {
        "command": ["python", "scripts/certify_live_providers.py"],
        "prerequisites": ["RIVEXIS_CERTIFY_LIVE_PROVIDERS"],
        "activation": "truthy:RIVEXIS_CERTIFY_LIVE_PROVIDERS",
        "destructive": False,
        "purpose": "Credentialed smoke/canonicalization checks for configured licensed providers.",
    },
    "protocol-adapters": {
        "command": ["python", "scripts/certify_protocol_adapters.py"],
        "prerequisites": [
            "RIVEXIS_CERT_AAVE_ASSET",
            "RIVEXIS_CERT_COMPOUND_ASSET",
            "RIVEXIS_CERT_MORPHO_MARKET_ID",
        ],
        "activation": "any_prerequisites",
        "destructive": False,
        "purpose": "Protocol-native adapter certification against an approved chain/market target.",
    },
    "archive-history": {
        "command": ["python", "scripts/certify_protocol_history.py"],
        "prerequisites": ["RIVEXIS_CERT_HISTORY_ADAPTER"],
        "activation": "all_prerequisites",
        "destructive": False,
        "purpose": "Archive-RPC historical range/reorg behavior certification for a configured adapter.",
    },
    "dependency-gates": {
        "command": ["python", "scripts/certify_dependency_gates.py"],
        "prerequisites": [],
        "activation": "always",
        "destructive": False,
        "purpose": "Resolved Python/frontend quality, audit, production build, Playwright and accessibility gates.",
    },
}

REQUIRED_STAGING_GATES = tuple(GATE_SPECS)

PROFILE_GATES: dict[str, tuple[str, ...]] = {
    "local": ("otlp-local", "dependency-gates"),
    "postgres-rls": ("postgres-rls",),
    "postgres-dr": ("postgres-dr",),
    "redis": ("redis-distributed",),
    "registry": ("registry-upstream",),
    "providers": ("live-providers",),
    "protocol": ("protocol-adapters",),
    "history": ("archive-history",),
    "dependencies": ("dependency-gates",),
    "full": REQUIRED_STAGING_GATES,
}

TRUTHY = {"1", "true", "yes", "on"}


def classify_gate_process_result(returncode: int, output: str) -> str:
    """Fail-closed classification for child certification processes.

    Gate scripts use exit code 0 for both PASS and SKIP, so exit status alone is not
    enough. Multi-provider certification can emit provider-specific diagnostics before
    the final overall outcome. Prefer the leading/final overall marker, accept the JSON
    PASS object emitted by the history certifier, and reject silent/unrecognized zero
    exits instead of manufacturing a PASS.
    """
    if returncode != 0:
        return "FAIL"
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return "FAIL"
    first, last = lines[0], lines[-1]
    if first.startswith("SKIP ") or last.startswith("SKIP ") or " certification SKIP" in last:
        return "SKIP"
    if first.startswith("PASS ") or " certification: PASS" in last or " certification PASS" in last:
        return "PASS"
    try:
        import json
        payload = json.loads(output)
    except (json.JSONDecodeError, TypeError):
        payload = None
    if isinstance(payload, dict) and payload.get("status") == "PASS":
        return "PASS"
    if isinstance(payload, dict) and payload.get("status") == "SKIP":
        return "SKIP"
    return "FAIL"


def normalize_profile(value: str | None) -> str:
    profile = (value or "local").strip().lower()
    if profile not in PROFILE_GATES:
        raise ValueError(f"unknown certification runner profile {profile!r}; choose one of {', '.join(PROFILE_GATES)}")
    return profile


def profile_allows(profile: str, gate: str) -> bool:
    return gate in PROFILE_GATES[normalize_profile(profile)]


def gate_enabled(gate: str, env: dict[str, str]) -> bool:
    spec = GATE_SPECS[gate]
    activation = str(spec["activation"])
    if activation == "always":
        return True
    if activation == "all_prerequisites":
        return all(bool(env.get(name, "").strip()) for name in spec["prerequisites"])
    if activation == "any_prerequisites":
        return any(bool(env.get(name, "").strip()) for name in spec["prerequisites"])
    if activation.startswith("truthy:"):
        name = activation.split(":", 1)[1]
        return env.get(name, "").strip().lower() in TRUTHY
    raise ValueError(f"unsupported activation rule {activation!r} for {gate}")


def certification_plan() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "release": RELEASE_CODENAME,
        "profiles": {
            profile: {
                "gates": list(gates),
                "command": f"RIVEXIS_CERT_RUNNER_PROFILE={profile} python scripts/certify_staging_suite.py",
            }
            for profile, gates in PROFILE_GATES.items()
        },
        "gates": {
            gate: {
                "profiles": [
                    profile for profile, gates in PROFILE_GATES.items() if gate in gates and profile != "full"
                ],
                "command": " ".join(spec["command"]),
                "prerequisites": list(spec["prerequisites"]),
                "destructive": bool(spec["destructive"]),
                "purpose": spec["purpose"],
            }
            for gate, spec in GATE_SPECS.items()
        },
    }
