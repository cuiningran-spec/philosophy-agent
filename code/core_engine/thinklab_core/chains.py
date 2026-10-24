"""RAG 链：检索 → 组装上下文 → LLM → 结构化输出。"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterator, List, Literal, Optional

from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from .config import Settings, get_settings
from .llm import TemplateChatModel, bind_task, intro_for, run_chain, stream_chain
from .memory import DialogueMemory
from .prompts import (
    DIALOGUE_PROMPT,
    FAQ_PROMPT,
    PERSPECTIVES_PROMPT,
    SUMMARY_PROMPT,
    TASK_DIALOGUE,
    TASK_FAQ,
    TASK_PERSPECTIVES,
    TASK_SUMMARY,
)
from .schemas import (
    DialogueResult,
    FaqResult,
    Perspective,
    PerspectivesResult,
    SourceItem,
    SummaryResult,
)

# --------------------------------------------------------------------------
# LLM 结构化输出模型
# --------------------------------------------------------------------------
class LensGeneration(BaseModel):
    key: Literal["stoic", "existential", "taoist"]
    name: str
    en: str
    core_ask: str
    headline: str
    description: str
    quote: str
    thinker: str
    fit_for: str
    opening: str = ""
    retrieved: List[str] = Field(default_factory=list)


class PerspectivesGeneration(BaseModel):
    reading: str
    lenses: List[LensGeneration]


class SummaryGeneration(BaseModel):
    takeaway: str
    insights: List[str] = Field(default_factory=list)
    tensions: List[str] = Field(default_factory=list)
    practices: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# 检索
# --------------------------------------------------------------------------
def _boost(school: Optional[str], metadata: Dict[str, Any]) -> float:
    doc_school = metadata.get("school", "general")
    if school and doc_school == school:
        return 0.18
    if doc_school == "general":
        return 0.06
    return 0.0


def retrieve(
    vectorstore: Any,
    query: str,
    school: Optional[str] = None,
    k: Optional[int] = None,
    settings: Optional[Settings] = None,
) -> List[SourceItem]:
    """向量检索 + 流派加权排序，返回带出处的信息片段。"""
    settings = settings or get_settings()
    top_k = k or settings.retrieval_top_k
    candidates = max(top_k * 3, settings.retrieval_candidate_k)

    raw: List = []
    try:
        raw = vectorstore.similarity_search_with_score(query, k=candidates)
    except Exception:
        docs = vectorstore.similarity_search(query, k=candidates)
        raw = [(doc, 0.0) for doc in docs]

    scored = []
    for doc, score in raw:
        metadata = dict(getattr(doc, "metadata", {}) or {})
        final = float(score) + _boost(school, metadata)
        scored.append((final, float(score), doc, metadata))

    scored.sort(key=lambda item: item[0], reverse=True)
    items: List[SourceItem] = []
    for final, raw_score, doc, metadata in scored[:top_k]:
        if final < settings.retrieval_min_score:
            continue
        content = getattr(doc, "page_content", "") or ""
        items.append(
            SourceItem(
                doc_id=str(metadata.get("doc_id") or metadata.get("faq_id") or ""),
                title=str(metadata.get("title") or metadata.get("question") or "语料片段"),
                school=str(metadata.get("school") or "general"),
                thinker=str(metadata.get("thinker") or ""),
                snippet=content[:220],
                score=round(final, 4),
            )
        )
    return items


def format_context(items: List[SourceItem]) -> str:
    if not items:
        return "（本次没有命中语料，请依靠该哲学视角本身的核心追问来回应。）"
    return "\n\n".join(
        f"[{i + 1}] {item.title}"
        + (f"（{item.thinker}）" if item.thinker else "")
        + f"\n{item.snippet}"
        for i, item in enumerate(items)
    )


def _documents_from_seed() -> List[Document]:
    from .knowledge.seed_docs import seed_documents

    docs = []
    for item in seed_documents():
        docs.append(
            Document(
                page_content=item["content"],
                metadata={
                    "doc_id": item["doc_id"],
                    "title": item["title"],
                    "school": item["school"],
                    "thinker": item.get("thinker", ""),
                    "kind": item.get("kind", ""),
                    "tags": item.get("tags", []),
                },
            )
        )
    return docs


def _faq_documents() -> List[Document]:
    from .knowledge.faq import faq_entries

    docs = []
    for item in faq_entries():
        docs.append(
            Document(
                page_content=f"问：{item['question']}\n答：{item['answer']}",
                metadata={
                    "faq_id": item["faq_id"],
                    "title": item["question"],
                    "school": item.get("school", "general"),
                    "kind": "faq",
                    "tags": item.get("tags", []),
                },
            )
        )
    return docs


def knowledge_documents() -> List[Document]:
    return _documents_from_seed() + _faq_documents()


def ensure_knowledge(vectorstore: Any, rebuild: bool = False) -> int:
    """把种子语料灌入向量库（幂等）。"""
    docs = knowledge_documents()
    already = 0
    try:
        already = vectorstore.count()  # LocalVectorStore
    except Exception:
        already = -1
    if rebuild or already <= 0:  # Pinecone 无 count() 时返回 -1，同样执行灌库
        if rebuild:
            try:
                vectorstore.delete(ids=[d.metadata.get("doc_id") or d.metadata.get("faq_id") for d in docs])
            except Exception:
                pass
        ids = [d.metadata.get("doc_id") or d.metadata.get("faq_id") for d in docs]
        vectorstore.add_documents(docs, ids=ids)
        return len(docs)
    return already


# --------------------------------------------------------------------------
# 链
# --------------------------------------------------------------------------
def _perspectives_chain(llm: Any) -> Runnable:
    parser = PydanticOutputParser(pydantic_object=PerspectivesGeneration)
    return (
        PERSPECTIVES_PROMPT.partial(format_instructions=parser.get_format_instructions())
        | llm
        | parser
    )


def _summary_chain(llm: Any) -> Runnable:
    parser = PydanticOutputParser(pydantic_object=SummaryGeneration)
    return (
        SUMMARY_PROMPT.partial(format_instructions=parser.get_format_instructions()) | llm | parser
    )


def _safe_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return {}
        return {}


def generate_perspectives(
    llm: Any,
    vectorstore: Any,
    question: str,
    settings: Optional[Settings] = None,
) -> PerspectivesResult:
    settings = settings or get_settings()
    ensure_knowledge(vectorstore)
    sources = retrieve(vectorstore, question, k=max(3, settings.retrieval_top_k), settings=settings)
    ctx = {"question": question, "sources": [s.model_dump() for s in sources]}

    payload = {
        "task": TASK_PERSPECTIVES,
        "question": question,
        "context": format_context(sources),
    }
    try:
        result: PerspectivesGeneration = run_chain(
            _perspectives_chain, llm, payload, TASK_PERSPECTIVES, ctx, settings
        )
        lenses_raw = [lens.model_dump() for lens in result.lenses]
        reading = result.reading
    except Exception:
        # 结构化解析失败：取原始文本再尽力解析
        raw = str(
            run_chain(_perspectives_chain, llm, payload, TASK_PERSPECTIVES, ctx, settings)
        )
        parsed = _safe_json(raw)
        reading = parsed.get("reading", "")
        lenses_raw = parsed.get("lenses", [])

    from .lenses import LENS_ORDER, LENS_PROFILES

    perspectives: List[Perspective] = []
    for key in LENS_ORDER:
        profile = LENS_PROFILES[key]
        generated = next((item for item in lenses_raw if item.get("key") == key), {})
        perspectives.append(
            Perspective(
                **profile.model_dump(),
                opening=generated.get("opening") or f"{profile.name}会先问：{profile.core_ask}",
                retrieved=generated.get("retrieved") or [s.title for s in sources[:2]],
            )
        )
    return PerspectivesResult(
        question=question,
        reading=reading,
        lenses=perspectives,
        sources=sources,
        mode=settings.resolved_llm_mode(),
    )


def build_dialogue_chain(llm: Any) -> Runnable:
    return DIALOGUE_PROMPT | llm | StrOutputParser()


def _dialogue_inputs(
    lens_profile: Any,
    question: str,
    user_input: str,
    memory: DialogueMemory,
    sources: List[SourceItem],
) -> Dict[str, Any]:
    return {
        "task": TASK_DIALOGUE,
        "lens_name": lens_profile.name,
        "core_ask": lens_profile.core_ask,
        "tagline": lens_profile.tagline,
        "history": memory.history_messages(),
        "question": question,
        "rolling_summary": memory.rolling_summary or "（暂无）",
        "context": format_context(sources),
        "input": user_input,
    }


def generate_reply(
    llm: Any,
    vectorstore: Any,
    question: str,
    lens_key: str,
    history: List[Dict[str, str]],
    user_input: str,
    rolling_summary: str = "",
    settings: Optional[Settings] = None,
) -> DialogueResult:
    from .lenses import get_lens

    settings = settings or get_settings()
    ensure_knowledge(vectorstore)
    lens_profile = get_lens(lens_key)
    memory = DialogueMemory(history, rolling_summary, settings)

    # 检索时同时带上问题与最新追问，并偏向当前流派语料
    query = f"{question} {user_input}"
    sources = retrieve(vectorstore, query, school=lens_key, settings=settings)

    ctx = {
        "lens": lens_key,
        "input": user_input,
        "turn": memory.user_turns + 1,
        "sources": [s.model_dump() for s in sources],
    }
    inputs = _dialogue_inputs(lens_profile, question, user_input, memory, sources)

    used_summary = bool(memory.rolling_summary)
    try:
        content = run_chain(build_dialogue_chain, llm, inputs, TASK_DIALOGUE, ctx, settings)
    except Exception as exc:
        print(f"[thinklab] 对话链失败，使用本地模板兜底：{exc}")
        content = (
            TemplateChatModel()
            .bind(task=TASK_DIALOGUE, ctx=ctx)
            .invoke([("human", f"{question}\n{user_input}")])
            .content
        )

    new_summary = memory.rolling_summary
    if memory.should_compress():
        new_summary = memory.compress(bind_task(llm, "compress", {"question": question, "lens": lens_key}))
        used_summary = True

    return DialogueResult(
        content=str(content).strip(),
        sources=sources,
        mode=settings.resolved_llm_mode(),
        used_memory_summary=used_summary,
    )


def stream_reply(
    llm: Any,
    vectorstore: Any,
    question: str,
    lens_key: str,
    history: List[Dict[str, str]],
    user_input: str,
    rolling_summary: str = "",
    settings: Optional[Settings] = None,
) -> Iterator[Dict[str, Any]]:
    """流式对话：先产出 token，最后产出 sources 事件。"""
    from .lenses import get_lens

    settings = settings or get_settings()
    ensure_knowledge(vectorstore)
    lens_profile = get_lens(lens_key)
    memory = DialogueMemory(history, rolling_summary, settings)
    sources = retrieve(vectorstore, f"{question} {user_input}", school=lens_key, settings=settings)
    ctx = {
        "lens": lens_key,
        "input": user_input,
        "turn": memory.user_turns + 1,
        "sources": [s.model_dump() for s in sources],
    }
    inputs = _dialogue_inputs(lens_profile, question, user_input, memory, sources)

    try:
        for chunk in stream_chain(build_dialogue_chain, llm, inputs, TASK_DIALOGUE, ctx, settings):
            yield {"type": "token", "content": chunk}
    except Exception as exc:
        print(f"[thinklab] 流式链失败，回退一次性输出：{exc}")
        content = generate_reply(
            llm, vectorstore, question, lens_key, history, user_input, rolling_summary, settings
        )
        yield {"type": "token", "content": content.content}
        sources = content.sources

    new_summary = memory.rolling_summary
    if memory.should_compress():
        new_summary = memory.compress(bind_task(llm, "compress", {"question": question, "lens": lens_key}))
    yield {
        "type": "done",
        "sources": [s.model_dump() for s in sources],
        "rolling_summary": new_summary,
    }


def generate_summary(
    llm: Any,
    vectorstore: Any,
    question: str,
    lens_key: str,
    history: List[Dict[str, str]],
    rolling_summary: str = "",
    settings: Optional[Settings] = None,
) -> SummaryResult:
    from .lenses import get_lens

    settings = settings or get_settings()
    ensure_knowledge(vectorstore)
    lens_profile = get_lens(lens_key)
    memory = DialogueMemory(history, rolling_summary, settings)
    sources = retrieve(vectorstore, question, school=lens_key, settings=settings)

    last_user = ""
    for item in reversed(history):
        if item.get("role") == "user":
            last_user = item.get("content", "")
            break

    ctx = {
        "lens": lens_key,
        "last_user": last_user,
        "sources": [s.model_dump() for s in sources],
    }
    payload = {
        "task": TASK_SUMMARY,
        "question": question,
        "lens_name": lens_profile.name,
        "core_ask": lens_profile.core_ask,
        "transcript": memory.transcript() or "（用户还没有展开追问）",
        "context": format_context(sources),
    }

    try:
        result: SummaryGeneration = run_chain(_summary_chain, llm, payload, TASK_SUMMARY, ctx, settings)
        takeaway = result.takeaway
        insights = result.insights
        tensions = result.tensions
        practices = result.practices
        keywords = result.keywords
    except Exception:
        data = _safe_json(
            str(run_chain(_summary_chain, llm, payload, TASK_SUMMARY, ctx, settings))
        )
        takeaway = data.get("takeaway", "")
        insights = data.get("insights", [])
        tensions = data.get("tensions", [])
        practices = data.get("practices", [])
        keywords = data.get("keywords", [])

    return SummaryResult(
        question=question,
        lens=lens_key,
        lens_name=lens_profile.name,
        core_ask=lens_profile.core_ask,
        tagline=lens_profile.tagline,
        turns=memory.user_turns,
        takeaway=takeaway or f"以「{lens_profile.name}」看这个处境：{lens_profile.tagline}。",
        insights=list(insights)[:3],
        tensions=list(tensions)[:2],
        practices=list(practices)[:3],
        keywords=list(keywords)[:6],
        sources=sources,
        mode=settings.resolved_llm_mode(),
    )


def answer_faq(
    llm: Any,
    vectorstore: Any,
    question: str,
    settings: Optional[Settings] = None,
) -> FaqResult:
    from .knowledge.faq import faq_entries

    settings = settings or get_settings()
    ensure_knowledge(vectorstore)
    sources = retrieve(vectorstore, question, k=settings.retrieval_top_k, settings=settings)

    hits = []
    for entry in faq_entries():
        overlap = sum(1 for ch in set(entry["question"]) if ch in question)
        if entry["question"] == question or overlap >= max(4, len(set(entry["question"])) * 0.5):
            hits.append(entry)
    hits.sort(key=lambda e: len(e["question"]), reverse=False)

    ctx = {"sources": [s.model_dump() for s in sources], "faq_hits": hits[:2]}
    faq_hits_text = "\n".join(f"问：{h['question']}\n答：{h['answer']}" for h in hits[:2]) or "（无）"

    def _faq_chain(bound_llm: Any) -> Runnable:
        return FAQ_PROMPT | bound_llm | StrOutputParser()

    answer = str(
        run_chain(
            _faq_chain,
            llm,
            {
                "task": TASK_FAQ,
                "question": question,
                "context": format_context(sources),
                "faq_hits": faq_hits_text,
            },
            TASK_FAQ,
            ctx,
            settings,
        )
    ).strip()

    return FaqResult(
        question=question,
        answer=answer,
        sources=sources,
        matched=hits[0]["question"] if hits else None,
        mode=settings.resolved_llm_mode(),
    )


def lens_intro(lens_key: str) -> str:
    return intro_for(lens_key)
