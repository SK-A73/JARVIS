"""
Tests for LLM Providers and Factory
"""
import pytest
import asyncio
from backend.app.llm.base import LLMMessage, ToolDefinition, ToolCall
from backend.app.llm.mock_provider import MockLLMProvider
from backend.app.llm.factory import LLMProviderFactory

@pytest.mark.asyncio
async def test_mock_provider_basic_response():
    provider = MockLLMProvider("mock-v1")
    messages = [
        LLMMessage(role="system", content="You are JARVIS."),
        LLMMessage(role="user", content="Hello JARVIS, status report.")
    ]
    resp = await provider.generate_response(messages)
    assert resp.content != ""
    assert "JARVIS" in resp.content
    assert resp.provider == "mock"
    assert resp.finish_reason == "stop"

@pytest.mark.asyncio
async def test_mock_provider_canned_tool_call():
    provider = MockLLMProvider("mock-v1")
    canned_call = ToolCall(
        id="call-42",
        name="read_file",
        arguments={"file_path": "project/main.py"}
    )
    provider.set_canned_tool_call(canned_call)

    tools = [
        ToolDefinition(
            name="read_file",
            description="Reads file contents",
            parameters={"type": "object", "properties": {"file_path": {"type": "string"}}}
        )
    ]
    messages = [LLMMessage(role="user", content="Please inspect the code")]
    resp = await provider.generate_response(messages, tools=tools)

    assert resp.finish_reason == "tool_calls"
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == "read_file"
    assert resp.tool_calls[0].arguments["file_path"] == "project/main.py"

@pytest.mark.asyncio
async def test_mock_provider_streaming():
    provider = MockLLMProvider("mock-v1")
    messages = [LLMMessage(role="user", content="Quick ping")]
    chunks = []
    async for chunk in provider.stream_response(messages):
        chunks.append(chunk)

    full_text = "".join(chunks)
    assert len(chunks) > 1
    assert "JARVIS" in full_text

@pytest.mark.asyncio
async def test_mock_provider_embeddings():
    provider = MockLLMProvider("mock-v1")
    texts = [
        "JARVIS is an autonomous assistant",
        "Deploy PostgreSQL database"
    ]
    embeddings = await provider.generate_embeddings(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 256
    assert len(embeddings[1]) == 256
    # Check normalization: sum of squares ~ 1.0
    norm_sq = sum(x * x for x in embeddings[0])
    assert abs(norm_sq - 1.0) < 1e-4

def test_provider_factory():
    mock_prov = LLMProviderFactory.get_provider("mock")
    assert isinstance(mock_prov, MockLLMProvider)

    # Unknown provider falls back safely to mock
    unknown_prov = LLMProviderFactory.get_provider("non_existent_provider")
    assert isinstance(unknown_prov, MockLLMProvider)
