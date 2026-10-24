"""后端配置：把 core_engine 加入模块搜索路径，并解析数据库连接。"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 让后端可以直接 import 同仓库的 core_engine 包
CORE_ENGINE_PATH = Path(__file__).resolve().parents[2] / "core_engine"
if str(CORE_ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(CORE_ENGINE_PATH))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = Field(default="ThinkLab Agent API")
    api_prefix: str = Field(default="/api")
    cors_origins: str = Field(default="*")

    database_url: Optional[str] = Field(default=None)
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="postgres")
    postgres_db: str = Field(default="thinklab")

    # auto | postgres | sqlite：auto 在 PostgreSQL 不可用时降级到 SQLite，便于本地演示
    db_mode: str = Field(default="auto", validation_alias=AliasChoices("THINKLAB_DB_MODE", "db_mode"))
    sqlite_path: str = Field(
        default="./.cache/thinklab.db",
        validation_alias=AliasChoices("THINKLAB_SQLITE_PATH", "sqlite_path"),
    )

    auto_create_tables: bool = Field(default=True)
    auto_ingest_on_startup: bool = Field(default=True)

    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
