"""知识库：视角画像、语义检索、灌库、FAQ 问答。"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from thinklab_core.knowledge.faq import faq_entries
from thinklab_core.knowledge.seed_docs import seed_documents

from .. import repositories
from ..deps import get_ai_agent, get_db
from ..schemas import (
    FaqAskIn,
    FaqAskOut,
    FaqEntryOut,
    IngestOut,
    KnowledgeDocOut,
    LensOut,
    SourceItem,
)
from ..serializers import source_item

router = APIRouter(tags=["knowledge"])


@router.get("/lenses", response_model=List[LensOut])
def list_lenses(agent=Depends(get_ai_agent)):
    """三种哲学视角的画像（配色 / 核心追问 / 推荐追问）。"""
    return [
        LensOut(**profile.model_dump(), opening="", retrieved=[])
        for profile in agent.lenses()
    ]


@router.get("/kb/search", response_model=List[SourceItem])
def search_knowledge(
    q: str,
    school: Optional[str] = None,
    k: int = 4,
    db: Session = Depends(get_db),
    agent=Depends(get_ai_agent),
):
    """知识库语义检索（调试与可解释性展示用）。"""
    items = agent.search(q, school=school, k=k)
    repositories.log_retrieval(db, query=q, hits=[i.model_dump() for i in items], school=school)
    db.commit()
    return items


@router.post("/kb/ingest", response_model=IngestOut)
def ingest_knowledge(
    rebuild: bool = False,
    db: Session = Depends(get_db),
    agent=Depends(get_ai_agent),
):
    """把种子语料与 FAQ 灌入向量库，并同步到 PostgreSQL 便于审计。"""
    try:
        result = agent.ingest(rebuild=rebuild)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"灌库失败：{exc}")

    for doc in seed_documents():
        repositories.upsert_knowledge_doc(db, doc)
    for entry in faq_entries():
        repositories.upsert_faq_entry(db, entry)
    db.commit()
    return IngestOut(**result)


@router.get("/kb/docs", response_model=List[KnowledgeDocOut])
def list_knowledge_docs(school: Optional[str] = None, db: Session = Depends(get_db)):
    rows = repositories.list_knowledge_docs(db, school=school)
    if not rows:  # 数据库为空时用种子语料兜底展示
        return [
            KnowledgeDocOut(
                doc_id=d["doc_id"],
                title=d["title"],
                school=d["school"],
                thinker=d.get("thinker", ""),
                kind=d.get("kind", ""),
                content=d["content"],
                tags=d.get("tags", []),
            )
            for d in seed_documents()
            if not school or d["school"] == school
        ]
    return [
        KnowledgeDocOut(
            doc_id=r.doc_id,
            title=r.title,
            school=r.school,
            thinker=r.thinker,
            kind=r.kind,
            content=r.content,
            tags=r.tags or [],
        )
        for r in rows
    ]


@router.get("/faq", response_model=List[FaqEntryOut])
def list_faq(db: Session = Depends(get_db)):
    rows = repositories.list_faq_entries(db)
    if rows:
        return [
            FaqEntryOut(
                faq_id=r.faq_id, question=r.question, answer=r.answer, school=r.school, tags=r.tags or []
            )
            for r in rows
        ]
    return [
        FaqEntryOut(
            faq_id=e["faq_id"],
            question=e["question"],
            answer=e["answer"],
            school=e.get("school", "general"),
            tags=e.get("tags", []),
        )
        for e in faq_entries()
    ]


@router.post("/faq/ask", response_model=FaqAskOut)
def ask_faq(
    payload: FaqAskIn,
    db: Session = Depends(get_db),
    agent=Depends(get_ai_agent),
):
    """FAQ 问答：先做知识库检索，再让 Agent 组织答案。"""
    result = agent.ask_faq(payload.question)
    repositories.log_retrieval(db, query=payload.question, hits=[s.model_dump() for s in result.sources])
    db.commit()
    return FaqAskOut(
        question=result.question,
        answer=result.answer,
        matched=result.matched,
        sources=[source_item(s.model_dump()) for s in result.sources],
        mode=result.mode,
    )
