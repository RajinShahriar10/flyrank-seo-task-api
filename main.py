from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

tasks = [
    {"id": 1, "title": "Audit /pricing for broken links", "done": False},
    {"id": 2, "title": "Generate sitemap for /blog", "done": True},
    {"id": 3, "title": "Check meta titles on /docs", "done": False},
]


class TaskCreate(BaseModel):
    title: str


def bad_request(message: str) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": message})


def not_found(task_id: int) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"},
    )


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
    for task in tasks:
        if task["id"] == task_id:
            return task
    return not_found(task_id)


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
