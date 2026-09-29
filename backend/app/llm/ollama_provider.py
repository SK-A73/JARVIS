"""
Local Ollama LLM Provider
Interacts with local Ollama daemon for offline, zero-cost, private AI inference.
"""
import json
import logging
from typing import List, Dict, Any, Optional, AsyncIterator
import httpx
from backend.app.llm.base import LLMProvider, LLMMessage, ToolDefinition, LLMResponse, ToolCall

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model_name: str = "llama3.2"):
        super().__init__(model_name)
        self.base_url = base_url.rstrip("/")

    async def is_available(self) -> bool:
        """Checks if the local Ollama server is running and reachable."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        converted = []
        for m in messages:
            item = {"role": m.role, "content": m.content or ""}
            if m.tool_calls:
                item["tool_calls"] = [
                    {"function": {"name": tc.name, "arguments": tc.arguments}}
                    for tc in m.tool_calls
                ]
            converted.append(item)
        return converted

    def _convert_tools(self, tools: Optional[List[ToolDefinition]]) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters
                }
            }
            for t in tools
        ]

    async def generate_response(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> LLMResponse:
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": self._convert_messages(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        converted_tools = self._convert_tools(tools)
        if converted_tools:
            payload["tools"] = converted_tools
        if response_format and response_format.get("type") == "json_object":
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        message_data = data.get("message", {})
        content = message_data.get("content", "")
        raw_tool_calls = message_data.get("tool_calls", [])

        tool_calls: List[ToolCall] = []
        for i, tc in enumerate(raw_tool_calls):
            fn = tc.get("function", {})
            name = fn.get("name", "")
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {"raw": args}
            tool_calls.append(ToolCall(
                id=f"ollama_tc_{i}",
                name=name,
                arguments=args
            ))

        finish_reason = "tool_calls" if tool_calls else ("stop" if data.get("done") else "length")
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
        }

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            provider="ollama",
            model=self.model_name,
            usage=usage
        )

    async def stream_response(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncIterator[str]:
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": self._convert_messages(messages),
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        converted_tools = self._convert_tools(tools)
        if converted_tools:
            payload["tools"] = converted_tools

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        text_piece = chunk.get("message", {}).get("content", "")
                        if text_piece:
                            yield text_piece
                    except json.JSONDecodeError:
                        continue

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        results = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for text in texts:
                resp = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model_name, "prompt": text}
                )
                if resp.status_code == 200:
                    results.append(resp.json().get("embedding", []))
                else:
                    results.append([])
        return results
