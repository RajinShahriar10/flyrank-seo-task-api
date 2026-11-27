Same API as before, but obey these exact rules:

- All client errors return `400` with body `{"error": "..."}`. Override FastAPI's default `422` from `RequestValidationError`; never emit `{"detail": ...}`. A missing id returns `404` with the same `{"error": "Task 99 not found"}` shape.
- `POST /tasks` accepts only `{"title": "<non-empty string>"}`; reject missing, blank, whitespace-only and non-string titles with `400`. Store the stripped title, set `done: false` and return `201` with the created task.
- `PUT /tasks/{id}` is a PARTIAL update: accept `title` and/or `done`, require at least one field, validate the same way, return `200`, and return `400` for an empty `{}` body. Unknown id is `404`.
- Allocate ids with `max(existing ids) + 1` so deleting a task can never cause an id to be reused.
- `GET /` returns exactly `{"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}`.
- Also add `GET /tasks?done=true&search=<text>&limit=<n>&offset=<n>` filtering/pagination, `GET /stats`, and `POST /reset` that restores the original three seeded jobs.
- Give every route a short Swagger description; run the app with `uvicorn main:app` from the round2 folder.
