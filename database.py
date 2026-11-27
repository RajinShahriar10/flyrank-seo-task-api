"""SQLite storage layer for the Task API.

The API layer in main.py calls these functions; it never writes SQL itself.
Set TASKS_DB_PATH to point at a different database file (used by the tests).
"""

import os
import sqlite3
from contextlib import closing

DB_PATH = os.getenv("TASKS_DB_PATH", "tasks.db")

SEED_TASKS = [
    (1, "Audit /pricing for broken links", 0),
    (2, "Generate sitemap for /blog", 1),
    (3, "Check meta titles on /docs", 0),
]


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Create the schema if needed and seed three tasks only on the first run."""
    with closing(connect()) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                done INTEGER NOT NULL CHECK (done IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            connection.executemany(
                "INSERT INTO tasks (id, title, done) VALUES (?, ?, ?)",
                SEED_TASKS,
            )
