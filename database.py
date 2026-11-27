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


def row_to_task(row: sqlite3.Row) -> dict:
    """Convert a database row into the exact JSON shape the API promised."""
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


def list_tasks(done: bool | None, search: str | None, limit: int | None, offset: int) -> list[dict]:
    """SELECT tasks, filtering in SQL rather than in Python."""
    sql = "SELECT id, title, done FROM tasks"
    clauses: list[str] = []
    params: list = []
    if done is not None:
        clauses.append("done = ?")
        params.append(int(done))
    if search:
        clauses.append("title LIKE ?")
        params.append(f"%{search}%")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY id LIMIT ? OFFSET ?"
    params.extend([limit if limit is not None else -1, offset])
    with closing(connect()) as connection, connection:
        return [row_to_task(row) for row in connection.execute(sql, params).fetchall()]


def get_task(task_id: int) -> dict | None:
    """SELECT one task, or return None when the id does not exist."""
    with closing(connect()) as connection, connection:
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return row_to_task(row) if row else None


def create_task(title: str) -> dict:
    """INSERT a new row and return it. SQLite assigns the next free id."""
    with closing(connect()) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, done) VALUES (?, 0)", (title,)
        )
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return row_to_task(row)
