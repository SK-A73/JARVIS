"""
Tests for Failure Parsing, Rectifier, and Coding Agent Loop
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.models.task import Task, TaskStep
from backend.app.agent.rectifier import Rectifier, FailureAnalysis
from backend.app.agent.coding_agent import CodingAgent
from backend.app.llm.mock_provider import MockLLMProvider

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

def test_rectifier_traceback_parsing():
    sample_traceback = """
Traceback (most recent call last):
  File "backend/services/order.py", line 42, in process_order
    total = calculate_discount(price, rate)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
NameError: name 'calculate_discount' is not defined
    """
    analysis = Rectifier.parse_traceback(sample_traceback)
    assert analysis.error_type == "NameError"
    assert "order.py" in (analysis.failing_file or "")
    assert analysis.line_number == 42
    assert "calculate_discount" in analysis.root_cause
    assert "Import or define" in analysis.suggested_fix

def test_rectifier_assertion_parsing():
    assertion_log = "FAILED tests/test_payment.py::test_stripe_charge - AssertionError: assert 400 == 200"
    analysis = Rectifier.parse_traceback(assertion_log)
    assert analysis.error_type == "AssertionError"
    assert "Assertion failed" in analysis.root_cause

@pytest.mark.asyncio
async def test_coding_agent_successful_lifecycle():
    db = TestingSessionLocal()
    llm = MockLLMProvider()

    task = Task(
        title="Implement Calculator Module",
        user_request="Build a basic math utility and test it.",
        mode="AUTONOMOUS",
        status="QUEUED"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    agent = CodingAgent(db, llm, task)
    # We pass a simple command that succeeds
    result = await agent.run_development_cycle(
        test_command="python -c \"print('All 15 tests passed')\"",
        max_rectification_attempts=3
    )

    assert result["status"] == "COMPLETED"
    assert result["attempts"] == 0
    assert "All tests passed" in result["summary"]

    # Verify steps recorded in DB
    steps = db.query(TaskStep).filter(TaskStep.task_id == task.id).all()
    assert len(steps) >= 3

    db.close()
