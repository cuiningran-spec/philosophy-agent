"""全局配置：全部通过环境变量覆盖，缺失密钥时自动降级。"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------- LLM：DeepSeek（主用） ----------
    # DeepSeek 使用 OpenAI 兼容协议，因此通过 langchain-openai 的 ChatOpenAI 接入。
    deepseek_api_key: Optional[str] = Field(default=None)
    deepseek_base_url: str = Field(default="https://api.deepseek.com")
    deepseek_model: str = Field(default="deepseek-chat")  # deepseek-chat / deepseek-reasoner
    deepseek_temperature: float = Field(default=0.65)
    deepseek_max_tokens: Optional[int] = Field(default=None)

    # OpenAI：可选备用 LLM + Embedding 提供方（DeepSeek 不提供 embedding 接口）
    openai_api_key: Optional[str] = Field(default=None)
    openai_base_url: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    openai_temperature: float = Field(default=0.65)

    # auto | deepseek | openai | template（env: THINKLAB_LLM_MODE / LLM_MODE）
    llm_mode: str = Field(
        default="auto", validation_alias=AliasChoices("THINKLAB_LLM_MODE", "llm_mode")
    )

    # 真实 LLM 调用失败（网络 / 鉴权 / 限流）时，是否用模板模型兜底保证服务可用
    llm_fallback_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("THINKLAB_LLM_FALLBACK", "llm_fallback_enabled"),
    )

    # ---------- 向量库 ----------
    pinecone_api_key: Optional[str] = Field(default=None)
    pinecone_index: str = Field(default="thinklab-philosophy")
    pinecone_namespace: str = Field(default="philosophy-v1")
    pinecone_cloud: str = Field(default="aws")
    pinecone_region: str = Field(default="us-east-1")
    pinecone_dimension: int = Field(default=1536)

    # auto | pinecone | local（env: THINKLAB_VECTORSTORE_MODE / vectorstore_mode）
    vectorstore_mode: str = Field(
        default="auto",
        validation_alias=AliasChoices("THINKLAB_VECTORSTORE_MODE", "vectorstore_mode"),
    )

    # 本地降级向量库（无密钥时使用）
    local_index_path: Optional[str] = Field(default=None)
    fallback_embedding_dim: int = Field(default=384)

    # ---------- 检索（env: THINKLAB_RETRIEVAL_*）----------
    retrieval_top_k: int = Field(
        default=4, validation_alias=AliasChoices("THINKLAB_RETRIEVAL_TOP_K", "retrieval_top_k")
    )
    retrieval_candidate_k: int = Field(
        default=16,
        validation_alias=AliasChoices("THINKLAB_RETRIEVAL_CANDIDATE_K", "retrieval_candidate_k"),
    )
    retrieval_min_score: float = Field(
        default=0.0, validation_alias=AliasChoices("THINKLAB_RETRIEVAL_MIN_SCORE", "retrieval_min_score")
    )

    # ---------- 记忆（env: THINKLAB_MEMORY_*）----------
    # 送入提示词的近期轮次
    memory_window_turns: int = Field(
        default=6, validation_alias=AliasChoices("THINKLAB_MEMORY_WINDOW_TURNS", "memory_window_turns")
    )
    # 超过该轮次触发滚动摘要
    memory_compress_turns: int = Field(
        default=8,
        validation_alias=AliasChoices("THINKLAB_MEMORY_COMPRESS_TURNS", "memory_compress_turns"),
    )

    def resolved_llm_mode(self) -> str:
        """auto → 有 DEEPSEEK_API_KEY 用 deepseek，其次 OPENAI_API_KEY，否则 template。"""
        if self.llm_mode and self.llm_mode.lower() != "auto":
            return self.llm_mode.lower()
        if self.deepseek_api_key:
            return "deepseek"
        if self.openai_api_key:
            return "openai"
        return "template"

    def resolved_llm_model(self) -> str:
        mode = self.resolved_llm_mode()
        if mode == "deepseek":
            return self.deepseek_model
        if mode == "openai":
            return self.openai_model
        return "template"

    def resolved_embedding_provider(self) -> str:
        """DeepSeek 不提供 embedding 接口，向量化仍走 OpenAI 或本地哈希向量。"""
        return "openai" if self.openai_api_key else "local"

    def resolved_vectorstore_mode(self) -> str:
        if self.vectorstore_mode and self.vectorstore_mode.lower() != "auto":
            return self.vectorstore_mode.lower()
        return "pinecone" if self.pinecone_api_key else "local"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
