"""Give the test session its own database so tests never touch tasks.db."""

import os
import tempfile

os.environ["TASKS_DB_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="flyrank_w3_"), "tasks.db"
)
