"""探索会话：创建（生成三视角）、查询、选择视角。"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from thinklab_core.lenses import LENS_PROFILES

from .. import repositories
from ..deps import get_ai_agent, get_db
from ..schemas import CreateSessionIn, LensOut, SelectLensIn, SessionDetail, SessionOut
from ..serializers import lens_out, session_detail, session_out

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionDetail, status_code=201)
def create_session(payload: CreateSessionIn, db: Session = Depends(get_db), agent=Depends(get_ai_agent)):
    """输入一个现实问题 → 生成三种有区别的哲学视角。"""
    session = repositories.create_session(db, payload.question)
    try:
        result = agent.read_and_perspectives(payload.question)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"视角生成失败：{exc}")

    repositories.save_perspectives(db, session.id, [lens.model_dump() for lens in result.lenses])
    repositories.log_retrieval(
        db,
        query=payload.question,
        hits=[s.model_dump() for s in result.sources],
        session_id=session.id,
    )
    # 保存 Agent 对问题的初步阅读（存为首条 agent 消息，role=agent，turn=0）
    repositories.add_message(
        db, session.id, "agent", result.reading, turn_index=0
    )
    db.commit()

    return _detail(db, session, reading=result.reading)


@router.get("", response_model=List[SessionOut])
def list_sessions(limit: int = 30, db: Session = Depends(get_db)):
    return [session_out(s, db) for s in repositories.list_sessions(db, limit=limit)]


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = repositories.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="探索不存在")
    return _detail(db, session)


@router.get("/{session_id}/lenses", response_model=List[LensOut])
def get_lenses(session_id: str, db: Session = Depends(get_db)):
    return [lens_out(p) for p in repositories.list_perspectives(db, session_id)]


@router.post("/{session_id}/lens", response_model=SessionDetail)
def select_lens(
    session_id: str,
    payload: SelectLensIn,
    db: Session = Depends(get_db),
    agent=Depends(get_ai_agent),
):
    """选择一个视角：写入会话，并由 Agent 给出该视角的开场。"""
    session = repositories.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="探索不存在")
    if payload.lens not in LENS_PROFILES:
        raise HTTPException(status_code=400, detail="未知的哲学视角")

    profile = LENS_PROFILES[payload.lens]
    repositories.set_lens(db, session, payload.lens, profile.name, profile.core_ask)

    # 切换视角时开启一条新的对话分支：清空旧消息，保留原始问题
    if not payload.keep_history:
        for message in repositories.list_messages(db, session_id):
            db.delete(message)
        db.flush()

    # 开场语只保留当前视角的那一条（移除创建会话时写入的“初步阅读”）
    for message in repositories.list_messages(db, session_id):
        if message.role == "agent" and message.turn_index == 0:
            db.delete(message)
    db.flush()

    intro = agent.intro(payload.lens)
    repositories.add_message(db, session_id, "agent", intro, turn_index=0)
    db.commit()
    return _detail(db, session)


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    session = repositories.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="探索不存在")
    db.delete(session)
    db.commit()


def _detail(db: Session, session, reading: str = "") -> SessionDetail:
    perspectives = repositories.list_perspectives(db, session.id)
    messages = repositories.list_messages(db, session.id)
    summaries = repositories.list_summaries(db, session.id)
    if not reading:
        for message in messages:
            if message.role == "agent" and message.turn_index == 0:
                reading = message.content
                break
    return session_detail(session, perspectives, messages, summaries, db=db, reading=reading)
