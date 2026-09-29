"""
Tests for Emotion Engine, Adaptive Learning, Decision Engine, and Operating Modes
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.core.emotion import EmotionEngine
from backend.app.core.learning import LearningEngine
from backend.app.core.decision import DecisionEngine
from backend.app.agent.modes import OperatingMode, ModePolicy

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

def test_probabilistic_emotion_inference():
    urgent = EmotionEngine.infer_emotion("JARVIS, check the server right now! It's critical!")
    assert urgent.state == "Urgent"
    assert urgent.brevity_level == "concise"

    frustrated = EmotionEngine.infer_emotion("Why is this failing again? This is broken and annoying.")
    assert frustrated.state == "Frustrated"
    assert "frustrated" in (urgent.empathetic_phrase or "").lower() or "frustrated" in (frustrated.empathetic_phrase or "").lower()

    confused = EmotionEngine.infer_emotion("I don't understand how this build system works, explain it.")
    assert confused.state == "Confused"
    assert confused.brevity_level == "detailed"

    calm = EmotionEngine.infer_emotion("Please summarize the project status.")
    assert calm.state == "Calm"

def test_adaptive_learning_from_feedback():
    db = TestingSessionLocal()
    learning = LearningEngine(db)

    pattern = learning.analyze_and_learn_from_feedback("Don't use tabs, always use 4 spaces for indentation")
    assert pattern is not None
    assert "4 spaces" in pattern.description
    assert pattern.is_active is True

    # Retrieve active patterns
    active = learning.get_active_patterns()
    assert len(active) == 1
    assert active[0].id == pattern.id

    # Deactivate / forget pattern
    learning.deactivate_pattern(pattern.id)
    active_after = learning.get_active_patterns()
    assert len(active_after) == 0

    db.close()

def test_operating_mode_tool_permissions():
    # PLAN mode should reject write_file and execute_terminal_command
    verdict_plan_write = DecisionEngine.evaluate_tool_execution(
        tool_name="write_file",
        tool_args={"file_path": "test.py", "content": "x = 1"},
        mode=OperatingMode.PLAN
    )
    assert verdict_plan_write.is_allowed is False
    assert "not permitted in PLAN mode" in verdict_plan_write.reason

    # PLAN mode allows read_file
    verdict_plan_read = DecisionEngine.evaluate_tool_execution(
        tool_name="read_file",
        tool_args={"file_path": "README.md"},
        mode=OperatingMode.PLAN
    )
    assert verdict_plan_read.is_allowed is True

    # TEST mode allows execute_terminal_command (to run tests) but rejects write_file
    verdict_test_write = DecisionEngine.evaluate_tool_execution(
        tool_name="write_file",
        tool_args={"file_path": "src/main.py"},
        mode=OperatingMode.TEST
    )
    assert verdict_test_write.is_allowed is False

def test_decision_engine_dangerous_commands_guard():
    dangerous_cmd = "rm -rf /"
    verdict = DecisionEngine.evaluate_tool_execution(
        tool_name="execute_terminal_command",
        tool_args={"command": dangerous_cmd},
        mode=OperatingMode.AUTONOMOUS
    )
    assert verdict.is_allowed is False
    assert verdict.requires_user_confirmation is True
    assert "destructive" in verdict.reason.lower()

    # Normal command should be allowed in AUTONOMOUS mode
    normal_cmd = "pytest tests/ -v"
    normal_verdict = DecisionEngine.evaluate_tool_execution(
        tool_name="execute_terminal_command",
        tool_args={"command": normal_cmd},
        mode=OperatingMode.AUTONOMOUS
    )
    assert normal_verdict.is_allowed is True
    assert normal_verdict.requires_user_confirmation is False
