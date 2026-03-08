from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_ENV, env_file_encoding="utf-8", extra="ignore"
    )

    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_secret_key: str | None = Field(default=None, alias="SUPABASE_SECRET_KEY")
    supabase_service_role_key_legacy: str | None = Field(
        default=None, alias="SUPABASE_SERVICE_ROLE_KEY"
    )
    supabase_board_slug: str = Field(
        default="limitboard-default", alias="SUPABASE_BOARD_SLUG"
    )
    server_host: str = Field(default="0.0.0.0", alias="SERVER_HOST")
    server_port: int = Field(default=8000, alias="SERVER_PORT")
    server_cors_origins: str = Field(
        default="http://localhost:3000", alias="SERVER_CORS_ORIGINS"
    )
    scheduler_timezone: str = Field(default="Asia/Shanghai", alias="SCHEDULER_TIMEZONE")
    engine_parallelism: bool = Field(default=True, alias="ENGINE_PARALLELISM")
    admin_api_key: str = Field(default="", alias="ADMIN_API_KEY")
    tracking_top_turnover_count: int = Field(
        default=20, alias="TRACKING_TOP_TURNOVER_COUNT"
    )
    tracking_limit_up_pool_count: int = Field(
        default=20, alias="TRACKING_LIMIT_UP_POOL_COUNT"
    )
    tracking_include_symbols: str = Field(default="", alias="TRACKING_INCLUDE_SYMBOLS")

    @property
    def cors_origins(self) -> list[str]:
        return [
            item.strip() for item in self.server_cors_origins.split(",") if item.strip()
        ]

    @property
    def tracking_symbols(self) -> list[str]:
        return [
            item.strip()
            for item in self.tracking_include_symbols.split(",")
            if item.strip()
        ]

    @property
    def supabase_server_key(self) -> str | None:
        return self.supabase_secret_key or self.supabase_service_role_key_legacy

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_server_key)


settings = Settings()
