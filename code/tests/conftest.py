"""ThinkLab 测试基础设施（组员 A 维护，B/C/D 直接使用其中的 fixture）。

本文件只负责：
1. 项目模块导入路径（core_engine 与 backend）；
2. 测试环境变量隔离（不访问 DeepSeek / OpenAI / Pinecone 等外部付费服务）；
3. 每个测试独立的临时 SQLite 数据库（函数级隔离，用后销毁）；
4. FastAPI TestClient、DB Session 两个基础 fixture；
5. 单例缓存清理（保证测试之间互不影响）。

不包含任何业务测试用例 —— 用例由 B（单元）、C（集成）、D（端到端）编写。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# ------------------------------------------------------------------
# 1. 模块导入路径：code/core_engine 与 code/backend
#    统一使用「app.main / app.db」导入后端（与 README 的 PYTHONPATH=backend 运行方式一致），
#    避免同一模块以两个名字被重复导入导致单例分裂。
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # code/
CORE_ENGINE_DIR = PROJECT_ROOT / "core_engine"
BACKEND_DIR = PROJECT_ROOT / "backend"

for _path in (str(CORE_ENGINE_DIR), str(BACKEND_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

# ------------------------------------------------------------------
# 2. 测试环境变量：必须在导入业务模块之前设置（优先级高于 code/.env）
#    - LLM 固定 template 模式：零网络请求、输出确定
#    - 数据库固定 SQLite，具体路径由 fresh_db fixture 指向 pytest 临时目录
#    - 不写业务日志文件，避免测试污染 code/backend/logs/thinklab.log
# ------------------------------------------------------------------
os.environ["THINKLAB_DB_MODE"] = "sqlite"
os.environ["THINKLAB_LLM_MODE"] = "template"
os.environ["DEEPSEEK_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["PINECONE_API_KEY"] = ""
os.environ["THINKLAB_LLM_FALLBACK"] = "true"
os.environ["AUTO_CREATE_TABLES"] = "false"      # 建表由 fixture 显式控制
os.environ["AUTO_INGEST_ON_STARTUP"] = "false"  # 灌库由 fixture 显式控制
os.environ.setdefault("THINKLAB_LOG_LEVEL", "WARNING")  # 默认静音；调试时可设 DEBUG
os.environ.pop("THINKLAB_LOG_FILE", None)


# ------------------------------------------------------------------
# 3. 单例清理工具
# ------------------------------------------------------------------
def _reset_singletons() -> None:
    """清理项目内的模块级单例，保证测试隔离。

    - thinklab_core.service._AGENT：Agent 单例（业务代码未提供 reset API，
      此处直接置空属于测试基础设施行为，不修改业务代码）
    - thinklab_core.vectorstore：本地向量库缓存（业务代码提供公开 reset API）
    """
    from thinklab_core import service as core_service
    from thinklab_core import vectorstore as core_vectorstore

    core_service._AGENT = None
    core_vectorstore.reset_vectorstore_cache()


# ------------------------------------------------------------------
# 4. 基础 fixture
# ------------------------------------------------------------------
@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """每个测试一个独立的临时 SQLite 数据库（函数级隔离，测试结束即销毁）。

    用法（B/C/D）：需要数据库的测试直接声明 ``def test_xxx(fresh_db):`` 或
    使用其上的 ``db_session`` / ``api_client``，不要自己连接业务库。
    """
    db_path = tmp_path / "test_thinklab.db"

    # 指向临时库；monkeypatch 会在测试结束后自动还原环境变量
    monkeypatch.setenv("THINKLAB_DB_MODE", "sqlite")
    monkeypatch.setenv("THINKLAB_SQLITE_PATH", str(db_path))

    # 两个配置缓存重读环境变量（公开 API / 标准用法）
    from thinklab_core.config import reload_settings

    reload_settings()

    from app.config import get_settings as backend_settings

    backend_settings.cache_clear()

    # 重建后端引擎与会话工厂（app/db.py 公开 API），并显式建表
    from app import db as app_db
    from app import models as app_models

    app_db.init_engine()
    app_models.Base.metadata.create_all(app_db.get_engine())

    _reset_singletons()

    yield db_path

    # 收尾：重建一次引擎释放对临时文件的引用（monkeypatch 之后由 pytest 删除 tmp 目录）
    app_db.init_engine()


@pytest.fixture
def db_session(fresh_db):
    """绑定到临时 SQLite 的 SQLAlchemy Session（每个测试独立，互不污染）。"""
    from app.db import session_scope

    session = session_scope()
    yield session
    session.close()


@pytest.fixture
def api_client(fresh_db):
    """FastAPI TestClient（启动事件已触发）。

    - AUTO_CREATE_TABLES=false、AUTO_INGEST_ON_STARTUP=false：
      建表已由 fresh_db 完成，知识库灌库在首个请求时自动进行（本地向量库，无网络）
    - LLM 为 template 模式：整个测试过程不访问 DeepSeek / OpenAI
    """
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_settings():
    """为单元测试提供独立的配置对象。"""
    from thinklab_core.config import Settings

    return Settings(
        llm_mode="template",
        memory_window_turns=2,
        memory_compress_turns=3,
        retrieval_top_k=4,
        retrieval_candidate_k=16,
        retrieval_min_score=0.0,
    )