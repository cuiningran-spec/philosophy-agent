"""健康检查与运行时信息。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..deps import get_ai_agent, get_db
from ..schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db), agent=Depends(get_ai_agent)):
    try:
        db.execute(text("SELECT 1"))
        database = "up"
    except Exception:
        database = "down"
    return HealthOut(status="ok", database=database, agent=agent.runtime_info())
