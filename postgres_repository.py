"""Postgres implementation of the task repository interface.

Public function names, arguments and return shapes match database.py (SQLite)
exactly. main.py never imports this module directly: repository.py selects it.
All user values go through %s placeholders; nothing is glued into SQL text.
"""

import os
from pathlib import Path

import psycopg

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://tasks:tasks@localhost:5432/tasks"
)

SEED_TASKS = [
    (1, "Audit /pricing for broken links", False),
    (2, "Generate sitemap for /blog", True),
    (3, "Check meta titles on /docs", False),
]

INIT_SQL = Path(__file__).resolve().parent / "db" / "init.sql"


def connect() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL)


def init_db() -> None:
    """Apply the single schema file; safe to run on every app start."""
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(INIT_SQL.read_text(encoding="utf-8"))


def row_to_task(row) -> dict:
    """Same JSON shape as the SQLite repository: no timestamps exposed."""
    return {"id": row[0], "title": row[1], "done": bool(row[2])}


def list_tasks(done, search, limit, offset) -> list[dict]:
    clauses: list[str] = []
    params: list = []
    if done is not None:
        clauses.append("done = %s")
        params.append(done)
    if search:
        clauses.append("title ILIKE %s")
        params.append(f"%{search}%")

    sql = "SELECT id, title, done FROM tasks"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY id"
    if limit is None:
        sql += " LIMIT ALL"  # SQLite's LIMIT -1 is an error in Postgres
    else:
        sql += " LIMIT %s"
        params.append(limit)
    sql += " OFFSET %s"
    params.append(offset)

    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(sql, params)
        return [row_to_task(row) for row in cursor.fetchall()]


def get_task(task_id: int) -> dict | None:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
        row = cursor.fetchone()
    return row_to_task(row) if row else None


def create_task(title: str) -> dict:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, FALSE) "
            "RETURNING id, title, done",
            (title,),
        )
        return row_to_task(cursor.fetchone())


def update_task(task_id: int, title: str | None, done: bool | None) -> dict | None:
    columns: list[str] = []
    values: list = []
    if title is not None:
        columns.append("title = %s")
        values.append(title)
    if done is not None:
        columns.append("done = %s")
        values.append(done)
    columns.append("updated_at = CURRENT_TIMESTAMP")
    values.append(task_id)

    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE tasks SET {', '.join(columns)} WHERE id = %s "
            "RETURNING id, title, done",
            values,
        )
        row = cursor.fetchone()
    return row_to_task(row) if row else None


def delete_task(task_id: int) -> bool:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        return cursor.rowcount > 0


def stats() -> dict:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """SELECT COUNT(*) AS total,
                      COUNT(*) FILTER (WHERE done) AS done
               FROM tasks"""
        )
        row = cursor.fetchone()
    total, done = row[0], row[1]
    return {"total": total, "done": done, "open": total - done}


def reset() -> int:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM tasks")
        cursor.executemany(
            "INSERT INTO tasks (id, title, done) VALUES (%s, %s, %s)", SEED_TASKS
        )
        cursor.execute(
            "SELECT setval(pg_get_serial_sequence('tasks', 'id'), "
            "GREATEST((SELECT COALESCE(MAX(id), 1) FROM tasks), 1))"
        )
    return len(SEED_TASKS)
