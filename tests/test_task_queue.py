"""
Tests for 24/7 Task Queue, Worker Lifecycle, and User Interruption
"""
import pytest
import asyncio
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.models.task import Task, TaskStep
from backend.app.agent.task_queue import TaskQueue

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.mark.asyncio
async def test_task_queue_interruption_and_cancel():
    db = TestingSessionLocal()
    queue = TaskQueue()

    task = Task(
        title="Long-Running Build Task",
        user_request="Build complex application module",
        status="PLANNING",
        created_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Register in queue cancel events
    queue.cancel_events[task.id] = asyncio.Event()

    # User interrupts and cancels task
    cancelled = queue.cancel_task(task.id, db)
    assert cancelled is True

    # Verify task status is CANCELLED
    db.refresh(task)
    assert task.status == "CANCELLED"
    assert "Interrupted" in (task.result_summary or "")

    db.close()

def test_reconnect_briefing_generation():
    db = TestingSessionLocal()

    task1 = Task(
        title="Database Migration",
        user_request="Migrate tables",
        status="COMPLETED",
        result_summary="All 12 tables created successfully."
    )
    task2 = Task(
        title="Frontend Build",
        user_request="Compile assets",
        status="FAILED",
        error_message="Missing dependency @types/react."
    )
    db.add_all([task1, task2])
    db.commit()

    briefing = TaskQueue.get_reconnect_briefing(db)
    assert "Database Migration" in briefing
    assert "Frontend Build" in briefing
    assert "COMPLETED" in briefing
    assert "FAILED" in briefing

    db.close()
