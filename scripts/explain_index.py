"""Stretch proof: EXPLAIN ANALYZE with and without idx_tasks_done.

Run against the live compose stack:
    set DATABASE_URL=postgresql://tasks:tasks@localhost:5432/tasks
    python scripts/explain_index.py

It needs at least a few hundred rows for the planner to prefer an index, so
the script seeds demo rows first. It restores the index at the end.
"""

import os

import psycopg

URL = os.getenv("DATABASE_URL", "postgresql://tasks:tasks@localhost:5432/tasks")
QUERY = "SELECT id, title, done FROM tasks WHERE done = %s"


def explain(cursor, label):
    cursor.execute("EXPLAIN ANALYZE " + QUERY, (True,))
    print(f"\n--- {label} ---")
    for (line,) in cursor.fetchall():
        print(line)


with psycopg.connect(URL) as connection, connection.cursor() as cursor:
    cursor.execute(
        """INSERT INTO tasks (title, done)
           SELECT 'Seeded row ' || n, n % 2 = 0
           FROM generate_series(1, 1000) AS n
           WHERE NOT EXISTS (SELECT 1 FROM tasks WHERE title LIKE 'Seeded row %')"""
    )
    connection.commit()

    cursor.execute("DROP INDEX IF EXISTS idx_tasks_done")
    explain(cursor, "BEFORE (no index on done)")

    cursor.execute("CREATE INDEX idx_tasks_done ON tasks(done)")
    cursor.execute("ANALYZE tasks")
    explain(cursor, "AFTER (idx_tasks_done)")
