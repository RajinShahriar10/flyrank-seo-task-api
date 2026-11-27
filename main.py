from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI()

tasks = [
    {"id": 1, "title": "Audit /pricing for broken links", "done": False},
    {"id": 2, "title": "Generate sitemap for /blog", "done": True},
    {"id": 3, "title": "Check meta titles on /docs", "done": False},
]


class TaskCreate(BaseModel):
    title: str = Field(strict=True)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, strict=True)
    done: bool | None = Field(default=None, strict=True)


def bad_request(message: str) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": message})


def not_found(task_id: int) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"},
    )


def find_task(task_id: int):
    return next((task for task in tasks if task["id"] == task_id), None)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    message = "Invalid request body"
    if exc.errors():
        message = f"Invalid request body: {exc.errors()[0]['msg']}"
    return bad_request(message)


@app.get("/")
def describe_api():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = find_task(task_id)
    return task if task else not_found(task_id)


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
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


@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
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


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    task = find_task(task_id)
    if not task:
        return not_found(task_id)
    tasks.remove(task)
    return Response(status_code=204)
