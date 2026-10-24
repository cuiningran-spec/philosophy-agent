"""LLM：DeepSeek（生产，OpenAI 兼容协议）/ OpenAI（备用）/ 模板化离线模型（无密钥降级）。

DeepSeek 的对话接口与 OpenAI 兼容（``https://api.deepseek.com``），
因此这里用 ``langchain_openai.ChatOpenAI`` 指向 DeepSeek 的 base_url 接入，
链（prompt | llm | parser）在三种模式下完全一致，只是产出内容不同。
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterator, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from .config import Settings, get_settings
from .lenses import (
    INTROS,
    LENS_ORDER,
    LENS_PROFILES,
    QUICK_REPLIES,
    REPLIES,
    SUMMARY_TEMPLATES,
    get_lens,
    reading_for,
)
from .prompts import (
    TASK_COMPRESS,
    TASK_DIALOGUE,
    TASK_FAQ,
    TASK_PERSPECTIVES,
    TASK_SUMMARY,
)


def _clip(text: str, length: int) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= length else value[:length] + "…"


def _sources_titles(sources: List[Dict]) -> List[str]:
    return [s.get("title", "") for s in sources if s.get("title")]


# --------------------------------------------------------------------------
# 模板化模型
# --------------------------------------------------------------------------
class TemplateChatModel(BaseChatModel):
    """离线可用的确定性模型：按 task 产出结构化 JSON 或自然语言回复。"""

    temperature: float = 0.0

    @property
    def _llm_type(self) -> str:
        return "thinklab-template"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        task = kwargs.get("task", TASK_DIALOGUE)
        ctx: Dict[str, Any] = kwargs.get("ctx") or {}
        content = self._render(task, ctx)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    # ---------------- 各任务的模板实现 ----------------
    def _render(self, task: str, ctx: Dict[str, Any]) -> str:
        if task == TASK_PERSPECTIVES:
            return json.dumps(self._perspectives(ctx), ensure_ascii=False)
        if task == TASK_SUMMARY:
            return json.dumps(self._summary(ctx), ensure_ascii=False)
        if task == TASK_FAQ:
            return self._faq(ctx)
        if task == TASK_COMPRESS:
            return self._compress(ctx)
        return self._dialogue(ctx)

    def _perspectives(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        question = ctx.get("question", "")
        sources = ctx.get("sources", [])
        titles = _sources_titles(sources)[:3]
        reading = reading_for(question)
        lenses = []
        for index, key in enumerate(LENS_ORDER):
            profile = get_lens(key)
            lenses.append(
                {
                    "key": key,
                    "name": profile.name,
                    "en": profile.en,
                    "core_ask": profile.core_ask,
                    "headline": profile.headline,
                    "description": profile.description,
                    "quote": profile.quote,
                    "thinker": profile.thinker,
                    "fit_for": profile.fit_for,
                    "opening": (
                        f"关于「{_clip(question, 28)}」，{profile.name}会先问：{profile.core_ask}"
                    ),
                    "retrieved": titles,
                }
            )
        return {"reading": reading, "lenses": lenses}

    def _dialogue(self, ctx: Dict[str, Any]) -> str:
        lens_key = ctx.get("lens", "stoic")
        text = str(ctx.get("input", "")).strip()
        sources = ctx.get("sources", [])
        prompts = LENS_PROFILES.get(lens_key, LENS_PROFILES["stoic"]).prompts
        turn = int(ctx.get("turn", 1) or 1)

        if text in prompts:
            body = QUICK_REPLIES[lens_key][prompts.index(text)]
        else:
            pool = REPLIES[lens_key]
            body = f"你提到的「{_clip(text, 24)}」，可以再往深处放一放。\n\n" + pool[(turn - 1) % len(pool)]

        if sources:
            top = sources[0]
            body += (
                f"\n\n（这一步借用了知识库中的「{top.get('title', '')}」"
                f"{'· ' + top.get('thinker', '') if top.get('thinker') else ''}）"
            )
        return body

    def _summary(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        lens_key = ctx.get("lens", "stoic")
        profile = get_lens(lens_key)
        template = SUMMARY_TEMPLATES[lens_key]
        last_user = _clip(ctx.get("last_user", ""), 44)
        insights = list(template["insights"])
        if last_user:
            insights[0] = (
                insights[0] + f" 你在对话中提到的「{last_user}」，让这个方向落在了更具体的生活处境里。"
            )
        else:
            insights.insert(
                0,
                "你还没有展开追问。这份记录保留了这次选择的起点，也留下了一条可以随时返回的入口。",
            )
        return {
            "takeaway": f"以「{profile.name}」看这个处境：{profile.tagline}。",
            "insights": insights[:3],
            "tensions": list(template["tensions"]),
            "practices": list(template["practices"]),
            "keywords": [profile.name, profile.core_ask[:8], "思考记录"],
        }

    def _compress(self, ctx: Dict[str, Any]) -> str:
        lens_key = ctx.get("lens", "stoic")
        profile = get_lens(lens_key)
        question = _clip(ctx.get("question", ""), 40)
        return (
            f"用户在「{question}」这一处境中，持续以{profile.name}的视角追问：{profile.core_ask}。"
            f"较早的对话里已出现对事实与判断的区分、对可控范围的确认，以及尚未解开的张力。"
        )

    def _faq(self, ctx: Dict[str, Any]) -> str:
        hits = ctx.get("faq_hits", [])
        if hits:
            return hits[0].get("answer", "")
        sources = ctx.get("sources", [])
        if not sources:
            return "知识库里暂时没有命中相关条目。你可以换个说法，或提出一个更具体的现实处境。"
        top = sources[0]
        return (
            f"知识库中没有完全对应的 FAQ，但语料「{top.get('title', '')}」与此相关："
            f"{_clip(top.get('snippet', ''), 160)}"
        )


# --------------------------------------------------------------------------
# 工厂
# --------------------------------------------------------------------------
def _build_deepseek(settings: Settings):
    """DeepSeek：OpenAI 兼容协议，使用 ChatOpenAI 指向 deepseek_base_url。"""
    from langchain_openai import ChatOpenAI

    kwargs: Dict[str, Any] = {
        "model": settings.deepseek_model,
        "api_key": settings.deepseek_api_key,
        "base_url": settings.deepseek_base_url,
        "temperature": settings.deepseek_temperature,
    }
    if settings.deepseek_max_tokens:
        kwargs["max_tokens"] = settings.deepseek_max_tokens
    return ChatOpenAI(**kwargs)


def _build_openai(settings: Settings):
    from langchain_openai import ChatOpenAI

    kwargs: Dict[str, Any] = {
        "model": settings.openai_model,
        "temperature": settings.openai_temperature,
        "api_key": settings.openai_api_key,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(**kwargs)


def get_llm(settings: Settings | None = None):
    settings = settings or get_settings()
    mode = settings.resolved_llm_mode()

    if mode == "deepseek":
        if not settings.deepseek_api_key:
            print("[thinklab] 未配置 DEEPSEEK_API_KEY，降级模板模型")
            return TemplateChatModel()
        try:
            return _build_deepseek(settings)
        except Exception as exc:  # pragma: no cover
            print(f"[thinklab] DeepSeek 初始化失败，降级模板模型：{exc}")

    elif mode == "openai":
        if not settings.openai_api_key:
            print("[thinklab] 未配置 OPENAI_API_KEY，降级模板模型")
            return TemplateChatModel()
        try:
            return _build_openai(settings)
        except Exception as exc:  # pragma: no cover
            print(f"[thinklab] ChatOpenAI 初始化失败，降级模板模型：{exc}")

    return TemplateChatModel()


class _FallbackNotAvailable(Exception):
    """真实 LLM 调用失败且兜底被关闭时抛出。"""


def _allow_fallback(llm: Any, settings: Settings | None) -> bool:
    settings = settings or get_settings()
    return settings.llm_fallback_enabled and not isinstance(llm, TemplateChatModel)


def run_chain(
    builder: Any,
    llm: Any,
    payload: Dict[str, Any],
    task: str,
    ctx: Dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> Any:
    """执行 ``builder(bound_llm).invoke(payload)``。

    真实 LLM（DeepSeek / OpenAI）调用失败时（网络、鉴权、限流），
    自动改用模板模型兜底，保证对话流程不中断。
    """
    try:
        return builder(bind_task(llm, task, ctx)).invoke(payload)
    except Exception as exc:
        if not _allow_fallback(llm, settings):
            raise
        print(f"[thinklab] LLM 调用失败（{task}），使用模板模型兜底：{exc}")
        return builder(bind_task(TemplateChatModel(), task, ctx)).invoke(payload)


def stream_chain(
    builder: Any,
    llm: Any,
    payload: Dict[str, Any],
    task: str,
    ctx: Dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> Iterator[str]:
    """流式版本：逐块产出文本；真实 LLM 失败时改用模板模型流式输出。"""
    try:
        for chunk in builder(bind_task(llm, task, ctx)).stream(payload):
            if chunk:
                yield str(chunk)
    except Exception as exc:
        if not _allow_fallback(llm, settings):
            raise _FallbackNotAvailable(str(exc)) from exc
        print(f"[thinklab] LLM 流式调用失败（{task}），使用模板模型兜底：{exc}")
        for chunk in builder(bind_task(TemplateChatModel(), task, ctx)).stream(payload):
            if chunk:
                yield str(chunk)


def bind_task(llm: Any, task: str, ctx: Dict[str, Any] | None = None) -> Any:
    """把任务标识与上下文注入模型调用。

    只有模板模型需要这些参数（通过 invoke kwargs 传入 ``_generate``），
    真实 LLM 直接原样返回，避免向 OpenAI 传递多余字段。
    """
    if isinstance(llm, TemplateChatModel):
        return llm.bind(task=task, ctx=ctx or {})
    return llm


def intro_for(lens_key: str) -> str:
    return INTROS.get(lens_key, INTROS["stoic"])
