from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import database

app = FastAPI(
    title="Task API",
    description="CRUD API for SEO audit jobs backed by SQLite. The API contract is identical to the Week 2 in-memory version; only the storage layer changed.",
    version="1.0.0",
)

database.init_db()


class TaskCreate(BaseModel):
    title: str = Field(strict=True, description="Non-empty task title")


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, strict=True, description="Replacement title")
    done: bool | None = Field(default=None, strict=True, description="Completion flag")


ERRORS = {
    400: {"description": "Invalid request body", "content": {"application/json": {"example": {"error": "Title must not be empty"}}}},
    404: {"description": "Task not found", "content": {"application/json": {"example": {"error": "Task 99 not found"}}}},
}


def bad_request(message: str) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": message})


def not_found(task_id: int) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    """Turn FastAPI's default 422 into the API's documented 400 error shape."""
    message = "Invalid request body"
    if exc.errors():
        message = f"Invalid request body: {exc.errors()[0]['msg']}"
    return bad_request(message)


@app.get("/", tags=["Meta"], summary="Describe this API")
def describe_api():
    """Return the API name, version and its main endpoint."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", tags=["Meta"], summary="Health check")
def health():
    """Return 200 while the server is alive — used by uptime monitors."""
    return {"status": "ok"}


@app.get("/tasks", tags=["Tasks"], summary="List, filter and paginate tasks", responses=ERRORS)
def list_tasks(done: bool | None = None, search: str | None = None, limit: int | None = None, offset: int = 0):
    """Return tasks, optionally filtered by `done`, `search`, `limit` and `offset`."""
    if limit is not None and limit < 1:
        return bad_request("limit must be at least 1")
    if offset < 0:
        return bad_request("offset must be 0 or greater")
    return database.list_tasks(done, search, limit, offset)


@app.get("/tasks/{task_id}", tags=["Tasks"], summary="Get one task", responses=ERRORS)
def get_task(task_id: int):
    """Return a task by id, or 404 when the id does not exist."""
    task = database.get_task(task_id)
    return task if task else not_found(task_id)


@app.post("/tasks", tags=["Tasks"], summary="Create a task", status_code=201, responses=ERRORS)
def create_task(payload: TaskCreate):
    """Create a task with the next free id and `done: false`; returns 201."""
    title = payload.title.strip()
    if not title:
        return bad_request("Title must not be empty")
    return database.create_task(title)


@app.put("/tasks/{task_id}", tags=["Tasks"], summary="Replace task fields", responses=ERRORS)
def update_task(task_id: int, payload: TaskUpdate):
    """Update the supplied title and/or done fields; at least one is required."""
    if not database.get_task(task_id):
        return not_found(task_id)
    fields = payload.model_fields_set
    if not fields:
        return bad_request("Provide at least one field: title or done")
    title = None
    done = None
    if "title" in fields:
        title = payload.title.strip() if isinstance(payload.title, str) else ""
        if not title:
            return bad_request("Title must not be empty")
    if "done" in fields:
        if not isinstance(payload.done, bool):
            return bad_request("done must be a boolean")
        done = payload.done
    return database.update_task(task_id, title, done)


@app.delete("/tasks/{task_id}", tags=["Tasks"], summary="Delete a task", status_code=204, responses=ERRORS)
def delete_task(task_id: int):
    """Remove a task and return 204 with an empty body, or 404 if unknown."""
    if not database.delete_task(task_id):
        return not_found(task_id)
    return Response(status_code=204)


@app.get("/stats", tags=["Extras"], summary="Count tasks")
def stats():
    """Return total, done and open counts computed by SQL COUNT()."""
    return database.stats()


@app.post("/reset", tags=["Extras"], summary="Restore demo tasks")
def reset():
    """Delete all rows and restore the three seeded jobs — handy for demos."""
    count = database.reset()
    return {"message": "Demo tasks restored", "count": count}
