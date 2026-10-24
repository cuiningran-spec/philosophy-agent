"""FastAPI 输入输出模型。"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SourceItem(BaseModel):
    doc_id: str = ""
    title: str = ""
    school: str = "general"
    thinker: str = ""
    snippet: str = ""
    score: float = 0.0


class LensOut(BaseModel):
    key: str
    name: str
    en: str = ""
    icon: str = "lucide:compass"
    accent: str = "#43563f"
    soft: str = "#e8ece0"
    line: str = "#bfc9b8"
    tagline: str = ""
    core_ask: str = ""
    headline: str = ""
    description: str = ""
    quote: str = ""
    thinker: str = ""
    fit_for: str = ""
    thinkers: List[str] = Field(default_factory=list)
    prompts: List[str] = Field(default_factory=list)
    opening: str = ""
    retrieved: List[str] = Field(default_factory=list)


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    turn_index: int = 0
    seq: int = 0
    created_at: Optional[datetime] = None
    sources: List[SourceItem] = Field(default_factory=list)


class SessionOut(BaseModel):
    id: str
    question: str
    lens: Optional[str] = None
    lens_name: Optional[str] = None
    core_ask: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    turn_count: int = 0
    summary_count: int = 0


class SessionDetail(SessionOut):
    perspectives: List[LensOut] = Field(default_factory=list)
    messages: List[MessageOut] = Field(default_factory=list)
    latest_summary_id: Optional[str] = None
    reading: str = ""


class CreateSessionIn(BaseModel):
    question: str = Field(..., min_length=2, max_length=300)


class SelectLensIn(BaseModel):
    lens: str = Field(..., pattern="^(stoic|existential|taoist)$")
    keep_history: bool = True


class SendMessageIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    stream: bool = False


class SendMessageOut(BaseModel):
    user_message: MessageOut
    agent_message: MessageOut
    rolling_summary_updated: bool = False


class SummaryOut(BaseModel):
    id: str
    session_id: str
    version: int
    question: str
    lens: str
    lens_name: str
    core_ask: str = ""
    tagline: str = ""
    turns: int = 0
    takeaway: str = ""
    insights: List[str] = Field(default_factory=list)
    tensions: List[str] = Field(default_factory=list)
    practices: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    excerpts: List[dict] = Field(default_factory=list)
    sources: List[SourceItem] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class FaqAskIn(BaseModel):
    question: str = Field(..., min_length=2, max_length=300)


class FaqAskOut(BaseModel):
    question: str
    answer: str
    matched: Optional[str] = None
    sources: List[SourceItem] = Field(default_factory=list)
    mode: str = "template"


class FaqEntryOut(BaseModel):
    faq_id: str
    question: str
    answer: str
    school: str = "general"
    tags: List[str] = Field(default_factory=list)


class KnowledgeDocOut(BaseModel):
    doc_id: str
    title: str
    school: str = "general"
    thinker: str = ""
    kind: str = ""
    content: str
    tags: List[str] = Field(default_factory=list)


class IngestOut(BaseModel):
    documents: int
    vectorstore: str
    llm: str
    rebuilt: bool


class HealthOut(BaseModel):
    status: str
    database: str
    agent: dict
