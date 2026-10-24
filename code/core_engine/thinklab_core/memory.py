"""多轮对话记忆：近期窗口 + 滚动摘要压缩。

近期若干轮原样进入提示词，更早的内容压缩为一段“滚动摘要”并持久化到数据库，
从而实现长对话下的上下文不丢失、也不无限膨胀。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:  # LangChain 记忆组件（langchain 包可用时使用）
    from langchain_core.chat_history import InMemoryChatMessageHistory
    from langchain.memory import (
        ConversationBufferWindowMemory,
        ConversationSummaryMemory,
    )

    _HAS_LANGCHAIN_MEMORY = True
except Exception:  # pragma: no cover - 依赖缺失时走内部实现
    _HAS_LANGCHAIN_MEMORY = False

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from .config import Settings, get_settings

SUMMARY_PROMPT = (
    "请把下面这段哲学对话压缩成 120 字以内的中文摘要，保留：用户的核心处境、"
    "已经形成的理解、尚未解开的张力、以及用户真正在意的东西。\n\n"
    "已有摘要：{existing}\n\n对话：\n{transcript}\n\n摘要："
)


def _to_message(item: Dict[str, str]) -> BaseMessage:
    role = item.get("role", "user")
    content = item.get("content", "")
    return HumanMessage(content=content) if role == "user" else AIMessage(content=content)


class DialogueMemory:
    """把数据库里的消息列表转成可用于提示词的记忆对象。"""

    def __init__(
        self,
        history: Optional[List[Dict[str, str]]] = None,
        rolling_summary: str = "",
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.history: List[Dict[str, str]] = list(history or [])
        self.rolling_summary = rolling_summary or ""
        self.window = max(1, self.settings.memory_window_turns)
        self._window_memory = None
        if _HAS_LANGCHAIN_MEMORY:
            chat_history = InMemoryChatMessageHistory()
            for item in self.history:
                chat_history.add_message(_to_message(item))
            self._window_memory = ConversationBufferWindowMemory(
                k=self.window * 2,  # 一轮 = user + agent 两条
                chat_memory=chat_history,
                return_messages=True,
                memory_key="history",
            )

    # ---------------- 上下文 ----------------
    def history_messages(self) -> List[BaseMessage]:
        """送入 MessagesPlaceholder 的近期消息。"""
        if self._window_memory is not None:
            return self._window_memory.load_memory_variables({}).get("history", [])
        recent = self.history[-(self.window * 2) :]
        return [_to_message(item) for item in recent]

    def transcript(self, limit: int = 40) -> str:
        lines = []
        for item in self.history[-limit:]:
            speaker = "用户" if item.get("role") == "user" else "Agent"
            lines.append(f"{speaker}：{item.get('content', '')}")
        return "\n".join(lines)

    # ---------------- 记忆压缩 ----------------
    def should_compress(self) -> bool:
        user_turns = sum(1 for item in self.history if item.get("role") == "user")
        return user_turns > self.settings.memory_compress_turns

    def compress(self, llm: Any) -> str:
        """用 LLM 把较早的对话压缩成滚动摘要（失败时保留旧摘要）。"""
        keep = self.window * 2
        older = self.history[:-keep] if len(self.history) > keep else []
        if not older and not self.rolling_summary:
            return self.rolling_summary
        transcript = "\n".join(
            f"{'用户' if i.get('role') == 'user' else 'Agent'}：{i.get('content', '')}"
            for i in (older or self.history[-keep:])
        )
        try:
            if _HAS_LANGCHAIN_MEMORY:
                memory = ConversationSummaryMemory(llm=llm, memory_key="history")
                predictor = getattr(memory, "predict_new_summary", None)
                if callable(predictor):
                    messages = [_to_message(i) for i in (older or self.history)]
                    return str(predictor(messages, self.rolling_summary))
            prompt = SUMMARY_PROMPT.format(existing=self.rolling_summary or "（无）", transcript=transcript)
            return str(llm.invoke(prompt).content).strip()
        except Exception:
            return self.rolling_summary

    @property
    def user_turns(self) -> int:
        return sum(1 for item in self.history if item.get("role") == "user")
