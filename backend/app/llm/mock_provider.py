"""
Deterministic Mock LLM Provider
Used for CI, unit testing, and fallback when offline or no API keys are provided.
"""
import asyncio
import hashlib
import json
import math
from typing import List, Dict, Any, Optional, AsyncIterator
from backend.app.llm.base import LLMProvider, LLMMessage, ToolDefinition, LLMResponse, ToolCall

class MockLLMProvider(LLMProvider):
    def __init__(self, model_name: str = "mock-jarvis-v1"):
        super().__init__(model_name)
        self.canned_responses: Dict[str, str] = {}
        self.default_canned_tool_call: Optional[ToolCall] = None

    def set_canned_response(self, prompt_substring: str, response: str):
        self.canned_responses[prompt_substring.lower()] = response

    def set_canned_tool_call(self, tool_call: ToolCall):
        self.default_canned_tool_call = tool_call

    async def generate_response(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> LLMResponse:
        last_message = messages[-1].content if messages else ""

        # Check for configured tool call
        if self.default_canned_tool_call and tools:
            # Match tool name
            matching = [t for t in tools if t.name == self.default_canned_tool_call.name]
            if matching:
                return LLMResponse(
                    content="",
                    tool_calls=[self.default_canned_tool_call],
                    finish_reason="tool_calls",
                    provider="mock",
                    model=self.model_name
                )

        # Check for heuristic tool invocation in test prompts
        if tools and "execute command:" in last_message.lower():
            cmd = last_message.split("execute command:", 1)[1].strip()
            return LLMResponse(
                content="Executing the requested terminal command.",
                tool_calls=[ToolCall(
                    id="mock-call-1",
                    name="execute_terminal_command",
                    arguments={"command": cmd}
                )],
                finish_reason="tool_calls",
                provider="mock",
                model=self.model_name
            )

        if tools and "read file" in last_message.lower():
            return LLMResponse(
                content="Reading the requested file.",
                tool_calls=[ToolCall(
                    id="mock-call-2",
                    name="read_file",
                    arguments={"file_path": "README.md"}
                )],
                finish_reason="tool_calls",
                provider="mock",
                model=self.model_name
            )

        # Check canned responses
        for key, canned in self.canned_responses.items():
            if key in last_message.lower():
                return LLMResponse(
                    content=canned,
                    provider="mock",
                    model=self.model_name
                )

        # Structured output check
        if response_format and response_format.get("type") == "json_object":
            content_json = json.dumps({
                "response": "JARVIS processed your request successfully.",
                "status": "ready",
                "intent": "general_query"
            })
            return LLMResponse(content=content_json, provider="mock", model=self.model_name)

        # Default conversational response
        response_text = f"JARVIS: I have analyzed your request: '{last_message}'. All systems are online and functioning normally."
        return LLMResponse(
            content=response_text,
            provider="mock",
            model=self.model_name,
            usage={"prompt_tokens": 15, "completion_tokens": 25, "total_tokens": 40}
        )

    async def stream_response(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncIterator[str]:
        resp = await self.generate_response(messages, tools, temperature=temperature)
        tokens = resp.content.split(" ")
        for i, token in enumerate(tokens):
            yield token + (" " if i < len(tokens) - 1 else "")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates deterministic pseudo-embeddings using SHA-256 for consistent testing."""
        dim = 256
        results = []
        for text in texts:
            vec = [0.0] * dim
            words = text.lower().split()
            for word in words:
                h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
                idx = h % dim
                vec[idx] += 1.0

            # L2 normalize
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            results.append(vec)
        return results
