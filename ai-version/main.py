from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="Task API", version="1.0")


class Task(BaseModel):
    id: int
    title: str
    done: bool = False


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool


tasks: list[Task] = [
    Task(id=1, title="Write unit tests", done=False),
    Task(id=2, title="Review PR", done=True),
    Task(id=3, title="Deploy API", done=False),
]


@app.get("/")
def root():
    """API details."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}


@app.get("/tasks")
def get_tasks():
    """Get all tasks."""
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Get a task by id."""
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    """Create a new task."""
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    task = Task(id=len(tasks) + 1, title=payload.title.strip(), done=False)
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    """Update a task."""
    for task in tasks:
        if task.id == task_id:
            task.title = payload.title
            task.done = payload.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    """Delete a task."""
    for index, task in enumerate(tasks):
        if task.id == task_id:
            tasks.pop(index)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
