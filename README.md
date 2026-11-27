# SEO Audit Task Queue — Task API

A hand-built CRUD API for **FlyRank Backend AI Engineering · BE-01 (W2/A1)**.

Each "task" is an SEO audit job: `{"id": 1, "title": "Audit /pricing for broken links", "done": false}`. The endpoint contract is exactly the one the assignment specifies (`/tasks`), but the domain is the one FlyRank actually works in — a queue of report-generation jobs. Same code shape as a social network's posts or a shop's orders.

Built with **FastAPI** so validation, JSON serialization and interactive **Swagger UI** come from the framework, while the storage stays deliberately boring: a Python list in `main.py`. No database, no file writes.

## Run it

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open **http://localhost:8000/docs** for Swagger UI, or **http://localhost:8000/** for API metadata.

Run the checks with `python -m pytest -q` (6 tests).

## Endpoints

| Method | Path | What it does | Success | Errors |
| --- | --- | --- | --- | --- |
| `GET` | `/` | API name, version, main endpoint | `200` | — |
| `GET` | `/health` | Liveness probe for uptime monitors | `200` | — |
| `GET` | `/tasks` | List tasks; filter with `?done=true`, `?search=meta`, paginate with `?limit=2&offset=1` | `200` | `400` |
| `GET` | `/tasks/{id}` | Fetch one task | `200` | `404` |
| `POST` | `/tasks` | Create with `{"title": "..."}`; assigns next id and `done: false` | `201` | `400` |
| `PUT` | `/tasks/{id}` | Replace `title` and/or `done` (at least one required) | `200` | `400`, `404` |
| `DELETE` | `/tasks/{id}` | Remove a task, empty body | `204` | `404` |
| `GET` | `/stats` | Server-computed `total` / `done` / `open` counts | `200` | — |
| `POST` | `/reset` | Restore the three seeded demo jobs | `200` | — |

Every error is JSON: `{"error": "Task 99 not found"}` — never an empty `200` or FastAPI's default `422`. Invalid bodies are normalized to `400` by the `RequestValidationError` handler.

### A real response, via curl

```console
$ curl -i -X POST http://localhost:8000/tasks \
    -H "Content-Type: application/json" \
    -d '{"title":"Crawl /blog for orphan pages"}'

HTTP/1.1 201 Created
date: Fri, 27 Nov 2026 03:53:19 GMT
server: uvicorn
content-length: 60
content-type: application/json

{"id":5,"title":"Crawl /blog for orphan pages","done":false}
```

The full cycle — create (`201`), update (`200`), delete (`204`), unknown id (`404`), bad body (`400`) — is covered in `tests/test_api.py` and works through "Try it out" in Swagger UI too.

## Swagger UI

![Swagger UI showing all Task API endpoints](docs/swagger.png)

OpenAPI JSON (generated from the route signatures and docstrings) is served at `/openapi.json`.

## The mortality experiment

I created a task, stopped the server with `Ctrl+C`, restarted it, and called `GET /tasks`: my new task was gone and the list was back to the three seeded jobs. That happens because the "database" is a list inside the running Python process — when the process dies, its memory dies with it. This is exactly the problem a real database solves in Week 3.

## Why this is on my CV

- **CRUD contract, not a toy:** nine documented endpoints with honest status codes and a consistent JSON error shape.
- **Input is untrusted:** strict Pydantic types, empty-title rejection, a custom `422 → 400` handler, and optional-field checks on `PUT`.
- **Query design:** filtering, case-insensitive search and offset/limit pagination, plus a server-computed `/stats` endpoint. Real APIs don't return "everything".
- **Self-describing API:** generated OpenAPI, Swagger UI, and six pytest tests that run in under a second.
- **AI engineering, not just AI usage:** the "AI vs me" section below records a written specification, a competing implementation and a diff — the review loop matters more than the generated code.

## Commit trail

One commit per stage, in order: `Stage 0: hello server` → `Stage 1: root and health endpoints` → `Stage 2: read endpoints with 404` → `Stage 3: create with validation` → `Stage 4: full CRUD` → `Stage 5: Swagger UI` → `Extras: ...` → `Stage 6: publish and docs` → `Stage 7: AI vs me`.
