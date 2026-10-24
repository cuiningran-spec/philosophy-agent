"""数据访问层：所有 SQL 都集中在这里。"""

from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models
from .db import new_id


# ---------------- sessions ----------------
def create_session(db: Session, question: str) -> models.ExplorationSession:
    session = models.ExplorationSession(id=new_id("s_"), question=question.strip())
    db.add(session)
    db.flush()
    return session


def get_session(db: Session, session_id: str) -> Optional[models.ExplorationSession]:
    return db.get(models.ExplorationSession, session_id)


def list_sessions(db: Session, limit: int = 30) -> List[models.ExplorationSession]:
    stmt = select(models.ExplorationSession).order_by(models.ExplorationSession.created_at.desc()).limit(limit)
    return list(db.scalars(stmt))


def set_lens(
    db: Session,
    session: models.ExplorationSession,
    lens_key: str,
    lens_name: str,
    core_ask: str,
) -> models.ExplorationSession:
    session.lens = lens_key
    session.lens_name = lens_name
    session.core_ask = core_ask
    db.flush()
    return session


def update_rolling_summary(db: Session, session: models.ExplorationSession, text: str) -> None:
    session.rolling_summary = text
    db.flush()


# ---------------- perspectives ----------------
def save_perspectives(
    db: Session, session_id: str, lenses: List[Dict]
) -> List[models.Perspective]:
    rows: List[models.Perspective] = []
    for index, lens in enumerate(lenses):
        row = models.Perspective(
            id=new_id("p_"),
            session_id=session_id,
            key=lens.get("key", ""),
            name=lens.get("name", ""),
            en=lens.get("en", ""),
            core_ask=lens.get("core_ask", ""),
            headline=lens.get("headline", ""),
            description=lens.get("description", ""),
            quote=lens.get("quote", ""),
            thinker=lens.get("thinker", ""),
            fit_for=lens.get("fit_for", ""),
            opening=lens.get("opening", ""),
            retrieved=list(lens.get("retrieved", [])),
            order_index=index,
        )
        db.add(row)
        rows.append(row)
    db.flush()
    return rows


def list_perspectives(db: Session, session_id: str) -> List[models.Perspective]:
    stmt = (
        select(models.Perspective)
        .where(models.Perspective.session_id == session_id)
        .order_by(models.Perspective.order_index)
    )
    return list(db.scalars(stmt))


# ---------------- messages ----------------
def _next_seq(db: Session, session_id: str) -> int:
    stmt = select(func.coalesce(func.max(models.Message.seq), 0)).where(
        models.Message.session_id == session_id
    )
    return int(db.scalar(stmt) or 0) + 1


def _next_turn(db: Session, session_id: str) -> int:
    stmt = select(func.count(models.Message.id)).where(
        models.Message.session_id == session_id, models.Message.role == "user"
    )
    return int(db.scalar(stmt) or 0) + 1


def add_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    sources: Optional[List[Dict]] = None,
    turn_index: Optional[int] = None,
) -> models.Message:
    message = models.Message(
        id=new_id("m_"),
        session_id=session_id,
        role=role,
        content=content,
        turn_index=turn_index if turn_index is not None else _next_turn(db, session_id),
        seq=_next_seq(db, session_id),
        sources=sources or None,
    )
    db.add(message)
    db.flush()
    return message


def list_messages(db: Session, session_id: str) -> List[models.Message]:
    stmt = (
        select(models.Message)
        .where(models.Message.session_id == session_id)
        .order_by(models.Message.seq)
    )
    return list(db.scalars(stmt))


def history_for_agent(db: Session, session_id: str) -> List[Dict[str, str]]:
    return [
        {"role": m.role, "content": m.content}
        for m in list_messages(db, session_id)
    ]


def user_turn_count(db: Session, session_id: str) -> int:
    stmt = select(func.count(models.Message.id)).where(
        models.Message.session_id == session_id, models.Message.role == "user"
    )
    return int(db.scalar(stmt) or 0)


