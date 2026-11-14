"""多轮对话：普通接口 + SSE 流式接口（检索增强 + 滚动记忆）。"""

from __future__ import annotations

import json
from typing import Iterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from thinklab_core.llm import bind_task
from thinklab_core.logging_utils import get_logger

from .. import repositories
from ..deps import get_ai_agent, get_db
from ..safety import guard_text, is_boundary_level
from ..schemas import SendMessageIn, SendMessageOut
from ..serializers import message_out

logger = get_logger("chat")

router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["chat"])


def _require_ready(session_id: str, db: Session):
    session = repositories.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="探索不存在")
    if not session.lens:
        raise HTTPException(status_code=400, detail="请先选择一种哲学视角")
    return session


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


@router.post("", response_model=SendMessageOut)
def send_message(
    session_id: str,
    payload: SendMessageIn,
    db: Session = Depends(get_db),
    agent=Depends(get_ai_agent),
):
    """一次完整的问答：guardrails → 写入用户追问 → 检索 → 生成 → 写入 Agent 回复。"""
    session = _require_ready(session_id, db)
    # guardrails：拦截/越界的输入在此终止（不会保存、不会调用 LLM）
    content, decision = guard_text(payload.content)
    history = repositories.history_for_agent(db, session_id)

    user_message = repositories.add_message(db, session_id, "user", content)
    db.commit()

    # 专业判断类：跳过 LLM，直接返回能力边界提示（对话可继续）
    if is_boundary_level(decision):
        logger.info("专业判断类输入（%s），返回能力边界提示（session=%s）", decision.category, session_id)
        agent_message = repositories.add_message(
            db, session_id, "agent", decision.reason, turn_index=user_message.turn_index
        )
        db.commit()
        return SendMessageOut(
            user_message=message_out(user_message),
            agent_message=message_out(agent_message),
            rolling_summary_updated=False,
        )

    try:
        result = agent.reply(
            question=session.question,
            lens_key=session.lens,
            history=history,
            user_input=content,
            rolling_summary=session.rolling_summary or "",
        )
    except Exception as exc:
        db.rollback()
        logger.error("Agent 回复失败（session=%s）：%s", session_id, exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Agent 回复失败：{exc}") from exc

    agent_message = repositories.add_message(
        db,
        session_id,
        "agent",
        result.content,
        sources=[s.model_dump() for s in result.sources],
        turn_index=user_message.turn_index,
    )
    repositories.log_retrieval(
        db,
        query=content,
        hits=[s.model_dump() for s in result.sources],
        school=session.lens,
        session_id=session_id,
    )

    rolling_updated = False
    if getattr(result, "used_memory_summary", False):
        from thinklab_core.memory import DialogueMemory

        memory = DialogueMemory(
            repositories.history_for_agent(db, session_id), session.rolling_summary or ""
        )
        if memory.should_compress():
            llm = bind_task(
                agent.llm, "compress", {"question": session.question, "lens": session.lens}
            )
            new_summary = memory.compress(llm)
            if new_summary and new_summary != session.rolling_summary:
                repositories.update_rolling_summary(db, session, new_summary)
                rolling_updated = True

    db.commit()
    return SendMessageOut(
        user_message=message_out(user_message),
        agent_message=message_out(agent_message),
        rolling_summary_updated=rolling_updated,
    )


@router.post("/stream")
def send_message_stream(
    session_id: str,
    payload: SendMessageIn,
    db: Session = Depends(get_db),
    agent=Depends(get_ai_agent),
):
    """SSE 流式问答：guardrails → user → token* → done。"""
    session = _require_ready(session_id, db)
    # guardrails：拦截/越界的输入在此终止（异常在流开始前返回，不会调用 LLM）
    content, decision = guard_text(payload.content)
    history = repositories.history_for_agent(db, session_id)
    user_message = repositories.add_message(db, session_id, "user", content)
    db.commit()
    user_payload = message_out(user_message).model_dump(mode="json")

    # 专业判断类：跳过 LLM，流式返回能力边界提示（对话可继续）
    professional = is_boundary_level(decision)

    def event_stream() -> Iterator[str]:
        yield _sse("user", {"message": user_payload})
        if professional:
            logger.info("专业判断类输入（%s），流式返回能力边界提示（session=%s）", decision.category, session_id)
            agent_message = repositories.add_message(
                db, session_id, "agent", decision.reason, turn_index=user_message.turn_index
            )
            db.commit()
            yield _sse("token", {"content": decision.reason})
            yield _sse(
                "done",
                {
                    "message": message_out(agent_message).model_dump(mode="json"),
                    "sources": [],
                },
            )
            return

        chunks: list[str] = []
        sources: list[dict] = []
        rolling_summary: str | None = None
        try:
            for event in agent.stream_reply(
                question=session.question,
                lens_key=session.lens,
                history=history,
                user_input=content,
                rolling_summary=session.rolling_summary or "",
            ):
                if event.get("type") == "token":
                    chunks.append(str(event.get("content", "")))
                    yield _sse("token", {"content": str(event.get("content", ""))})
                elif event.get("type") == "done":
                    sources = list(event.get("sources") or [])
                    rolling_summary = event.get("rolling_summary") or None
        except Exception as exc:  # pragma: no cover - 流式中断
            logger.error(
                "流式对话中断（session=%s，已输出 %s 个片段）：%s", session_id, len(chunks), exc, exc_info=True
            )
            try:
                db.rollback()
            except Exception:  # pragma: no cover - 连接已断开时忽略
                logger.debug("流式中断后回滚事务失败（连接可能已关闭）")
            yield _sse("error", {"message": "对话生成中断，请重试", "request_id": None})
            return

        # 注意：这里必须用新名字 agent_content —— 若复用外层的 content，
        # 本赋值会把 content 变成 event_stream 的局部变量，
        # 导致上方 agent.stream_reply(user_input=content) 抛 UnboundLocalError（流式 100% 中断）
        agent_content = "".join(chunks).strip()
        agent_message = repositories.add_message(
            db,
            session_id,
            "agent",
            agent_content,
            sources=sources,
            turn_index=user_message.turn_index,
        )
        repositories.log_retrieval(
            db,
            query=content,
            hits=sources,
            school=session.lens,
            session_id=session_id,
        )
        if rolling_summary and rolling_summary != session.rolling_summary:
            repositories.update_rolling_summary(db, session, rolling_summary)
        db.commit()
        yield _sse(
            "done",
            {
                "message": message_out(agent_message).model_dump(mode="json"),
                "sources": sources,
            },
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
