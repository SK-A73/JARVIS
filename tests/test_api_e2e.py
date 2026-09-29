"""
End-to-End API Integration and WebSocket Verification
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database import Base, get_db

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

def test_health_check_endpoint():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "JARVIS" in data["service"]

def test_full_user_and_task_e2e_flow():
    client = TestClient(app)

    # 1. Register
    reg_resp = client.post("/api/v1/auth/register", json={
        "username": "tony_e2e",
        "password": "StarkPassword2026!"
    })
    assert reg_resp.status_code == 200
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Add Memory
    mem_resp = client.post("/api/v1/memory", json={
        "content": "Project uses FastAPI backend and Kotlin Compose Android client",
        "category": "project",
        "importance": 8.0
    }, headers=headers)
    assert mem_resp.status_code == 200
    assert "FastAPI" in mem_resp.json()["content"]

    # 3. Create Task
    task_resp = client.post("/api/v1/tasks", json={
        "title": "Verify Backend Architecture",
        "user_request": "Run unit tests and verify database connectivity",
        "priority": 8
    }, headers=headers)
    assert task_resp.status_code == 200
    task_data = task_resp.json()
    assert task_data["title"] == "Verify Backend Architecture"
    assert task_data["status"] == "QUEUED"

    # 4. List Tasks
    list_tasks = client.get("/api/v1/tasks", headers=headers)
    assert list_tasks.status_code == 200
    assert len(list_tasks.json()) == 1

def test_websocket_client_interaction():
    client = TestClient(app)
    with client.websocket_connect("/ws/client/phone-client-1") as websocket:
        # Receive initial status
        initial_status = websocket.receive_json()
        assert initial_status["type"] == "jarvis_status"
        assert initial_status["state"] == "online"

        # Send conversational message
        websocket.send_json({"message": "Hello JARVIS, are you ready?"})

        # Receive stream start
        start_msg = websocket.receive_json()
        assert start_msg["type"] == "stream_start"

        # Receive stream chunks
        chunks = []
        while True:
            msg = websocket.receive_json()
            if msg["type"] == "stream_chunk":
                chunks.append(msg["chunk"])
            elif msg["type"] == "stream_end":
                break

        full_reply = "".join(chunks)
        assert len(full_reply) > 0
        assert "JARVIS" in full_reply