# ---------------- summaries ----------------
def create_summary(
    db: Session,
    session_id: str,
    payload: Dict,
    excerpts: List[Dict],
) -> models.ThinkingSummary:
    stmt = select(func.coalesce(func.max(models.ThinkingSummary.version), 0)).where(
        models.ThinkingSummary.session_id == session_id
    )
    version = int(db.scalar(stmt) or 0) + 1
    row = models.ThinkingSummary(
        id=new_id("r_"),
        session_id=session_id,
        version=version,
        question=payload.get("question", ""),
        lens=payload.get("lens", ""),
        lens_name=payload.get("lens_name", ""),
        core_ask=payload.get("core_ask", ""),
        tagline=payload.get("tagline", ""),
        turns=int(payload.get("turns", 0) or 0),
        takeaway=payload.get("takeaway", ""),
        insights=list(payload.get("insights", [])),
        tensions=list(payload.get("tensions", [])),
        practices=list(payload.get("practices", [])),
        keywords=list(payload.get("keywords", [])),
        excerpts=excerpts,
        sources=list(payload.get("sources", [])),
    )
    db.add(row)
    db.flush()
    return row


def get_summary(db: Session, summary_id: str) -> Optional[models.ThinkingSummary]:
    return db.get(models.ThinkingSummary, summary_id)


def list_summaries(db: Session, session_id: str) -> List[models.ThinkingSummary]:
    stmt = (
        select(models.ThinkingSummary)
        .where(models.ThinkingSummary.session_id == session_id)
        .order_by(models.ThinkingSummary.version)
    )
    return list(db.scalars(stmt))


def count_summaries(db: Session, session_id: str) -> int:
    stmt = select(func.count(models.ThinkingSummary.id)).where(
        models.ThinkingSummary.session_id == session_id
    )
    return int(db.scalar(stmt) or 0)


# ---------------- knowledge / faq ----------------
def upsert_knowledge_doc(db: Session, doc: Dict) -> None:
    existing = db.scalar(
        select(models.KnowledgeDoc).where(models.KnowledgeDoc.doc_id == doc["doc_id"])
    )
    if existing:
        existing.title = doc["title"]
        existing.school = doc.get("school", "general")
        existing.thinker = doc.get("thinker", "")
        existing.kind = doc.get("kind", "")
        existing.content = doc["content"]
        existing.tags = list(doc.get("tags", []))
    else:
        db.add(
            models.KnowledgeDoc(
                id=new_id("k_"),
                doc_id=doc["doc_id"],
                title=doc["title"],
                school=doc.get("school", "general"),
                thinker=doc.get("thinker", ""),
                kind=doc.get("kind", ""),
                content=doc["content"],
                tags=list(doc.get("tags", [])),
            )
        )
    db.flush()


def upsert_faq_entry(db: Session, entry: Dict) -> None:
    existing = db.scalar(
        select(models.FaqEntry).where(models.FaqEntry.faq_id == entry["faq_id"])
    )
    if existing:
        existing.question = entry["question"]
        existing.answer = entry["answer"]
        existing.school = entry.get("school", "general")
        existing.tags = list(entry.get("tags", []))
    else:
        db.add(
            models.FaqEntry(
                id=new_id("f_"),
                faq_id=entry["faq_id"],
                question=entry["question"],
                answer=entry["answer"],
                school=entry.get("school", "general"),
                tags=list(entry.get("tags", [])),
            )
        )
    db.flush()


def list_knowledge_docs(db: Session, school: Optional[str] = None, limit: int = 100):
    stmt = select(models.KnowledgeDoc).order_by(models.KnowledgeDoc.doc_id).limit(limit)
    if school:
        stmt = stmt.where(models.KnowledgeDoc.school == school)
    return list(db.scalars(stmt))


def list_faq_entries(db: Session, limit: int = 100):
    stmt = select(models.FaqEntry).order_by(models.FaqEntry.faq_id).limit(limit)
    return list(db.scalars(stmt))


# ---------------- retrieval log ----------------
def log_retrieval(
    db: Session,
    query: str,
    hits: List[Dict],
    school: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    db.add(
        models.RetrievalLog(
            id=new_id("l_"),
            session_id=session_id,
            query=query,
            school=school,
            hits=hits,
        )
    )
    db.flush()
