"""FastAPI 依赖注入。"""

from __future__ import annotations

from typing import Iterator

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from thinklab_core import ThinkLabAgent, get_agent
from thinklab_core.logging_utils import get_logger

from . import repositories
from .db import get_session_factory

logger = get_logger("deps")


def get_db() -> Iterator[Session]:
    db = get_session_factory()()
    try:
        yield db
    except Exception:
        # 请求处理中抛出异常时回滚未提交的事务，再交由上层处理器响应
        logger.debug("请求处理异常，回滚数据库事务")
        db.rollback()
        raise
    finally:
        db.close()


def get_ai_agent() -> ThinkLabAgent:
    return get_agent()


def require_session(session_id: str, db: Session = Depends(get_db)):
    from . import models  # noqa: F401

    session = repositories.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="探索不存在")
    return session
