"""Redis-backed analysis cache for ProofStack.

Caches completed analysis results to avoid redundant API calls.
Key format: proofstack:analysis:{username}:{role_level}
TTL: 1 hour (configurable).

Usage:
    cache = AnalysisCache()
    cached = await cache.get("torvalds", "senior")
    if cached:
        return cached
    # ... run analysis ...
    await cache.set("torvalds", "senior", result)
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = "proofstack:analysis"
_DEFAULT_TTL = 3600  # 1 hour


class AnalysisCache:
    """Async Redis cache for analysis results."""

    def __init__(self, ttl: int = _DEFAULT_TTL) -> None:
        self.ttl = ttl
        self._redis: Optional[aioredis.Redis] = None

    async def _get_client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
        return self._redis

    @staticmethod
    def _key(username: str, role_level: str) -> str:
        return f"{_KEY_PREFIX}:{username.lower()}:{role_level}"

    async def get(self, username: str, role_level: str) -> Optional[Dict[str, Any]]:
        """Return cached analysis or None."""
        try:
            client = await self._get_client()
            data = await client.get(self._key(username, role_level))
            if data:
                logger.info("Cache HIT for %s/%s", username, role_level)
                return json.loads(data)
            logger.debug("Cache MISS for %s/%s", username, role_level)
            return None
        except Exception as exc:
            logger.warning("Cache read failed: %s", exc)
            return None

    async def set(
        self, username: str, role_level: str, result: Dict[str, Any]
    ) -> None:
        """Store analysis result with TTL."""
        try:
            client = await self._get_client()
            await client.set(
                self._key(username, role_level),
                json.dumps(result, default=str),
                ex=self.ttl,
            )
            logger.info("Cached result for %s/%s (TTL=%ds)", username, role_level, self.ttl)
        except Exception as exc:
            logger.warning("Cache write failed: %s", exc)

    async def invalidate(self, username: str, role_level: str) -> None:
        """Remove a cached entry."""
        try:
            client = await self._get_client()
            await client.delete(self._key(username, role_level))
        except Exception as exc:
            logger.warning("Cache invalidation failed: %s", exc)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
