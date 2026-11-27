from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from database import init_db

app = FastAPI(
    title="Task API",
    description="In-memory CRUD API for SEO audit jobs. Storage is a list in this file: data is lost on restart.",
    version="1.0.0",
)

init_db()


def seed_tasks():
    """Fresh copies of the three demo jobs — also used by POST /reset."""
    return [
        {"id": 1, "title": "Audit /pricing for broken links", "done": False},
        {"id": 2, "title": "Generate sitemap for /blog", "done": True},
        {"id": 3, "title": "Check meta titles on /docs", "done": False},
    ]


tasks = seed_tasks()


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


def find_task(task_id: int):
    return next((task for task in tasks if task["id"] == task_id), None)


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
    result = tasks
    if done is not None:
        result = [task for task in result if task["done"] is done]
    if search:
        needle = search.lower()
        result = [task for task in result if needle in task["title"].lower()]
    result = result[offset:]
    if limit is not None:
        result = result[:limit]
    return result


@app.get("/tasks/{task_id}", tags=["Tasks"], summary="Get one task", responses=ERRORS)
def get_task(task_id: int):
    """Return a task by id, or 404 when the id does not exist."""
    task = find_task(task_id)
    return task if task else not_found(task_id)


@app.post("/tasks", tags=["Tasks"], summary="Create a task", status_code=201, responses=ERRORS)
def create_task(payload: TaskCreate):
    """Create a task with the next free id and `done: false`; returns 201."""
    title = payload.title.strip()
    if not title:
        return bad_request("Title must not be empty")
    task = {
        "id": max((t["id"] for t in tasks), default=0) + 1,
        "title": title,
        "done": False,
    }
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}", tags=["Tasks"], summary="Replace task fields", responses=ERRORS)
def update_task(task_id: int, payload: TaskUpdate):
    """Update the supplied title and/or done fields; at least one is required."""
    task = find_task(task_id)
    if not task:
        return not_found(task_id)
    fields = payload.model_fields_set
    if not fields:
        return bad_request("Provide at least one field: title or done")
    if "title" in fields:
        title = payload.title.strip() if isinstance(payload.title, str) else ""
        if not title:
            return bad_request("Title must not be empty")
        task["title"] = title
    if "done" in fields:
        if not isinstance(payload.done, bool):
            return bad_request("done must be a boolean")
        task["done"] = payload.done
    return task


@app.delete("/tasks/{task_id}", tags=["Tasks"], summary="Delete a task", status_code=204, responses=ERRORS)
def delete_task(task_id: int):
    """Remove a task and return 204 with an empty body, or 404 if unknown."""
    task = find_task(task_id)
    if not task:
        return not_found(task_id)
    tasks.remove(task)
    return Response(status_code=204)


@app.get("/stats", tags=["Extras"], summary="Count tasks")
def stats():
    """Return total, done and open counts computed by the server."""
    done = sum(1 for task in tasks if task["done"])
    return {"total": len(tasks), "done": done, "open": len(tasks) - done}


@app.post("/reset", tags=["Extras"], summary="Restore demo tasks")
def reset():
    """Clear the list and restore the three seeded jobs — handy for demos."""
    tasks.clear()
    tasks.extend(seed_tasks())
    return {"message": "Demo tasks restored", "count": len(tasks)}
