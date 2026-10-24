"""FastAPI 依赖注入。"""

from __future__ import annotations

from typing import Iterator

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from thinklab_core import ThinkLabAgent, get_agent

from . import repositories
from .db import get_session_factory


def get_db() -> Iterator[Session]:
    db = get_session_factory()()
    try:
        yield db
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
