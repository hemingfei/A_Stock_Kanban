from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
import json


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    env: str = "development"
    debug: bool = False

    # JWT settings
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_hours: int = 2
    jwt_refresh_token_expire_days: int = 7

    # Database
    database_url: str = "sqlite:///./data/astock.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Tushare (optional)
    tushare_token: str = ""

    # Rate limiting
    rate_limit_enabled: bool = True

    # CORS
    cors_origins: str = '["http://localhost:3000","http://localhost:5173"]'

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        try:
            return json.loads(self.cors_origins)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
