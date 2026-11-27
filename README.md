# SEO Audit Task Queue — Postgres in Docker

**FlyRank Backend AI Engineering · A3 (BE-04)** — the A2 task API with its storage swapped once more: SQLite file → Postgres container. The routes, validation and JSON contract are the ones from A1/A2; only the repository underneath changed.

```
A1: Client → FastAPI → Python list        (dies on restart)
A2: Client → FastAPI → SQLite tasks.db    (survives process restart)
A3: Client → FastAPI → Postgres in Docker (survives app + container restart)
```

## The architecture claim, honestly

`main.py` contains **no storage code and no SQL**. In A2 it did `import database`; now it does `from repository import database`. That is the only functional line that changed — plus the Swagger description string. Every route body is byte-for-byte the A2 version.

`repository.py` is the single wiring point:

```python
if os.getenv("STORAGE_BACKEND", "sqlite").lower() == "postgres":
    import postgres_repository as database
else:
    import database
```

`postgres_repository.py` implements the **same public functions** as the SQLite `database.py`, so the routes keep calling `database.list_tasks(...)`, `database.create_task(...)`, etc.:

| Interface | SQLite (A2) | Postgres (A3) |
| --- | --- | --- |
| `init_db()` | `CREATE TABLE IF NOT EXISTS` | executes `db/init.sql` |
| `list_tasks(done, search, limit, offset)` | `WHERE`, `LIKE`, `LIMIT/OFFSET` | `WHERE`, `ILIKE`, `LIMIT/OFFSET` |
| `get_task(id)` | `SELECT ... WHERE id = ?` | `SELECT ... WHERE id = %s` |
| `create_task(title)` | `INSERT` + `lastrowid` | `INSERT ... RETURNING` |
| `update_task(id, title, done)` | dynamic partial `UPDATE` | same, with `RETURNING` |
| `delete_task(id)` | rowcount | rowcount |
| `stats()` / `reset()` | `COUNT` / reseed | `COUNT FILTER` / reseed + `setval` |

All user-supplied values go through `?` (SQLite) or `%s` (Postgres) placeholders. Nothing is string-glued into a query.

## Files added for A3

| File | Purpose |
| --- | --- |
| `postgres_repository.py` | Postgres implementation of the A2 repository interface |
| `repository.py` | Picks SQLite or Postgres from `STORAGE_BACKEND` |
| `db/init.sql` | The one schema file: table, two indexes, first-run seeds, sequence fix |
| `.env.example` | Committed template; real `.env` is gitignored |
| `Dockerfile` | App image (`python:3.12-slim`) |
| `docker-compose.yml` | `db` (Postgres + named volume), `app`, optional `cache` (Redis) |
| `cache.py` | Optional Redis `PING` at startup; never fatal |
| `scripts/explain_index.py` | Stretch: `EXPLAIN ANALYZE` before/after an index |
| `pytest.ini` | Keeps tests scoped to the root `tests/` folder |

## Run the whole stack

Docker Desktop is required (see [install steps](#install-docker-if-not-present)). Then, from this folder:

```cmd
copy .env.example .env
docker compose up --build -d
```

Open http://localhost:8000/docs. The Postgres service is healthy-checked with `pg_isready`, and the app waits for it before starting. `STORAGE_BACKEND=postgres` and `DATABASE_URL` come from `.env`; the hostname `db` is the compose service name.

### Environment

`.env` is **gitignored**; `.env.example` is committed. Values:

| Key | Example | Used by |
| --- | --- | --- |
| `STORAGE_BACKEND` | `postgres` | `repository.py` swap |
| `DATABASE_URL` | `postgresql://tasks:tasks@db:5432/tasks` | app → Postgres |
| `POSTGRES_USER/PASSWORD/DB` | `tasks` / `tasks` / `tasks` | compose substitutes into the db container |
| `REDIS_URL` | `redis://cache:6379/0` | optional stretch ping |

For a non-Docker local run against a published port, override in the shell:
`set DATABASE_URL=postgresql://tasks:tasks@localhost:5432/tasks`

## Persistence proof (app restart **and** container restart)

Run these from the repo root after `docker compose up -d`:

```cmd
curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d "{\"title\":\"Survives both restarts\"}"
docker compose restart app
curl -i http://localhost:8000/tasks
docker compose down
docker compose up -d
curl -i http://localhost:8000/tasks
docker compose exec db psql -U tasks -d tasks -c "SELECT id, title, done FROM tasks ORDER BY id;"
```

The created row must appear in all three `GET /tasks` calls and in the `psql` output. `docker compose down` **keeps** the named volume `pgdata`; `docker compose down -v` deliberately deletes it and the next `up` re-seeds the three example jobs.

> Results of this run will be pasted here once Docker Desktop is installed in the working environment. The API-side assertion is already automated locally in `tests/test_api.py` (9 tests pass with the SQLite repository); the container restart check needs the live stack.

## Database viewer / SQL

```cmd
docker compose exec db psql -U tasks -d tasks -c "SELECT * FROM tasks;"
docker compose exec db psql -U tasks -d tasks -c "SELECT COUNT(*) FROM tasks;"
```

`db/init.sql` is mounted at `/docker-entrypoint-initdb.d/init.sql`, so a fresh volume creates the table, indexes and three seeds automatically. The app also executes the same file at startup, which makes a partially initialized volume self-heal. Seeds are guarded by `WHERE NOT EXISTS (SELECT 1 FROM tasks)` and the identity sequence is set to `MAX(id)`, so example tasks never multiply and new ids never collide.

## Stretch goals

- **Redis:** compose starts `cache` (`redis:7-alpine`) with a healthcheck. When `REDIS_URL` is set, `cache.py` sends `PING` once at startup and logs `pong`. A missing Redis logs a warning but never blocks the API, so it stays optional.
- **Index proof:** `scripts/explain_index.py` seeds 1,000 rows, drops `idx_tasks_done`, runs `EXPLAIN ANALYZE`, recreates the index, and runs it again. Run it after the stack is up:
  `set DATABASE_URL=postgresql://tasks:tasks@localhost:5432/tasks && python scripts/explain_index.py`

## Tests

```cmd
python -m pytest -q
```

9 tests cover the unchanged A1/A2 contract plus persistence and seeding, using an isolated SQLite file. `tests/conftest.py` forces `STORAGE_BACKEND=sqlite` so a developer's `.env` cannot make unit tests need a running Postgres.

## Install Docker (if not present)

1. Install WSL2 in an **elevated** PowerShell: `wsl --install`
2. Reboot when prompted.
3. Install Docker Desktop: `winget install --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements`
4. Start Docker Desktop, accept the license, and confirm `docker --version` and `docker compose version` work.

## Commit trail

Previous history: A1 `hello server` → `Stage 7: AI vs me`, then A2 `Stage 0: create SQLite database` → `Extras: SQL indexes and migration notes`. A3 commits: Postgres repository and schema, Docker/compose wiring, documentation and verification. The old in-memory and SQLite snapshots are kept in archived sibling folders locally and are gitignored.
