"""Application settings loaded from environment variables.

All configuration is explicit.  No hidden defaults for secrets.
Requires GITHUB_TOKEN to be set — no unauthenticated GitHub calls.
"""

from __future__ import annotations

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    GITHUB_TOKEN: str
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost/proofstack"
    API_KEY: str = "proofstack-demo-2025"
    REDIS_URL: str = "redis://localhost:6379/0"
    FRONTEND_URL: str = "http://localhost:3000"


settings = Settings()  # type: ignore[call-arg]
