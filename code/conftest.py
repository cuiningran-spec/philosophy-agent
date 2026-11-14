
import sys
from pathlib import Path

import pytest

# code/ 目录
CODE_ROOT = Path(__file__).resolve().parents[1]

# 将核心引擎目录加入 Python 搜索路径
CORE_ENGINE = CODE_ROOT / "core_engine"

if str(CORE_ENGINE) not in sys.path:
    sys.path.insert(0, str(CORE_ENGINE))


@pytest.fixture
def test_settings():
    """提供不依赖外部 API 的测试配置。"""
    from thinklab_core.config import Settings

    return Settings(
        llm_mode="template",
        vectorstore_mode="local",
        fallback_embedding_dim=128,
        retrieval_top_k=3,
        retrieval_candidate_k=9,
        retrieval_min_score=0.0,
        memory_window_turns=2,
        memory_compress_turns=3,
    )
