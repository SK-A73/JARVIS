"""
JARVIS System Configuration Module
Loads settings from environment variables and .env file with strong typing.
"""
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Server & Networking
    JARVIS_HOST: str = "127.0.0.1"
    JARVIS_PORT: int = 8000
    JARVIS_ENV: Literal["development", "production", "test"] = "development"
    JARVIS_SECRET_KEY: str = "change-this-to-a-secure-random-32-byte-hex-secret"
    JARVIS_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # LLM Providers Configuration
    DEFAULT_LLM_PROVIDER: Literal["ollama", "openai", "anthropic", "mock"] = "mock"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama3.2"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Database
    DATABASE_URL: str = "sqlite:///./jarvis.db"

    # Workspace & File Sandboxing
    WORKSPACE_ROOT: str = str(BASE_DIR / "workspace_storage")
    MAX_COMMAND_TIMEOUT_SECONDS: int = 60
    DANGEROUS_COMMANDS_CONFIRMATION: bool = True

    # Multi-Device & Security
    ALLOW_DEVICE_REGISTRATION: bool = True
    ADMIN_PASSWORD: str = "jarvis_secure_admin_password_2026"
    DEVICE_HEARTBEAT_INTERVAL_SECONDS: int = 30
    DEVICE_OFFLINE_TIMEOUT_SECONDS: int = 90

    # Memory Engine
    EMBEDDING_PROVIDER: Literal["local", "ollama", "openai"] = "local"
    MEMORY_SIMILARITY_THRESHOLD: float = 0.5
    MAX_RELEVANT_MEMORIES: int = 8

settings = Settings()
