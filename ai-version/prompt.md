Build me a small task API in Python with FastAPI for a FlyRank internship assignment. It should manage a to-do list with an in-memory Python list (no database, no files). Each task has an integer id, a title string, and a done boolean. Seed the list with three example tasks when the app starts.

I need these endpoints:
- GET / returns some JSON describing the API
- GET /health returns {"status": "ok"}
- GET /tasks returns all tasks
- GET /tasks/{id} returns one task or a 404 if it doesn't exist
- POST /tasks creates a task from {"title": "..."} and returns it
- PUT /tasks/{id} updates a task
- DELETE /tasks/{id} removes a task and returns no content

Use proper HTTP status codes: 200 for reads and updates, 201 for create, 204 for delete, 404 when an id is missing. Check that title is present and not blank before creating; reject bad input. Add Swagger docs at /docs with short descriptions. Put the code in ai-version/main.py and keep it runnable with uvicorn. Also add a requirements.txt there.
