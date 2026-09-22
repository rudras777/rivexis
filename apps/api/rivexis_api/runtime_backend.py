from __future__ import annotations

import os
import threading
from uuid import uuid4
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class CircuitState:
    consecutive_failures: int = 0
    opened_until: float = 0.0


class ControlPlane(Protocol):
    name: str
    def consume_budget(self, scope: str, provider_id: str, now: float, limit: int) -> bool: ...
    def circuit(self, scope: str, provider_id: str, now: float) -> CircuitState: ...
    def success(self, scope: str, provider_id: str) -> None: ...
    def failure(self, scope: str, provider_id: str, now: float, threshold: int, cooldown: float) -> CircuitState: ...
    def reset(self) -> None: ...


class MemoryControlPlane:
    name = "memory"

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._budgets: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._circuits: dict[tuple[str, str], CircuitState] = defaultdict(CircuitState)

    def consume_budget(self, scope: str, provider_id: str, now: float, limit: int) -> bool:
        if limit == 0:
            return False
        with self._lock:
            q = self._budgets[(scope, provider_id)]
            cutoff = now - 60.0
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True

    def circuit(self, scope: str, provider_id: str, now: float) -> CircuitState:
        with self._lock:
            state = self._circuits[(scope, provider_id)]
            if state.opened_until and state.opened_until <= now:
                state.opened_until = 0.0
                state.consecutive_failures = 0
            return CircuitState(state.consecutive_failures, state.opened_until)

    def success(self, scope: str, provider_id: str) -> None:
        with self._lock:
            self._circuits[(scope, provider_id)] = CircuitState()

    def failure(self, scope: str, provider_id: str, now: float, threshold: int, cooldown: float) -> CircuitState:
        with self._lock:
            state = self._circuits[(scope, provider_id)]
            state.consecutive_failures += 1
            if state.consecutive_failures >= threshold:
                state.opened_until = now + cooldown
            return CircuitState(state.consecutive_failures, state.opened_until)

    def reset(self) -> None:
        with self._lock:
            self._budgets.clear()
            self._circuits.clear()


class RedisControlPlane:
    """Distributed provider budget/circuit state using Redis.

    The client is injectable for tests. Production construction uses redis-py only when
    RIVEXIS_PROVIDER_CONTROL_BACKEND=redis, keeping the core API dependency-free by default.
    """

    name = "redis"
    _BUDGET_SCRIPT = """
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

    def __init__(self, client: Any, prefix: str = "rivexis:provider-control") -> None:
        self.client = client
        self.prefix = prefix.rstrip(":")
        self.instance_id = uuid4().hex
        self._seq = 0
        self._seq_lock = threading.Lock()

    @classmethod
    def from_env(cls) -> "RedisControlPlane":
        try:
            import redis  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Redis control backend requested but redis-py is not installed") from exc
        url = os.getenv("REDIS_URL", "").strip()
        if not url:
            raise RuntimeError("Redis control backend requested but REDIS_URL is not configured")
        return cls(redis.Redis.from_url(url, decode_responses=True))

    def _key(self, kind: str, scope: str, provider_id: str) -> str:
        return f"{self.prefix}:{kind}:{scope}:{provider_id}"

    def consume_budget(self, scope: str, provider_id: str, now: float, limit: int) -> bool:
        if limit == 0:
            return False
        with self._seq_lock:
            self._seq += 1
            member = f"{now:.6f}:{self.instance_id}:{self._seq}"
        result = self.client.eval(
            self._BUDGET_SCRIPT,
            1,
            self._key("budget", scope, provider_id),
            now - 60.0,
            now,
            member,
            limit,
        )
        return bool(int(result))

    def circuit(self, scope: str, provider_id: str, now: float) -> CircuitState:
        key = self._key("circuit", scope, provider_id)
        data = self.client.hgetall(key) or {}
        failures = int(data.get("consecutive_failures", 0) or 0)
        opened_until = float(data.get("opened_until", 0) or 0)
        if opened_until and opened_until <= now:
            self.client.delete(key)
            return CircuitState()
        return CircuitState(failures, opened_until)

    def success(self, scope: str, provider_id: str) -> None:
        self.client.delete(self._key("circuit", scope, provider_id))

    def failure(self, scope: str, provider_id: str, now: float, threshold: int, cooldown: float) -> CircuitState:
        key = self._key("circuit", scope, provider_id)
        failures = int(self.client.hincrby(key, "consecutive_failures", 1))
        opened_until = 0.0
        if failures >= threshold:
            opened_until = now + cooldown
            self.client.hset(key, mapping={"opened_until": opened_until})
        self.client.expire(key, max(60, int(cooldown) + 60))
        return CircuitState(failures, opened_until)

    def reset(self) -> None:
        # Production reset is intentionally a no-op: one worker must never flush shared state.
        return None


class PostgresControlPlane:
    """Distributed provider controls using the existing production PostgreSQL database."""

    name = "postgres"

    def __init__(self, prefix: str = "rivexis:provider-control") -> None:
        self.prefix = prefix.rstrip(":")

    @classmethod
    def from_env(cls) -> "PostgresControlPlane":
        return cls()

    def _key(self, scope: str, provider_id: str) -> str:
        return f"{self.prefix}:{scope}:{provider_id}"

    def consume_budget(self, scope: str, provider_id: str, now: float, limit: int) -> bool:
        from rivexis_api.postgres_control import consume_budget

        return consume_budget(self._key(scope, provider_id), now, limit)

    def circuit(self, scope: str, provider_id: str, now: float) -> CircuitState:
        from rivexis_api.postgres_control import read_circuit

        state = read_circuit(scope, provider_id, now)
        return CircuitState(state.consecutive_failures, state.opened_until)

    def success(self, scope: str, provider_id: str) -> None:
        from rivexis_api.postgres_control import record_success

        record_success(scope, provider_id)

    def failure(self, scope: str, provider_id: str, now: float, threshold: int, cooldown: float) -> CircuitState:
        from rivexis_api.postgres_control import record_failure

        state = record_failure(scope, provider_id, now, threshold, cooldown)
        return CircuitState(state.consecutive_failures, state.opened_until)

    def reset(self) -> None:
        # Production reset is intentionally a no-op: one worker must never flush shared state.
        return None
