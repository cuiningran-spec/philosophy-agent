"""智能体内核对外的数据结构（与 FastAPI schema 一一对应）。"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

LensKey = Literal["stoic", "existential", "taoist"]


class LensProfile(BaseModel):
    """一种哲学视角的静态画像（不随问题变化）。"""

    key: LensKey
    name: str
    en: str
    icon: str = "lucide:compass"
    accent: str = "#43563f"
    soft: str = "#e8ece0"
    line: str = "#bfc9b8"
    tagline: str
    core_ask: str
    headline: str
    description: str
    quote: str
    thinker: str
    fit_for: str
    thinkers: List[str] = Field(default_factory=list)
    prompts: List[str] = Field(default_factory=list)


class Perspective(LensProfile):
    """针对某个具体问题生成的视角（在 LensProfile 上叠加动态内容）。"""

    opening: str = ""          # 该视角对这个问题的第一句追问
    retrieved: List[str] = Field(default_factory=list)  # 命中的知识库条目标题


class SourceItem(BaseModel):
    """一次检索命中的知识库片段，用于在界面上展示出处。"""

    doc_id: str
    title: str
    school: str = "general"
    thinker: str = ""
    snippet: str = ""
    score: float = 0.0


class PerspectivesResult(BaseModel):
    question: str
    reading: str                       # Agent 对问题的初步阅读
    lenses: List[Perspective]
    sources: List[SourceItem] = Field(default_factory=list)
    mode: str = "template"


class DialogueResult(BaseModel):
    content: str
    sources: List[SourceItem] = Field(default_factory=list)
    mode: str = "template"
    used_memory_summary: bool = False


class SummaryResult(BaseModel):
    question: str
    lens: str
    lens_name: str
    core_ask: str
    tagline: str
    turns: int = 0
    takeaway: str = ""
    insights: List[str] = Field(default_factory=list)
    tensions: List[str] = Field(default_factory=list)
    practices: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    sources: List[SourceItem] = Field(default_factory=list)
    mode: str = "template"


class FaqResult(BaseModel):
    question: str
    answer: str
    sources: List[SourceItem] = Field(default_factory=list)
    matched: Optional[str] = None
    mode: str = "template"
