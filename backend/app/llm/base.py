"""
Modular LLM Abstraction Layer
Defines common interfaces, message schemas, and provider contracts.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator, Union
from pydantic import BaseModel, Field
import json

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]

class LLMMessage(BaseModel):
    role: str  # system | user | assistant | tool
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema

class LLMResponse(BaseModel):
    content: Optional[str] = ""
    tool_calls: List[ToolCall] = Field(default_factory=list)
    finish_reason: str = "stop"  # stop | tool_calls | length | error
    provider: str
    model: str
    usage: Dict[str, int] = Field(default_factory=dict)

class LLMProvider(ABC):
    """Abstract Base Class for all LLM providers (Ollama, OpenAI, Anthropic, Mock)."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    async def generate_response(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> LLMResponse:
        """Generates a complete response with optional tool calling."""
        pass

    @abstractmethod
    async def stream_response(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncIterator[str]:
        """Streams text chunks in real-time."""
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates vector embeddings for memory and semantic search."""
        pass
