"""智能体门面：FastAPI 只需要依赖这个类。"""

from __future__ import annotations

import threading
from typing import Any, Dict, Iterator, List, Optional

from . import chains
from .config import Settings, get_settings
from .llm import get_llm
from .schemas import (
    DialogueResult,
    FaqResult,
    LensProfile,
    PerspectivesResult,
    SourceItem,
    SummaryResult,
)
from .vectorstore import get_vectorstore, vectorstore_label


class ThinkLabAgent:
    """知识库检索智能体：RAG + 多轮记忆 + 结构化总结。"""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.llm = get_llm(self.settings)
        self.vectorstore = get_vectorstore(self.settings)
        self.llm_mode = self.settings.resolved_llm_mode()
        self.vectorstore_mode = vectorstore_label(self.vectorstore)

    # ---------------- 视角 ----------------
    def lenses(self) -> List[LensProfile]:
        from .lenses import LENS_ORDER, LENS_PROFILES

        return [LENS_PROFILES[key] for key in LENS_ORDER]

    def read_and_perspectives(self, question: str) -> PerspectivesResult:
        return chains.generate_perspectives(self.llm, self.vectorstore, question, self.settings)

    def intro(self, lens_key: str) -> str:
        return chains.lens_intro(lens_key)

    # ---------------- 对话 ----------------
    def reply(
        self,
        question: str,
        lens_key: str,
        history: List[Dict[str, str]],
        user_input: str,
        rolling_summary: str = "",
    ) -> DialogueResult:
        return chains.generate_reply(
            self.llm,
            self.vectorstore,
            question,
            lens_key,
            history,
            user_input,
            rolling_summary,
            self.settings,
        )

    def stream_reply(
        self,
        question: str,
        lens_key: str,
        history: List[Dict[str, str]],
        user_input: str,
        rolling_summary: str = "",
    ) -> Iterator[Dict[str, Any]]:
        return chains.stream_reply(
            self.llm,
            self.vectorstore,
            question,
            lens_key,
            history,
            user_input,
            rolling_summary,
            self.settings,
        )

    # ---------------- 总结 ----------------
    def summarize(
        self,
        question: str,
        lens_key: str,
        history: List[Dict[str, str]],
        rolling_summary: str = "",
    ) -> SummaryResult:
        return chains.generate_summary(
            self.llm,
            self.vectorstore,
            question,
            lens_key,
            history,
            rolling_summary,
            self.settings,
        )

    # ---------------- FAQ / 检索 ----------------
    def ask_faq(self, question: str) -> FaqResult:
        return chains.answer_faq(self.llm, self.vectorstore, question, self.settings)

    def search(self, query: str, school: Optional[str] = None, k: Optional[int] = None) -> List[SourceItem]:
        chains.ensure_knowledge(self.vectorstore)
        return chains.retrieve(self.vectorstore, query, school=school, k=k, settings=self.settings)

    def ingest(self, rebuild: bool = False) -> Dict[str, Any]:
        count = chains.ensure_knowledge(self.vectorstore, rebuild=rebuild)
        return {
            "documents": count,
            "vectorstore": self.vectorstore_mode,
            "llm": self.llm_mode,
            "rebuilt": rebuild,
        }

    def runtime_info(self) -> Dict[str, Any]:
        return {
            "llm_mode": self.llm_mode,
            "llm_model": self.settings.resolved_llm_model(),
            "llm_base_url": (
                self.settings.deepseek_base_url if self.llm_mode == "deepseek" else None
            ),
            "embedding_provider": self.settings.resolved_embedding_provider(),
            "vectorstore": self.vectorstore_mode,
            "pinecone_index": (
                self.settings.pinecone_index if self.vectorstore_mode == "pinecone" else None
            ),
            "top_k": self.settings.retrieval_top_k,
            "memory_window_turns": self.settings.memory_window_turns,
            "memory_compress_turns": self.settings.memory_compress_turns,
        }


_AGENT: Optional[ThinkLabAgent] = None
_LOCK = threading.Lock()


def get_agent() -> ThinkLabAgent:
    global _AGENT
    with _LOCK:
        if _AGENT is None:
            _AGENT = ThinkLabAgent()
        return _AGENT
