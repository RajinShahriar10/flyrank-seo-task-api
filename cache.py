"""Optional Redis check for the stretch goal — no route depends on it."""

import os


def ping_redis() -> str | None:
    """Return 'pong' when REDIS_URL is reachable, None when absent/unavailable."""
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        import redis

        redis.Redis.from_url(url, socket_connect_timeout=3).ping()
        print("[cache] Redis ping: pong")
        return "pong"
    except Exception as exc:  # a dead cache must never stop the API
        print(f"[cache] Redis ping failed (non-fatal): {exc}")
        return None
