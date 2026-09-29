"""
Anthropic Claude LLM Provider
Supports Claude 3.5 Sonnet, Haiku, Opus via Anthropic Messages API.
"""
import json
import logging
from typing import List, Dict, Any, Optional, AsyncIterator
import httpx
from backend.app.llm.base import LLMProvider, LLMMessage, ToolDefinition, LLMResponse, ToolCall

logger = logging.getLogger(__name__)

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "claude-3-5-sonnet-20241022"):
        super().__init__(model_name)
        self.api_key = api_key or ""
        self.base_url = "https://api.anthropic.com/v1"

    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

    async def generate_response(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Anthropic API key is missing. Set ANTHROPIC_API_KEY in .env")

        system_prompt = ""
        claude_messages = []
        for m in messages:
            if m.role == "system":
                system_prompt += (m.content or "") + "\n"
            else:
                claude_messages.append({"role": m.role if m.role in ["user", "assistant"] else "user", "content": m.content or ""})

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": claude_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        if system_prompt:
            payload["system"] = system_prompt.strip()

        if tools:
            payload["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters
                }
                for t in tools
            ]

        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(f"{self.base_url}/messages", headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = ""
        tool_calls = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.get("id", ""),
                    name=block.get("name", ""),
                    arguments=block.get("input", {})
                ))

        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=data.get("stop_reason", "end_turn"),
            provider="anthropic",
            model=self.model_name,
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            }
        )

    async def stream_response(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncIterator[str]:
        # For simplicity and fallback, generate response then stream chunks
        resp = await self.generate_response(messages, tools, temperature=temperature, max_tokens=max_tokens)
        if resp.content:
            for word in resp.content.split(" "):
                yield word + " "

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Anthropic does not have a native embeddings endpoint; raise or return empty
        return [[] for _ in texts]
