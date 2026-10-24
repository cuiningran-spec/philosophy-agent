"""ORM → Pydantic 的转换。"""

from __future__ import annotations

from typing import Dict, List

from . import models
from .schemas import LensOut, MessageOut, SessionDetail, SessionOut, SourceItem, SummaryOut


def source_item(data: Dict) -> SourceItem:
    return SourceItem(
        doc_id=str(data.get("doc_id", "") or ""),
        title=str(data.get("title", "") or ""),
        school=str(data.get("school", "general") or "general"),
        thinker=str(data.get("thinker", "") or ""),
        snippet=str(data.get("snippet", "") or ""),
        score=float(data.get("score", 0.0) or 0.0),
    )


def sources_of(raw) -> List[SourceItem]:
    return [source_item(item) for item in (raw or []) if isinstance(item, dict)]


def message_out(message: models.Message) -> MessageOut:
    return MessageOut(
        id=message.id,
        role=message.role,
        content=message.content,
        turn_index=message.turn_index,
        seq=message.seq,
        created_at=message.created_at,
        sources=sources_of(message.sources),
    )


def lens_out(lens: models.Perspective) -> LensOut:
    from thinklab_core.lenses import LENS_PROFILES

    profile = LENS_PROFILES.get(lens.key)
    return LensOut(
        key=lens.key,
        name=lens.name,
        en=lens.en,
        icon=profile.icon if profile else "lucide:compass",
        accent=profile.accent if profile else "#43563f",
        soft=profile.soft if profile else "#e8ece0",
        line=profile.line if profile else "#bfc9b8",
        tagline=profile.tagline if profile else "",
        core_ask=lens.core_ask,
        headline=lens.headline,
        description=lens.description,
        quote=lens.quote,
        thinker=lens.thinker,
        fit_for=lens.fit_for,
        thinkers=list(profile.thinkers) if profile else [],
        prompts=list(profile.prompts) if profile else [],
        opening=lens.opening,
        retrieved=list(lens.retrieved or []),
    )


def session_out(session: models.ExplorationSession, db=None) -> SessionOut:
    turn_count = 0
    summary_count = 0
    if db is not None:
        from . import repositories

        turn_count = repositories.user_turn_count(db, session.id)
        summary_count = repositories.count_summaries(db, session.id)
    return SessionOut(
        id=session.id,
        question=session.question,
        lens=session.lens,
        lens_name=session.lens_name,
        core_ask=session.core_ask,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        turn_count=turn_count,
        summary_count=summary_count,
    )


def summary_out(row: models.ThinkingSummary) -> SummaryOut:
    return SummaryOut(
        id=row.id,
        session_id=row.session_id,
        version=row.version,
        question=row.question,
        lens=row.lens,
        lens_name=row.lens_name,
        core_ask=row.core_ask,
        tagline=row.tagline,
        turns=row.turns,
        takeaway=row.takeaway,
        insights=list(row.insights or []),
        tensions=list(row.tensions or []),
        practices=list(row.practices or []),
        keywords=list(row.keywords or []),
        excerpts=list(row.excerpts or []),
        sources=sources_of(row.sources),
        created_at=row.created_at,
    )


def session_detail(
    session: models.ExplorationSession,
    perspectives: List[models.Perspective],
    messages: List[models.Message],
    summaries,
    db=None,
    reading: str = "",
) -> SessionDetail:
    base = session_out(session, db)
    return SessionDetail(
        **base.model_dump(),
        perspectives=[lens_out(p) for p in perspectives],
        messages=[message_out(m) for m in messages],
        latest_summary_id=summaries[-1].id if summaries else None,
        reading=reading,
    )
