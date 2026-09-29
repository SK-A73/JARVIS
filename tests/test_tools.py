"""
Tests for Sandboxed File, Terminal, and Git Tools
"""
import pytest
import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.tools.file_tools import (
    write_file,
    read_file,
    edit_file_block,
    list_directory,
    search_files_regex
)
from backend.app.tools.terminal_tools import execute_terminal_command
from backend.app.tools.registry import ToolRegistry
from backend.app.agent.modes import OperatingMode
from backend.app.models.task import AuditLog

TEST_WORKSPACE = "./test_scratch_workspace"

@pytest.fixture(autouse=True)
def setup_workspace():
    os.makedirs(TEST_WORKSPACE, exist_ok=True)
    yield
    if os.path.exists(TEST_WORKSPACE):
        shutil.rmtree(TEST_WORKSPACE, ignore_errors=True)

def test_file_tools_crud():
    # 1. Write file
    target = os.path.join(TEST_WORKSPACE, "sub", "hello.txt")
    write_res = write_file(target, "Hello Stark Industries!\nLine 2: Mark 42\nLine 3: Complete")
    assert "Successfully wrote" in write_res

    # 2. Read full file
    full_content = read_file(target)
    assert "Mark 42" in full_content

    # 3. Read slice
    sliced = read_file(target, start_line=2, end_line=2)
    assert "Line 2: Mark 42" in sliced
    assert "Line 3" not in sliced

    # 4. Edit block
    edit_file_block(target, "Mark 42", "Mark 85")
    updated = read_file(target)
    assert "Mark 85" in updated
    assert "Mark 42" not in updated

    # 5. List directory
    items = list_directory(TEST_WORKSPACE, depth=3)
    assert len(items) > 0

    # 6. Regex search
    matches = search_files_regex(TEST_WORKSPACE, r"Mark \d+", file_pattern="*.txt")
    assert len(matches) == 1
    assert "Mark 85" in matches[0]["content"]

@pytest.mark.asyncio
async def test_terminal_tool_execution():
    res = await execute_terminal_command("python -c \"print('JARVIS Terminal Online')\"", cwd=TEST_WORKSPACE)
    assert res["exit_code"] == 0
    assert "JARVIS Terminal Online" in res["stdout"]
    assert res["is_timeout"] is False

@pytest.mark.asyncio
async def test_terminal_tool_timeout():
    # Small timeout to test timeout behavior
    res = await execute_terminal_command("python -c \"import time; time.sleep(5)\"", cwd=TEST_WORKSPACE, timeout_seconds=1)
    assert res["is_timeout"] is True

@pytest.mark.asyncio
async def test_tool_registry_with_audit():
    TEST_DB_URL = "sqlite:///:memory:"
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Execute allowed tool
    res = await ToolRegistry.execute_tool(
        "write_file",
        {"file_path": os.path.join(TEST_WORKSPACE, "sample.py"), "content": "print('hello')", "overwrite": True},
        mode=OperatingMode.IMPLEMENT,
        db=db
    )
    assert res["success"] is True

    # Verify audit log was created
    audit = db.query(AuditLog).first()
    assert audit is not None
    assert audit.action == "tool_execution:write_file"
    assert audit.status == "SUCCESS"

    db.close()
