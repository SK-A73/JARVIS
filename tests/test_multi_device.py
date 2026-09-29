"""
Tests for Multi-Device Routing Mesh, Command Router, and Laptop Node Executor
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.models.auth import DeviceNode
from backend.app.routing.device_manager import DeviceMeshManager
from backend.app.routing.command_router import CommandRouter
from laptop_node.system_executor import SystemExecutor

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

def test_system_executor_metrics():
    metrics = SystemExecutor.get_system_metrics()
    assert "platform" in metrics
    assert "cpu_percent" in metrics
    assert "memory_percent" in metrics
    assert "disk_percent" in metrics

def test_system_executor_shell():
    res = SystemExecutor.execute_shell("python -c \"print('Node alive')\"")
    assert res["exit_code"] == 0
    assert "Node alive" in res["stdout"]

def test_device_capability_discovery_and_routing():
    db = TestingSessionLocal()
    mesh = DeviceMeshManager()

    # Register Laptop Node
    laptop = DeviceNode(
        id="dev-laptop-lenovo",
        name="Lenovo Dev",
        device_type="laptop",
        api_token_hash="hash_laptop_123",
        is_active=True,
        is_online=True,
        capabilities=["terminal", "filesystem", "build_tools"]
    )
    # Register Phone Node
    phone = DeviceNode(
        id="dev-phone-pixel",
        name="Pixel 9 Pro",
        device_type="phone",
        api_token_hash="hash_phone_123",
        is_active=True,
        is_online=True,
        capabilities=["microphone", "speaker", "notifications"]
    )
    db.add_all([laptop, phone])
    db.commit()

    # Find device for capability "terminal"
    target_dev = mesh.find_device_for_capability("terminal", db)
    assert target_dev is not None
    assert target_dev.id == "dev-laptop-lenovo"

    # Command Router: "Run the Python project on my laptop"
    target_id, message = CommandRouter.resolve_target_device("JARVIS, run the Python project on my laptop", "dev-phone-pixel", db)
    assert target_id == "dev-laptop-lenovo"
    assert "laptop" in message.lower()

    # Command Router: "Send report to my phone"
    target_id2, message2 = CommandRouter.resolve_target_device("Send the report to my phone", "dev-laptop-lenovo", db)
    assert target_id2 == "dev-phone-pixel"

    db.close()
