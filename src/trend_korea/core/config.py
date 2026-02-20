from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Trend Korea API"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/trend_korea"

    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    jwt_secret_key: str = Field(default="change-me-in-env", min_length=16)
    jwt_algorithm: str = "HS256"

    scheduler_timezone: str = "Asia/Seoul"
    auto_create_tables: bool = True

    cors_origins: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()] or ["*"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
