import sqlite3

from fastapi.testclient import TestClient

import database
from main import app

client = TestClient(app)


def reset():
    assert client.post("/reset").status_code == 200


def test_root_and_health():
    assert client.get("/").json() == {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }
    assert client.get("/health").json() == {"status": "ok"}


def test_read_endpoints_and_404():
    reset()
    assert len(client.get("/tasks").json()) == 3
    assert client.get("/tasks/1").json()["title"] == "Audit /pricing for broken links"
    missing = client.get("/tasks/99")
    assert missing.status_code == 404
    assert missing.json() == {"error": "Task 99 not found"}


def test_create_validation():
    reset()
    created = client.post("/tasks", json={"title": "  Buy milk  "})
    assert created.status_code == 201
    assert created.json() == {"id": 4, "title": "Buy milk", "done": False}
    for body in ({}, {"title": ""}, {"title": 123}):
        bad = client.post("/tasks", json=body)
        assert bad.status_code == 400
        assert "error" in bad.json()


def test_full_crud_cycle():
    reset()
    created = client.post("/tasks", json={"title": "Ship SEO report"}).json()
    task_id = created["id"]
    updated = client.put(f"/tasks/{task_id}", json={"title": "Ship report", "done": True})
    assert updated.status_code == 200
    assert updated.json() == {"id": task_id, "title": "Ship report", "done": True}
    deleted = client.delete(f"/tasks/{task_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/tasks/{task_id}").status_code == 404
    assert client.delete(f"/tasks/{task_id}").status_code == 404


def test_update_validation():
    reset()
    empty = client.put("/tasks/1", json={})
    assert empty.status_code == 400
    assert "error" in empty.json()
    unknown = client.put("/tasks/99", json={"done": True})
    assert unknown.status_code == 404


def test_extras():
    reset()
    assert [t["id"] for t in client.get("/tasks", params={"done": "true"}).json()] == [2]
    assert [t["id"] for t in client.get("/tasks", params={"search": "meta"}).json()] == [3]
    assert [t["id"] for t in client.get("/tasks", params={"limit": 2, "offset": 1}).json()] == [2, 3]
    assert client.get("/stats").json() == {"total": 3, "done": 1, "open": 2}
    assert client.get("/tasks", params={"limit": 0}).status_code == 400


def test_data_survives_restart():
    """Re-running init_db() is what a server restart does; rows must remain."""
    reset()
    created = client.post("/tasks", json={"title": "Survives restart"}).json()
    database.init_db()
    assert client.get(f"/tasks/{created['id']}").json() == created
    with sqlite3.connect(database.DB_PATH) as connection:
        assert connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 4


def test_seeding_happens_only_once():
    reset()
    database.init_db()
    database.init_db()
    assert len(client.get("/tasks").json()) == 3


def test_external_sql_write_is_visible_to_api():
    """Stage 4: a committed write from a SQLite viewer shows up through the API."""
    reset()
    with sqlite3.connect(database.DB_PATH) as connection:
        connection.execute("UPDATE tasks SET done = 1 WHERE id = 1")
        connection.commit()
    assert client.get("/tasks/1").json()["done"] is True
    assert client.get("/stats").json() == {"total": 3, "done": 2, "open": 1}
