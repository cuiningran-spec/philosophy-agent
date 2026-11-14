"""Configuration resolution tests without external services."""
from thinklab_core.config import Settings


def test_b14_auto_mode_without_keys_uses_template():
    """B-14: auto 模式且没有密钥时使用 template。"""
    settings = Settings(llm_mode="auto", deepseek_api_key=None, openai_api_key=None)
    assert settings.resolved_llm_mode() == "template"
    assert settings.resolved_llm_model() == "template"


def test_b15_auto_mode_prefers_deepseek_key():
    """B-15: auto 模式下存在 DeepSeek 密钥时选择 deepseek。"""
    settings = Settings(llm_mode="auto", deepseek_api_key="test-key", openai_api_key="openai-key")
    assert settings.resolved_llm_mode() == "deepseek"


def test_b16_explicit_template_mode_overrides_keys():
    """B-16: 显式 template 模式优先于密钥配置。"""
    settings = Settings(llm_mode="template", deepseek_api_key="test-key")
    assert settings.resolved_llm_mode() == "template"


def test_b17_embedding_provider_falls_back_to_local():
    """B-17: 未配置 OpenAI 密钥时 embedding 使用本地实现。"""
    settings = Settings(openai_api_key=None)
    assert settings.resolved_embedding_provider() == "local"


def test_b18_vectorstore_mode_falls_back_to_local():
    """B-18: auto 模式且无 Pinecone 密钥时使用本地向量库。"""
    settings = Settings(vectorstore_mode="auto", pinecone_api_key=None)
    assert settings.resolved_vectorstore_mode() == "local"
