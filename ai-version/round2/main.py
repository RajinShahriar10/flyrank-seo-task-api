from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Task API", version="1.0")


class TaskCreate(BaseModel):
    title: str = Field(strict=True)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, strict=True)
    done: bool | None = Field(default=None, strict=True)


def seed():
    return [
        {"id": 1, "title": "Write unit tests", "done": False},
        {"id": 2, "title": "Review PR", "done": True},
        {"id": 3, "title": "Deploy API", "done": False},
    ]


tasks = seed()


def error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": message})


@app.exception_handler(RequestValidationError)
async def invalid(request, exc):
    return error(400, "Invalid request body")


@app.get("/")
def root():
    """API metadata."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks(done: bool | None = None, search: str | None = None, limit: int | None = None, offset: int = 0):
    """List tasks with optional filters and pagination."""
    result = [t for t in tasks if done is None or t["done"] is done]
    if search:
        result = [t for t in result if search.lower() in t["title"].lower()]
    result = result[offset:]
    return result[:limit] if limit is not None else result


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Fetch one task."""
    return next((t for t in tasks if t["id"] == task_id), error(404, f"Task {task_id} not found"))


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    """Create a task."""
    title = payload.title.strip()
    if not title:
        return error(400, "Title must not be empty")
    task = {"id": max((t["id"] for t in tasks), default=0) + 1, "title": title, "done": False}
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    """Partially update a task."""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        return error(404, f"Task {task_id} not found")
    fields = payload.model_fields_set
    if not fields:
        return error(400, "Provide at least one field: title or done")
    if "title" in fields:
        title = payload.title.strip() if isinstance(payload.title, str) else ""
        if not title:
            return error(400, "Title must not be empty")
        task["title"] = title
    if "done" in fields:
        if not isinstance(payload.done, bool):
            return error(400, "done must be a boolean")
        task["done"] = payload.done
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task."""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        return error(404, f"Task {task_id} not found")
    tasks.remove(task)
    return Response(status_code=204)


@app.get("/stats")
def stats():
    """Return counts."""
    done = sum(t["done"] for t in tasks)
    return {"total": len(tasks), "done": done, "open": len(tasks) - done}


@app.post("/reset")
def reset():
    """Restore seeded tasks."""
    tasks.clear()
    tasks.extend(seed())
    return {"message": "Demo tasks restored", "count": len(tasks)}
