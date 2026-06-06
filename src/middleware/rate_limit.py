"""Redis-based rate limiting middleware.

When REDIS_URL is not set, the middleware is a no-op (no Redis required in dev).

Rate limits (per route group, per IP):
  - auth:login / auth:register / auth:refresh  → 10 req / 60s
  - leads (POST /leads)                        → 5 req / 60s
  - search (GET /properties)                   → 60 req / 60s
  - image upload                               → 20 req / 60s
  - metrics events                             → 120 req / 60s
  - default (any other)                        → 100 req / 60s

On limit exceeded: 429 Too Many Requests + Retry-After header.
"""
from __future__ import annotations

import os
import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

_REDIS_URL = os.getenv("REDIS_URL", "")

# (path_prefix, method) → (max_requests, window_seconds)
_LIMITS: list[tuple[str, str | None, int, int]] = [
    ("/api/v1/auth/login",    "POST", 10,  60),
    ("/api/v1/auth/register", "POST", 10,  60),
    ("/api/v1/auth/refresh",  "POST", 10,  60),
    ("/api/v1/leads",         "POST",  5,  60),
    ("/api/v1/properties",    "GET",  60,  60),
    ("/images",               "POST", 20,  60),
    ("/api/v1/metrics",       "POST", 120, 60),
]
_DEFAULT_LIMIT = (100, 60)


def _get_limit(path: str, method: str) -> tuple[int, int]:
    for prefix, m, limit, window in _LIMITS:
        if path.startswith(prefix) and (m is None or method == m):
            return limit, window
    return _DEFAULT_LIMIT


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter backed by Redis.

    If Redis is unavailable, all requests pass through.
    """

    def __init__(self, app, redis_url: str = _REDIS_URL) -> None:
        super().__init__(app)
        self._redis = None
        if redis_url:
            try:
                import redis as _redis  # type: ignore
                self._redis = _redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None  # fall back to no-op

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._redis is None:
            return await call_next(request)

        path = request.url.path
        method = request.method
        limit, window = _get_limit(path, method)
        ip = _client_ip(request)
        key = f"rl:{method}:{path}:{ip}"

        now = int(time.time())
        window_start = now - window

        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window)
        results = pipe.execute()
        count = results[2]

        if count > limit:
            retry_after = window
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests", "details": None}},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
