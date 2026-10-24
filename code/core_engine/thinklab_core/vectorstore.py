"""向量库：Pinecone（生产） / 本地 JSON 向量索引（降级）。"""

from __future__ import annotations

import json
import math
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from .config import Settings, get_settings
from .embeddings import build_embeddings

_LOCK = threading.Lock()
_STORE_CACHE: Dict[str, Any] = {}


class LocalVectorStore(VectorStore):
    """纯 Python 实现的本地向量库（余弦相似度），可持久化到 JSON 文件。

    用于未配置 Pinecone 时的完整降级：接口与 LangChain VectorStore 一致，
    因此上层检索 / 灌库代码无需分支。
    """

    def __init__(
        self,
        embeddings: Embeddings,
        persist_path: Optional[str] = None,
        namespace: str = "default",
    ):
        self._embeddings = embeddings
        self.namespace = namespace
        self.persist_path = Path(persist_path) if persist_path else None
        self._records: List[Dict[str, Any]] = []
        self._load()

    # ---------------- 持久化 ----------------
    def _load(self) -> None:
        if not self.persist_path or not self.persist_path.exists():
            return
        try:
            raw = json.loads(self.persist_path.read_text(encoding="utf-8"))
        except Exception:
            return
        if isinstance(raw, dict) and raw.get("namespace") == self.namespace:
            self._records = raw.get("records", [])

    def save(self) -> None:
        if not self.persist_path:
            return
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        self.persist_path.write_text(
            json.dumps(
                {"namespace": self.namespace, "records": self._records},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def clear(self) -> None:
        self._records = []
        self.save()

    # ---------------- LangChain 接口 ----------------
    @property
    def embeddings(self) -> Embeddings:  # type: ignore[override]
        return self._embeddings

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> List[str]:
        texts = list(texts)
        metadatas = list(metadatas or [{}])
        ids = list(ids or [])
        vectors = self._embeddings.embed_documents(texts)
        new_ids: List[str] = []
        for index, text in enumerate(texts):
            doc_id = ids[index] if index < len(ids) and ids[index] else f"doc-{len(self._records)}-{index}"
            metadata = dict(metadatas[index] if index < len(metadatas) else {})
            self._drop(doc_id)
            self._records.append(
                {"id": doc_id, "text": text, "metadata": metadata, "vector": vectors[index]}
            )
            new_ids.append(doc_id)
        self.save()
        return new_ids

    def _drop(self, doc_id: str) -> None:
        self._records = [r for r in self._records if r.get("id") != doc_id]

    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> "LocalVectorStore":
        store = cls(embedding, persist_path=kwargs.get("persist_path"))
        store.add_texts(texts, metadatas=metadatas)
        return store

    def _cosine(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(y * y for y in b)) or 1.0
        return dot / (na * nb)

    def _match(self, metadata: dict, where: Optional[dict]) -> bool:
        if not where:
            return True
        for key, value in where.items():
            if metadata.get(key) != value:
                return False
        return True

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        query_vec = self._embeddings.embed_query(query)
        scored: List[Tuple[Document, float]] = []
        for record in self._records:
            if not self._match(record.get("metadata", {}), filter):
                continue
            score = self._cosine(query_vec, record.get("vector", []))
            scored.append(
                (
                    Document(
                        page_content=record.get("text", ""),
                        metadata=dict(record.get("metadata", {})),
                    ),
                    score,
                )
            )
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:k]

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
        **kwargs: Any,
    ) -> List[Document]:
        return [doc for doc, _ in self.similarity_search_with_score(query, k=k, filter=filter)]

    def delete(self, ids: Optional[List[str]] = None, **kwargs: Any) -> Optional[bool]:
        for doc_id in ids or []:
            self._drop(doc_id)
        self.save()
        return True

    def count(self) -> int:
        return len(self._records)


def _default_local_path(settings: Settings) -> Path:
    if settings.local_index_path:
        return Path(settings.local_index_path)
    here = Path(__file__).resolve().parents[1]
    return here / ".cache" / "local_vectorstore.json"


def _build_pinecone(settings: Settings, embeddings: Embeddings, namespace: str):
    from langchain_pinecone import PineconeVectorStore

    try:
        from pinecone import Pinecone, ServerlessSpec

        pc = Pinecone(api_key=settings.pinecone_api_key)
        existing = {idx["name"] for idx in pc.list_indexes().get("indexes", [])}
        if settings.pinecone_index not in existing:
            pc.create_index(
                name=settings.pinecone_index,
                dimension=settings.pinecone_dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
            )
    except Exception as exc:  # pragma: no cover - 索引已存在或权限受限
        print(f"[thinklab] Pinecone 索引初始化跳过：{exc}")

    return PineconeVectorStore(
        index_name=settings.pinecone_index,
        embedding=embeddings,
        namespace=namespace,
    )


def get_vectorstore(settings: Settings | None = None, namespace: str | None = None):
    """按配置返回 Pinecone 或本地向量库（结果缓存）。"""
    settings = settings or get_settings()
    ns = namespace or settings.pinecone_namespace
    mode = settings.resolved_vectorstore_mode()
    cache_key = f"{mode}:{ns}"
    with _LOCK:
        if cache_key in _STORE_CACHE:
            return _STORE_CACHE[cache_key]

        embeddings = build_embeddings(settings)
        if mode == "pinecone":
            try:
                store = _build_pinecone(settings, embeddings, ns)
            except Exception as exc:  # pragma: no cover - 密钥无效时降级
                print(f"[thinklab] Pinecone 不可用，降级本地向量库：{exc}")
                store = LocalVectorStore(
                    embeddings, persist_path=str(_default_local_path(settings)), namespace=ns
                )
        else:
            store = LocalVectorStore(
                embeddings, persist_path=str(_default_local_path(settings)), namespace=ns
            )
        _STORE_CACHE[cache_key] = store
        return store


def reset_vectorstore_cache() -> None:
    with _LOCK:
        _STORE_CACHE.clear()


def vectorstore_label(store: Any) -> str:
    return "pinecone" if not isinstance(store, LocalVectorStore) else "local"
