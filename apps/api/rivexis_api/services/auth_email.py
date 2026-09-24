from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import secrets
from urllib.parse import quote, urlsplit

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, String, select
from sqlalchemy.orm import Mapped, mapped_column

from rivexis_api.core.config import settings
from rivexis_api.core.security import hash_password
from rivexis_api.services.auth_rate_limit import consume_login_attempt
from rivexis_api.services.db import Base, SessionLocal, UserRow, now
from rivexis_api.services.store import audit, get_user
from rivexis_api.services.transactional_email import (
    EmailAcceptance,
    EmailConfigurationError,
    EmailDeliveryError,
    EmailSettings,
    send_template_email,
    validate_email_configuration,
)


class UserAuthStateRow(Base):
    __tablename__ = "user_auth_state"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verification_token_digest: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    verification_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_reset_token_digest: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    password_reset_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )


class AuthEmailRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class AuthTokenConfirm(BaseModel):
    token: str = Field(min_length=32, max_length=512)


class PasswordResetConfirm(AuthTokenConfirm):
    password: str = Field(min_length=8, max_length=256)


router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def _bool_env(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _ttl(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer number of seconds") from exc
    if not (300 <= value <= 86400):
        raise RuntimeError(f"{name} must be between 300 and 86400 seconds")
    return value


def email_verification_required() -> bool:
    return _bool_env("RIVEXIS_EMAIL_VERIFICATION_REQUIRED", False)


def _production() -> bool:
    return os.getenv("RIVEXIS_ENV", str(settings.environment or "development")).strip().lower() in {
        "production",
        "prod",
    }


def _public_web_url(*, required: bool) -> str | None:
    raw = os.getenv("RIVEXIS_PUBLIC_WEB_URL", "").strip().rstrip("/")
    if not raw:
        if required:
            raise EmailConfigurationError(
                "RIVEXIS_PUBLIC_WEB_URL is required before password-reset email can send"
            )
        return None
    parts = urlsplit(raw)
    if parts.scheme not in ({"https"} if _production() else {"http", "https"}):
        raise EmailConfigurationError("RIVEXIS_PUBLIC_WEB_URL must use an approved scheme")
    if not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise EmailConfigurationError("RIVEXIS_PUBLIC_WEB_URL must be a clean web origin")
    if parts.path not in {"", "/"}:
        raise EmailConfigurationError("RIVEXIS_PUBLIC_WEB_URL must not contain a path")
    return raw


def validate_auth_email_runtime() -> dict[str, object]:
    verification_required = email_verification_required()
    verification_ttl = _ttl("RIVEXIS_EMAIL_VERIFICATION_TTL_SECONDS", 1800)
    reset_ttl = _ttl("RIVEXIS_PASSWORD_RESET_TTL_SECONDS", 1800)
    cfg = EmailSettings.from_env()
    status = validate_email_configuration(cfg)
    if status.get("enabled") and cfg.password_reset_template_id:
        _public_web_url(required=True)
    if not verification_required:
        return {
            "verification_required": False,
            "verification_ttl_seconds": verification_ttl,
            "password_reset_ttl_seconds": reset_ttl,
            "email_provider": status.get("provider"),
        }
    if not status.get("enabled") or not cfg.verification_template_id:
        raise EmailConfigurationError(
            "Email verification cannot be required until Brevo and the verification template are configured"
        )
    return {
        "verification_required": True,
        "verification_ttl_seconds": verification_ttl,
        "password_reset_ttl_seconds": reset_ttl,
        "email_provider": status.get("provider"),
        "sandbox": status.get("sandbox"),
    }


def _normalize_email(value: str) -> str:
    return str(value or "").strip().lower()


def _digest(raw_token: str, purpose: str) -> str:
    message = f"rivexis-auth-email:v1:{purpose}:{raw_token}".encode()
    return hmac.new(settings.auth_secret.encode(), message, hashlib.sha256).hexdigest()


def _new_token() -> str:
    return secrets.token_urlsafe(32)


def _expiry_minutes(expires_at: datetime) -> int:
    return max(1, int((expires_at - now()).total_seconds() // 60))


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def initialize_user_auth_state(user_id: str, *, verified: bool) -> None:
    with SessionLocal() as db:
        row = db.get(UserAuthStateRow, user_id)
        if row is None:
            row = UserAuthStateRow(
                user_id=user_id,
                email_verified_at=now() if verified else None,
            )
            db.add(row)
        elif verified and row.email_verified_at is None:
            row.email_verified_at = now()
        db.commit()


def is_email_verified(user_id: str) -> bool:
    with SessionLocal() as db:
        row = db.get(UserAuthStateRow, user_id)
        return bool(row and row.email_verified_at is not None)


def _consume_flow_budget(flow: str, email: str) -> None:
    try:
        allowed = consume_login_attempt(f"{flow}:{_normalize_email(email)}")
    except Exception as exc:
        raise HTTPException(503, "Authentication rate limiter unavailable") from exc
    if not allowed:
        raise HTTPException(429, "Too many authentication requests")


def issue_verification_email(user: UserRow) -> EmailAcceptance:
    raw_token = _new_token()
    token_digest = _digest(raw_token, "verification")
    expires_at = now() + timedelta(
        seconds=_ttl("RIVEXIS_EMAIL_VERIFICATION_TTL_SECONDS", 1800)
    )
    with SessionLocal() as db:
        row = db.get(UserAuthStateRow, user.id)
        if row is None:
            row = UserAuthStateRow(user_id=user.id)
            db.add(row)
        if row.email_verified_at is not None:
            return EmailAcceptance(
                status="already_verified",
                provider="internal",
                provider_message_id=None,
                sandbox=False,
            )
        row.verification_token_digest = token_digest
        row.verification_expires_at = expires_at
        row.updated_at = now()
        db.commit()
    return send_template_email(
        recipient=user.email,
        kind="verification",
        params={"code": raw_token, "expiry_minutes": _expiry_minutes(expires_at)},
        idempotency_key=f"verify:{token_digest[:32]}",
    )


def issue_password_reset_email(user: UserRow) -> EmailAcceptance:
    base_url = _public_web_url(required=True)
    assert base_url is not None
    raw_token = _new_token()
    token_digest = _digest(raw_token, "password-reset")
    expires_at = now() + timedelta(
        seconds=_ttl("RIVEXIS_PASSWORD_RESET_TTL_SECONDS", 1800)
    )
    with SessionLocal() as db:
        row = db.get(UserAuthStateRow, user.id)
        if row is None:
            row = UserAuthStateRow(user_id=user.id, email_verified_at=now())
            db.add(row)
        row.password_reset_token_digest = token_digest
        row.password_reset_expires_at = expires_at
        row.updated_at = now()
        db.commit()
    reset_url = f"{base_url}/reset-password?token={quote(raw_token, safe='')}"
    return send_template_email(
        recipient=user.email,
        kind="password_reset",
        params={"reset_url": reset_url, "expiry_minutes": _expiry_minutes(expires_at)},
        idempotency_key=f"reset:{token_digest[:32]}",
    )


def consume_verification_token(raw_token: str) -> UserRow | None:
    digest = _digest(raw_token, "verification")
    current = now()
    with SessionLocal() as db:
        row = db.scalar(
            select(UserAuthStateRow).where(
                UserAuthStateRow.verification_token_digest == digest
            )
        )
        if row is None or _aware(row.verification_expires_at) is None or _aware(row.verification_expires_at) <= current:
            return None
        user = db.get(UserRow, row.user_id)
        if user is None:
            return None
        row.email_verified_at = current
        row.verification_token_digest = None
        row.verification_expires_at = None
        row.updated_at = current
        db.commit()
        db.refresh(user)
        return user


def consume_password_reset_token(raw_token: str, new_password_hash: str) -> UserRow | None:
    digest = _digest(raw_token, "password-reset")
    current = now()
    with SessionLocal() as db:
        row = db.scalar(
            select(UserAuthStateRow).where(
                UserAuthStateRow.password_reset_token_digest == digest
            )
        )
        if row is None or _aware(row.password_reset_expires_at) is None or _aware(row.password_reset_expires_at) <= current:
            return None
        user = db.get(UserRow, row.user_id)
        if user is None:
            return None
        user.password_hash = new_password_hash
        user.token_version = int(user.token_version or 0) + 1
        row.password_reset_token_digest = None
        row.password_reset_expires_at = None
        row.updated_at = current
        db.commit()
        db.refresh(user)
        return user


@router.post("/email-verification/request", status_code=202)
def request_email_verification(req: AuthEmailRequest):
    _consume_flow_budget("verify", req.email)
    user = get_user(req.email)
    if user is not None and not is_email_verified(user.id):
        try:
            issue_verification_email(user)
            audit("auth.email_verification.request", "user", user.id, actor_user_id=user.id)
        except (EmailConfigurationError, EmailDeliveryError, ValueError):
            # Enumeration safety: provider/configuration failures for an existing account
            # do not alter the public response compared with an unknown address.
            pass
    return {"status": "accepted"}


@router.post("/email-verification/confirm")
def confirm_email_verification(req: AuthTokenConfirm):
    user = consume_verification_token(req.token)
    if user is None:
        raise HTTPException(400, "Verification token is invalid or expired")
    audit("auth.email_verification.confirm", "user", user.id, actor_user_id=user.id)
    return {"status": "verified"}


@router.post("/password-reset/request", status_code=202)
def request_password_reset(req: AuthEmailRequest):
    _consume_flow_budget("reset", req.email)
    user = get_user(req.email)
    if user is not None:
        try:
            issue_password_reset_email(user)
            audit("auth.password_reset.request", "user", user.id, actor_user_id=user.id)
        except (EmailConfigurationError, EmailDeliveryError, ValueError):
            pass
    return {"status": "accepted"}


@router.post("/password-reset/confirm")
def confirm_password_reset(req: PasswordResetConfirm):
    user = consume_password_reset_token(req.token, hash_password(req.password))
    if user is None:
        raise HTTPException(400, "Password reset token is invalid or expired")
    audit("auth.password_reset.confirm", "user", user.id, actor_user_id=user.id)
    return {"status": "password_reset", "sessions_revoked": True}
