"""PostgreSQL 数据模型（SQLAlchemy ORM）。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base, new_id


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ExplorationSession(Base, TimestampMixin):
    """一次探索：一个现实问题 + 一个被选中的哲学视角。"""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("s_"))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    lens: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lens_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    core_ask: Mapped[str | None] = mapped_column(Text, nullable=True)
    rolling_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # 长对话滚动摘要
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="Message.seq"
    )
    perspectives: Mapped[list["Perspective"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="Perspective.order_index"
    )
    summaries: Mapped[list["ThinkingSummary"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ThinkingSummary.version"
    )


class Perspective(Base, TimestampMixin):
    """某次探索下生成的一种哲学视角（含该视角对这个问题的 opening）。"""

    __tablename__ = "perspectives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("p_"))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    key: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    en: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    core_ask: Mapped[str] = mapped_column(Text, default="", nullable=False)
    headline: Mapped[str] = mapped_column(Text, default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    quote: Mapped[str] = mapped_column(Text, default="", nullable=False)
    thinker: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    fit_for: Mapped[str] = mapped_column(Text, default="", nullable=False)
    opening: Mapped[str] = mapped_column(Text, default="", nullable=False)
    retrieved: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    session: Mapped[ExplorationSession] = relationship(back_populates="perspectives")


class Message(Base, TimestampMixin):
    """对话消息（user / agent），带检索出处与序号。"""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("m_"))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    turn_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    seq: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sources: Mapped[list | None] = mapped_column(JSON, nullable=True)

    session: Mapped[ExplorationSession] = relationship(back_populates="messages")


class ThinkingSummary(Base, TimestampMixin):
    """结构化思考记录（可多次生成，version 递增）。"""

    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("r_"))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    lens: Mapped[str] = mapped_column(String(32), nullable=False)
    lens_name: Mapped[str] = mapped_column(String(64), nullable=False)
    core_ask: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tagline: Mapped[str] = mapped_column(Text, default="", nullable=False)
    turns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    takeaway: Mapped[str] = mapped_column(Text, default="", nullable=False)
    insights: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    tensions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    practices: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    keywords: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    excerpts: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    sources: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    session: Mapped[ExplorationSession] = relationship(back_populates="summaries")


class KnowledgeDoc(Base, TimestampMixin):
    """知识库文档（与向量库中的 doc_id 一一对应，便于审计与后台管理）。"""

    __tablename__ = "knowledge_docs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("k_"))
    doc_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    school: Mapped[str] = mapped_column(String(32), default="general", index=True, nullable=False)
    thinker: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    kind: Mapped[str] = mapped_column(String(32), default="concept", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)


class FaqEntry(Base, TimestampMixin):
    """FAQ 条目。"""

    __tablename__ = "faq_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("f_"))
    faq_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    school: Mapped[str] = mapped_column(String(32), default="general", nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)


class RetrievalLog(Base, TimestampMixin):
    """检索审计：记录每次问答命中了哪些语料。"""

    __tablename__ = "retrieval_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: new_id("l_"))
    session_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    school: Mapped[str | None] = mapped_column(String(32), nullable=True)
    hits: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
