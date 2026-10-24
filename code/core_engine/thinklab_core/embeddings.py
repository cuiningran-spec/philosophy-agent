"""Embeddings：OpenAI（生产） / 本地哈希向量（无密钥降级）。

注意：DeepSeek 目前只提供对话模型、不提供 embedding 接口，
因此向量化独立于 LLM 提供方单独配置。
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import List

from langchain_core.embeddings import Embeddings

from .config import Settings, get_settings


class HashingEmbeddings(Embeddings):
    """无密钥时的确定性向量：字符 unigram + bigram 哈希投影后 L2 归一化。

    语义能力弱于真实 embedding，但足以让本地检索流程（灌库 / 召回 / 排序）完整跑通，
    且结果稳定可复现。
    """

    def __init__(self, dim: int = 384):
        self.dim = dim

    # ---- 内部工具 ----
    def _tokens(self, text: str) -> List[str]:
        cleaned = re.sub(r"[\s，。、；：？！“”‘’（）《》,.;:?!()\[\]]+", " ", text or "")
        cleaned = cleaned.strip().lower()
        if not cleaned:
            return []
        tokens = []
        for word in cleaned.split(" "):
            if not word:
                continue
            tokens.append(word)
            if len(word) > 1:
                tokens.extend(word[i : i + 2] for i in range(len(word) - 1))
        # 中文没有空格，补充单字与二元组
        chars = [c for c in cleaned if not c.isspace()]
        tokens.extend(chars)
        tokens.extend(
            "".join(chars[i : i + 2]) for i in range(len(chars) - 1) if len(chars) > 1
        )
        return tokens

    def _vector(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        tokens = self._tokens(text)
        if not tokens:
            return vec
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    # ---- LangChain 接口 ----
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._vector(text)


def build_embeddings(settings: Settings | None = None):
    """DeepSeek 不提供 embedding 接口，向量化优先使用 OpenAI，缺失时降级本地哈希向量。"""
    settings = settings or get_settings()
    if settings.resolved_embedding_provider() == "openai":
        try:
            from langchain_openai import OpenAIEmbeddings

            kwargs = {"model": settings.openai_embedding_model}
            if settings.openai_base_url:
                kwargs["base_url"] = settings.openai_base_url
            return OpenAIEmbeddings(**kwargs)
        except Exception:  # pragma: no cover - 依赖缺失时降级
            pass
    return HashingEmbeddings(dim=settings.fallback_embedding_dim)


def embedding_dimension(settings: Settings | None = None) -> int:
    settings = settings or get_settings()
    if settings.resolved_embedding_provider() == "openai":
        return settings.pinecone_dimension
    return settings.fallback_embedding_dim
