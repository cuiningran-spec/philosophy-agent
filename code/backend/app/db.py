"""SQLAlchemy 引擎与会话（PostgreSQL 优先，不可用时降级 SQLite）。"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import Settings, get_settings


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex}"


def _build_engine(settings: Settings):
    mode = (settings.db_mode or "auto").lower()
    sqlite_path = Path(settings.sqlite_path)
    if not sqlite_path.is_absolute():
        sqlite_path = Path(__file__).resolve().parents[1] / settings.sqlite_path

    if mode in ("auto", "postgres"):
        url = settings.resolved_database_url()
        try:
            engine = create_engine(url, pool_pre_ping=True, future=True)
            with engine.connect() as conn:  # 实际连通性探测
                conn.exec_driver_sql("SELECT 1")
            print(f"[thinklab] 已连接 PostgreSQL：{url.split('@')[-1]}")
            return engine
        except Exception as exc:
            if mode == "postgres":
                raise
            print(f"[thinklab] PostgreSQL 不可用（{exc}），降级为 SQLite：{sqlite_path}")

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{sqlite_path}", future=True)

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


_engine = None
_session_factory: Optional[sessionmaker] = None


def init_engine(settings: Optional[Settings] = None) -> None:
    global _engine, _session_factory
    settings = settings or get_settings()
    _engine = _build_engine(settings)
    _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)


def get_engine():
    global _engine
    if _engine is None:
        init_engine()
    return _engine


def get_session_factory() -> sessionmaker:
    global _session_factory
    if _session_factory is None:
        init_engine()
    assert _session_factory is not None
    return _session_factory


def create_tables() -> None:
    from . import models  # noqa: F401 确保模型被注册

    Base.metadata.create_all(bind=get_engine())


def session_scope() -> Session:
    """非 FastAPI 上下文（脚本 / 测试）使用的会话。"""
    return get_session_factory()()
