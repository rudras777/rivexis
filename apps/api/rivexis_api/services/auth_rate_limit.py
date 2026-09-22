from __future__ import annotations

import hashlib
import hmac
import os
import threading
import time
from collections import defaultdict, deque
from uuid import uuid4

from rivexis_api.core.config import settings

_lock = threading.RLock()
_memory: dict[str, deque[float]] = defaultdict(deque)
_global_memory: deque[float] = deque()
_redis_client = None
_instance = uuid4().hex
_seq = 0

_REDIS_SCRIPT = """
local key=KEYS[1]
local cutoff=tonumber(ARGV[1])
local now=tonumber(ARGV[2])
local member=ARGV[3]
local limit=tonumber(ARGV[4])
redis.call('ZREMRANGEBYSCORE',key,'-inf',cutoff)
local count=redis.call('ZCARD',key)
if count >= limit then return 0 end
redis.call('ZADD',key,now,member)
redis.call('EXPIRE',key,70)
return 1
"""


def _identity(email: str) -> str:
    normalized = str(email or "").strip().lower()[:320]
    digest = hmac.new(settings.auth_secret.encode(), ("login:" + normalized).encode(), hashlib.sha256).hexdigest()
    return digest


def _limit() -> int:
    try:
        return max(1, min(1000, int(os.getenv("RIVEXIS_AUTH_LOGIN_ATTEMPTS_PER_MINUTE", str(settings.auth_login_attempts_per_minute)))))
    except ValueError:
        return max(1, int(settings.auth_login_attempts_per_minute))


def _global_limit() -> int:
    try:
        return max(1, min(10000, int(os.getenv("RIVEXIS_AUTH_GLOBAL_ATTEMPTS_PER_MINUTE", str(settings.auth_global_attempts_per_minute)))))
    except ValueError:
        return max(1, int(settings.auth_global_attempts_per_minute))


def _backend() -> str:
    return os.getenv("RIVEXIS_AUTH_RATE_LIMIT_BACKEND", settings.auth_rate_limit_backend).strip().lower()


def _redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Redis auth rate limiter requested but redis-py is not installed") from exc
    url = os.getenv("REDIS_URL", settings.redis_url).strip()
    if not url:
        raise RuntimeError("Redis auth rate limiter requested but REDIS_URL is not configured")
    _redis_client = redis.Redis.from_url(url, decode_responses=True)
    return _redis_client


def consume_login_attempt(email: str, *, now: float | None = None) -> bool:
    """Consume global + account authentication budget without storing the account email.

    The global budget prevents CPU exhaustion through rotating random email addresses,
    while the account bucket still limits credential guessing against one identity.
    Production requires Redis so both dimensions are shared across API replicas.
    """
    global _seq
    timestamp = float(time.time() if now is None else now)
    key = _identity(email)
    limit = _limit()
    global_limit = _global_limit()
    if _backend() == "redis":
        with _lock:
            _seq += 1
            seq = _seq
        global_member = f"{timestamp:.6f}:{_instance}:global:{seq}"
        global_result = _redis().eval(
            _REDIS_SCRIPT, 1, "rivexis:auth-global", timestamp - 60.0, timestamp, global_member, global_limit
        )
        if not bool(int(global_result)):
            return False
        account_member = f"{timestamp:.6f}:{_instance}:account:{seq}"
        result = _redis().eval(
            _REDIS_SCRIPT, 1, f"rivexis:auth-login:{key}", timestamp - 60.0, timestamp, account_member, limit
        )
        return bool(int(result))
    with _lock:
        cutoff = timestamp - 60.0
        while _global_memory and _global_memory[0] <= cutoff:
            _global_memory.popleft()
        if len(_global_memory) >= global_limit:
            return False
        _global_memory.append(timestamp)
        q = _memory[key]
        while q and q[0] <= cutoff:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(timestamp)
        return True


def clear_login_attempts(email: str) -> None:
    key = _identity(email)
    if _backend() == "redis":
        _redis().delete(f"rivexis:auth-login:{key}")
        return
    with _lock:
        _memory.pop(key, None)


def reset_auth_rate_limit_for_tests() -> None:
    global _redis_client
    with _lock:
        _memory.clear()
        _global_memory.clear()
    _redis_client = None
