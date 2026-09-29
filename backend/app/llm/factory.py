"""
LLM Provider Factory with Automatic Fallback and Resilience
"""
import logging
from typing import Optional
from backend.app.config import settings
from backend.app.llm.base import LLMProvider
from backend.app.llm.mock_provider import MockLLMProvider
from backend.app.llm.ollama_provider import OllamaProvider
from backend.app.llm.openai_provider import OpenAIProvider
from backend.app.llm.anthropic_provider import AnthropicProvider

logger = logging.getLogger(__name__)

class LLMProviderFactory:
    _instances = {}

    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None, model_name: Optional[str] = None) -> LLMProvider:
        name = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()

        if name == "ollama":
            model = model_name or settings.OLLAMA_MODEL
            return OllamaProvider(base_url=settings.OLLAMA_BASE_URL, model_name=model)

        elif name == "openai":
            model = model_name or settings.OPENAI_MODEL
            return OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                model_name=model
            )

        elif name == "anthropic":
            model = model_name or settings.ANTHROPIC_MODEL
            return AnthropicProvider(
                api_key=settings.ANTHROPIC_API_KEY,
                model_name=model
            )

        elif name == "mock":
            return MockLLMProvider(model_name=model_name or "mock-jarvis-v1")

        else:
            logger.warning(f"Unknown LLM provider '{name}', falling back to MockLLMProvider.")
            return MockLLMProvider(model_name=model_name or "mock-jarvis-v1")
