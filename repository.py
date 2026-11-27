"""The one wiring point that swaps storage without touching a route.

Tests and local SQLite runs get `database.py`. With STORAGE_BACKEND=postgres
(and a DATABASE_URL from .env), the identical function names are supplied by
`postgres_repository.py`. main.py aliases whichever module is chosen to the
name `database`, so every route body stays exactly as it was in A2.
"""

import os

from dotenv import load_dotenv

# Does not overwrite variables already supplied by compose or the shell.
load_dotenv()

if os.getenv("STORAGE_BACKEND", "sqlite").lower() == "postgres":
    import postgres_repository as database
else:
    import database

# Optional stretch: ping Redis once at startup. Never fatal if Redis is absent.
if os.getenv("REDIS_URL"):
    from cache import ping_redis

    ping_redis()
