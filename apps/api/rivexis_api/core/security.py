from __future__ import annotations
import base64, hashlib, hmac, json, os, time
from rivexis_api.core.config import settings


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters")
    salt = os.urandom(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(key).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt_b64, key_b64 = encoded.split("$", 2)
        if algorithm != "scrypt": return False
        salt = base64.urlsafe_b64decode(salt_b64)
        expected = base64.urlsafe_b64decode(key_b64)
        actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _encode_signed_payload(payload: dict) -> str:
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    sig = _b64(hmac.new(settings.auth_secret.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def _decode_signed_payload(token: str) -> dict:
    body, sig = token.split(".", 1)
    expected = _b64(hmac.new(settings.auth_secret.encode(), body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):
        raise ValueError("invalid signature")
    payload = json.loads(_unb64(body))
    if int(payload["exp"]) < int(time.time()):
        raise ValueError("expired")
    return payload


def create_token(email: str, role: str, token_version: int = 0) -> str:
    payload = {
        "typ": "session", "sub": email.lower(), "role": role, "ver": int(token_version),
        "iat": int(time.time()), "exp": int(time.time()) + settings.token_ttl_seconds,
    }
    return _encode_signed_payload(payload)


def decode_token(token: str) -> dict:
    try:
        payload = _decode_signed_payload(token)
        if payload.get("typ", "session") != "session":
            raise ValueError("wrong token type")
        return payload
    except Exception as exc:
        raise ValueError("Invalid or expired token") from exc


def create_csrf_token(session_token: str) -> str:
    return _b64(hmac.new(settings.auth_secret.encode(), ("csrf:" + session_token).encode(), hashlib.sha256).digest())


def verify_csrf_token(session_token: str, supplied: str) -> bool:
    if not session_token or not supplied:
        return False
    return hmac.compare_digest(create_csrf_token(session_token), supplied)


def create_membership_claim(user_id: str, organization_id: str, token_version: int = 0) -> str:
    now = int(time.time())
    return _encode_signed_payload({
        "typ": "organization_membership_claim", "sub": user_id, "organization_id": organization_id,
        "ver": int(token_version), "iat": now, "exp": now + max(60, int(settings.membership_claim_ttl_seconds)),
        "nonce": _b64(os.urandom(18)),
    })


def decode_membership_claim(token: str, organization_id: str) -> dict:
    try:
        payload = _decode_signed_payload(token)
        if payload.get("typ") != "organization_membership_claim":
            raise ValueError("wrong token type")
        if payload.get("organization_id") != organization_id:
            raise ValueError("wrong organization")
        return payload
    except Exception as exc:
        raise ValueError("Invalid or expired membership claim") from exc
