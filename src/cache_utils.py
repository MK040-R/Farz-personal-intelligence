"""Shared read-cache helpers for user-scoped API responses."""

from __future__ import annotations

import json
import logging
import os
import ssl
import sys
import threading
from functools import lru_cache
from hashlib import sha256
from time import monotonic
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from src.config import settings

logger = logging.getLogger(__name__)

_VERSION_TTL_SECONDS = 7 * 24 * 60 * 60
_DEFAULT_VERSION = "0"
_memory_cache_lock = threading.Lock()
_memory_cache: dict[str, tuple[float, Any]] = {}
_memory_versions: dict[str, int] = {}


def cache_enabled() -> bool:
    """Return True when external caching should be used for the current process."""
    if os.environ.get("PYTEST_CURRENT_TEST") or "pytest" in sys.modules:
        return False
    return True


def _redis_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "decode_responses": True,
        "socket_connect_timeout": 0.5,
        "socket_timeout": 0.5,
    }
    if settings.UPSTASH_REDIS_URL.startswith("rediss://"):
        kwargs["ssl_cert_reqs"] = ssl.CERT_REQUIRED
    return kwargs


@lru_cache(maxsize=1)
def _get_cache_client() -> Redis[Any]:
    return Redis.from_url(settings.UPSTASH_REDIS_URL, **_redis_kwargs())


def _version_key(user_id: str) -> str:
    return f"user:{user_id}:read_cache_version"


def _memory_get(key: str) -> Any | None:
    now = monotonic()
    with _memory_cache_lock:
        entry = _memory_cache.get(key)
        if entry is None:
            return None
        expires_at, payload = entry
        if expires_at <= now:
            _memory_cache.pop(key, None)
            return None
        return payload


def _memory_set(key: str, payload: Any, ttl_seconds: int) -> None:
    expires_at = monotonic() + ttl_seconds
    with _memory_cache_lock:
        _memory_cache[key] = (expires_at, payload)


def _memory_get_version(user_id: str) -> str:
    with _memory_cache_lock:
        version = _memory_versions.get(user_id, 0)
    return str(version)


def get_user_cache_version(user_id: str) -> str:
    """Return the current per-user cache version."""
    if not cache_enabled():
        return _DEFAULT_VERSION

    try:
        value = _get_cache_client().get(_version_key(user_id))
    except (RedisError, OSError) as exc:
        logger.warning("Cache version lookup failed for user=%s: %s", user_id, type(exc).__name__)
        return _memory_get_version(user_id)

    return value if isinstance(value, str) and value else _DEFAULT_VERSION


def bump_user_cache_version(user_id: str) -> None:
    """Invalidate all cached read responses for a user."""
    if not cache_enabled():
        return

    with _memory_cache_lock:
        _memory_versions[user_id] = _memory_versions.get(user_id, 0) + 1

    try:
        client = _get_cache_client()
        client.incr(_version_key(user_id))
        client.expire(_version_key(user_id), _VERSION_TTL_SECONDS)
    except (RedisError, OSError) as exc:
        logger.warning("Cache version bump failed for user=%s: %s", user_id, type(exc).__name__)


def _cache_suffix(identity: Any) -> str:
    serialized = json.dumps(identity, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(serialized.encode("utf-8")).hexdigest()


def build_user_cache_key(user_id: str, namespace: str, identity: Any) -> str:
    """Build a user-scoped read-cache key using the current cache version."""
    version = get_user_cache_version(user_id)
    return f"user:{user_id}:read_cache:v{version}:{namespace}:{_cache_suffix(identity)}"


def get_cached_json(key: str) -> Any | None:
    """Return cached JSON-like payload or None on miss/failure."""
    if not cache_enabled():
        return None

    try:
        raw = _get_cache_client().get(key)
    except (RedisError, OSError) as exc:
        logger.warning("Cache read failed for key=%s: %s", key, type(exc).__name__)
        return _memory_get(key)

    if not isinstance(raw, str) or not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Cache payload decode failed for key=%s", key)
        return None


def set_cached_json(key: str, payload: Any, ttl_seconds: int) -> None:
    """Store a JSON-serializable payload in cache."""
    if not cache_enabled():
        return

    _memory_set(key, payload, ttl_seconds)

    try:
        serialized = json.dumps(payload, sort_keys=True, default=str)
        _get_cache_client().setex(key, ttl_seconds, serialized)
    except (RedisError, OSError, TypeError, ValueError) as exc:
        logger.warning("Cache write failed for key=%s: %s", key, type(exc).__name__)
