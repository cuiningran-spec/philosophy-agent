"""思考总结：随时生成结构化记录，生成后对话仍可继续。"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import repositories
from ..deps import get_ai_agent, get_db
from ..schemas import SummaryOut
from ..serializers import summary_out

router = APIRouter(tags=["summaries"])


def _clip(text: str, length: int = 220) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= length else value[:length] + "…"


@router.post("/sessions/{session_id}/summaries", response_model=SummaryOut, status_code=201)
def create_summary(session_id: str, db: Session = Depends(get_db), agent=Depends(get_ai_agent)):
    session = repositories.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="探索不存在")
    if not session.lens:
        raise HTTPException(status_code=400, detail="请先选择一种哲学视角")

    history = repositories.history_for_agent(db, session_id)
    try:
        result = agent.summarize(
            question=session.question,
            lens_key=session.lens,
            history=history,
            rolling_summary=session.rolling_summary or "",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"总结生成失败：{exc}")

    messages = repositories.list_messages(db, session_id)
    excerpts = [
        {
            "role": m.role,
            "text": _clip(m.content),
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages[-6:]
        if m.turn_index > 0
    ]

    row = repositories.create_summary(db, session_id, result.model_dump(), excerpts)
    db.commit()
    return summary_out(row)


@router.get("/sessions/{session_id}/summaries", response_model=List[SummaryOut])
def list_summaries(session_id: str, db: Session = Depends(get_db)):
    return [summary_out(row) for row in repositories.list_summaries(db, session_id)]


@router.get("/summaries/{summary_id}", response_model=SummaryOut)
def get_summary(summary_id: str, db: Session = Depends(get_db)):
    row = repositories.get_summary(db, summary_id)
    if not row:
        raise HTTPException(status_code=404, detail="思考记录不存在")
    return summary_out(row)
