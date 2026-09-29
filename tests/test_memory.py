"""
Tests for Memory Manager, Hybrid Retrieval, and Memory Control
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.models.memory import MemoryRecord, ProjectContext
from backend.app.memory.retriever import HybridRetriever, cosine_similarity, keyword_overlap_score
from backend.app.memory.manager import MemoryManager
from backend.app.llm.mock_provider import MockLLMProvider

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    assert abs(cosine_similarity(v1, v2) - 1.0) < 1e-5
    assert abs(cosine_similarity(v1, v3) - 0.0) < 1e-5

def test_keyword_overlap_score():
    score = keyword_overlap_score("use postgresql database", "we decided to use postgresql database for backend")
    assert score > 0.4
    unrelated = keyword_overlap_score("cooking pasta recipes", "deploy fast docker container")
    assert unrelated == 0.0

@pytest.mark.asyncio
async def test_memory_manager_add_and_retrieve():
    db = TestingSessionLocal()
    llm = MockLLMProvider()
    manager = MemoryManager(db, llm)

    # Add several memories
    await manager.add_memory("User prefers tabs over spaces", category="long_term", importance=8.0)
    await manager.add_memory("User wants PostgreSQL database instead of MongoDB", category="long_term", importance=9.0)
    await manager.add_memory("Deploy on port 9000 for local dev", category="project", importance=4.0)

    # Query for database preference
    results = await manager.retrieve_relevant(query="What database should we use?", limit=2)
    assert len(results) > 0
    top_mem, score = results[0]
    assert "PostgreSQL" in top_mem.content

    db.close()

@pytest.mark.asyncio
async def test_natural_memory_commands():
    db = TestingSessionLocal()
    llm = MockLLMProvider()
    manager = MemoryManager(db, llm)

    # 1. "Remember that" command
    cmd_resp = await manager.handle_natural_memory_command("JARVIS, remember that my favorite color is dark cyan")
    assert cmd_resp is not None
    assert cmd_resp["handled"] is True
    assert cmd_resp["action"] == "remembered"

    # 2. "What do you remember about" command
    query_resp = await manager.handle_natural_memory_command("JARVIS, what do you remember about favorite color?")
    assert query_resp is not None
    assert query_resp["handled"] is True
    assert "dark cyan" in query_resp["message"]

    # 3. "Forget that" command
    forget_resp = await manager.handle_natural_memory_command("JARVIS, forget favorite color")
    assert forget_resp is not None
    assert forget_resp["handled"] is True
    assert forget_resp["action"] == "forgot"

    # Verify forgotten
    after_query = await manager.handle_natural_memory_command("JARVIS, what do you remember about favorite color?")
    assert after_query["action"] == "empty"

    db.close()

@pytest.mark.asyncio
async def test_project_memory_purge():
    db = TestingSessionLocal()
    llm = MockLLMProvider()
    manager = MemoryManager(db, llm)

    proj = ProjectContext(name="StarkIndustriesPortal")
    db.add(proj)
    db.commit()
    db.refresh(proj)

    await manager.add_memory("Project uses Python 3.11", category="project", project_id=proj.id)
    await manager.add_memory("Project auth uses OAuth2", category="project", project_id=proj.id)
    await manager.add_memory("General note: user is admin", category="long_term")

    # Purge project memories
    purged_count = manager.purge_project_memories(proj.id)
    assert purged_count == 2

    # Global note should remain
    remaining = db.query(MemoryRecord).all()
    assert len(remaining) == 1
    assert remaining[0].category == "long_term"

    db.close()
