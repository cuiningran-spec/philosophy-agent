"""ThinkLab 知识库检索智能体内核（LangChain + Pinecone）。

对外只暴露 ``ThinkLabAgent`` 门面，供 FastAPI 服务调用：

- ``read_and_perspectives`` 读取用户问题并产出三种哲学视角
- ``start_dialogue`` / ``reply`` 基于知识库检索 + 多轮记忆生成对话
- ``summarize`` 生成结构化思考记录（洞见 / 张力 / 实践）
- ``ask_faq`` FAQ 知识库问答
- ``search`` / ``ingest`` 知识库检索与灌库

LLM 默认调用 **DeepSeek**（``DEEPSEEK_API_KEY``，走 OpenAI 兼容协议的 ``https://api.deepseek.com``）。
未配置 DEEPSEEK_API_KEY / PINECONE_API_KEY 时自动降级为本地向量库 + 模板化 LLM，
保证零密钥也能完整跑通 MVP 流程。
"""

from .config import Settings, get_settings
from .schemas import (
    DialogueResult,
    FaqResult,
    LensProfile,
    Perspective,
    PerspectivesResult,
    SourceItem,
    SummaryResult,
)
from .service import ThinkLabAgent, get_agent

__all__ = [
    "Settings",
    "get_settings",
    "ThinkLabAgent",
    "get_agent",
    "LensProfile",
    "Perspective",
    "PerspectivesResult",
    "DialogueResult",
    "SummaryResult",
    "FaqResult",
    "SourceItem",
]
