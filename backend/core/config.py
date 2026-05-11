from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost/agentforge"
    openai_api_key: str = ""
    telegram_bot_token: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_base_url: str = ""
    cors_origins: List[str] = ["http://localhost:5173"]
    ws_heartbeat_interval: int = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        # Railway sets env vars as plain strings, not JSON lists
        # Accept both: "https://a.com,https://b.com" and '["https://a.com"]'
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
