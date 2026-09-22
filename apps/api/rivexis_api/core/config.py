from dataclasses import dataclass
import os
from urllib.parse import urlsplit

PRODUCTION_ENVIRONMENTS = {"production", "prod"}
KNOWN_INSECURE_AUTH_SECRETS = {"", "development-only-change-me", "local-compose-secret-change-me", "replace-with-a-long-random-secret"}


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}

@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("RIVEXIS_ENV", "development")
    auth_secret: str = os.getenv("RIVEXIS_AUTH_SECRET", "development-only-change-me")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./rivexis.db")
    allowed_origins: tuple[str, ...] = tuple(x.strip() for x in os.getenv("RIVEXIS_ALLOWED_ORIGINS", "http://localhost:3000").split(",") if x.strip())
    enable_demo_adapter: bool = _bool("ENABLE_DEMO_ADAPTER", True)
    token_ttl_seconds: int = int(os.getenv("RIVEXIS_TOKEN_TTL_SECONDS", "28800"))
    session_cookie_name: str = os.getenv("RIVEXIS_SESSION_COOKIE_NAME", "rivexis_session")
    session_cookie_samesite: str = os.getenv("RIVEXIS_SESSION_COOKIE_SAMESITE", "lax").strip().lower()
    allow_direct_org_member_add: bool = _bool("RIVEXIS_ALLOW_DIRECT_ORG_MEMBER_ADD", True)
    membership_claim_ttl_seconds: int = int(os.getenv("RIVEXIS_MEMBERSHIP_CLAIM_TTL_SECONDS", "900"))
    auth_rate_limit_backend: str = os.getenv("RIVEXIS_AUTH_RATE_LIMIT_BACKEND", "memory").strip().lower()
    auth_login_attempts_per_minute: int = int(os.getenv("RIVEXIS_AUTH_LOGIN_ATTEMPTS_PER_MINUTE", "20"))
    auth_global_attempts_per_minute: int = int(os.getenv("RIVEXIS_AUTH_GLOBAL_ATTEMPTS_PER_MINUTE", "300"))
    redis_url: str = os.getenv("REDIS_URL", "")
    provider_control_backend: str = os.getenv("RIVEXIS_PROVIDER_CONTROL_BACKEND", "memory").strip().lower()

settings = Settings()


def validate_runtime_security(settings_obj: Settings | None = None) -> dict[str, object]:
    """Fail closed on insecure production authentication/demo configuration."""
    cfg = settings_obj or settings
    environment = str(cfg.environment or "").strip().lower()
    production = environment in PRODUCTION_ENVIRONMENTS
    if production:
        secret = str(cfg.auth_secret or "").strip()
        if secret in KNOWN_INSECURE_AUTH_SECRETS or len(secret) < 32:
            raise RuntimeError("RIVEXIS_AUTH_SECRET must be a non-placeholder secret of at least 32 characters in production")
        if bool(cfg.enable_demo_adapter):
            raise RuntimeError("ENABLE_DEMO_ADAPTER must be false in production")
        if bool(cfg.allow_direct_org_member_add):
            raise RuntimeError("RIVEXIS_ALLOW_DIRECT_ORG_MEMBER_ADD must be false in production")
        auth_backend = str(cfg.auth_rate_limit_backend).strip().lower()
        provider_backend = str(cfg.provider_control_backend).strip().lower()
        if auth_backend not in {"postgres", "redis"}:
            raise RuntimeError("RIVEXIS_AUTH_RATE_LIMIT_BACKEND must be postgres or redis in production")
        if provider_backend not in {"postgres", "redis"}:
            raise RuntimeError("RIVEXIS_PROVIDER_CONTROL_BACKEND must be postgres or redis in production")
        if "redis" in {auth_backend, provider_backend} and not str(cfg.redis_url or "").strip():
            raise RuntimeError("REDIS_URL is required when a production distributed-control backend uses redis")
        database_url = str(cfg.database_url or "").strip().lower()
        if not (database_url.startswith("postgresql://") or database_url.startswith("postgresql+")):
            raise RuntimeError("DATABASE_URL must use PostgreSQL in production so tenant RLS is enforceable")
        if int(cfg.auth_login_attempts_per_minute) < 1 or int(cfg.auth_login_attempts_per_minute) > 100:
            raise RuntimeError("RIVEXIS_AUTH_LOGIN_ATTEMPTS_PER_MINUTE must be between 1 and 100 in production")
        if int(cfg.auth_global_attempts_per_minute) < 10 or int(cfg.auth_global_attempts_per_minute) > 10000:
            raise RuntimeError("RIVEXIS_AUTH_GLOBAL_ATTEMPTS_PER_MINUTE must be between 10 and 10000 in production")
        if not cfg.allowed_origins:
            raise RuntimeError("RIVEXIS_ALLOWED_ORIGINS must contain at least one HTTPS origin in production")
        for origin in cfg.allowed_origins:
            parsed = urlsplit(origin)
            if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
                raise RuntimeError("RIVEXIS_ALLOWED_ORIGINS must contain exact HTTPS origins only in production")
            if "*" in origin:
                raise RuntimeError("RIVEXIS_ALLOWED_ORIGINS must not contain wildcards in production")
    if cfg.session_cookie_samesite not in {"lax", "strict", "none"}:
        raise RuntimeError("RIVEXIS_SESSION_COOKIE_SAMESITE must be lax, strict, or none")
    return {
        "environment": environment or "development",
        "production": production,
        "demo_adapter_enabled": bool(cfg.enable_demo_adapter),
        "auth_secret_configured": bool(str(cfg.auth_secret or "").strip()),
        "direct_org_member_add_enabled": bool(cfg.allow_direct_org_member_add),
        "session_cookie_samesite": cfg.session_cookie_samesite,
        "auth_rate_limit_backend": cfg.auth_rate_limit_backend,
        "provider_control_backend": cfg.provider_control_backend,
        "database_backend": "postgresql" if str(cfg.database_url).lower().startswith("postgresql") else "other",
    }
