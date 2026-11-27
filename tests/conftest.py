"""Give the test session its own database so tests never touch tasks.db."""

import os
import tempfile

# These tests exercise the A1/A2 contract with the SQLite repository. Force it
# even if a developer has a .env with Postgres settings in the repo root.
os.environ["STORAGE_BACKEND"] = "sqlite"
os.environ.pop("DATABASE_URL", None)
os.environ.pop("REDIS_URL", None)

os.environ["TASKS_DB_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="flyrank_w3_"), "tasks.db"
)
