"""应用入口：装配日志、路由、全局异常处理、建表、预热知识库。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 先导入本地 config：它会把 core_engine 加入 sys.path（thinklab_core 的导入依赖它）
from .config import get_settings  # noqa: E402  # isort: skip

from thinklab_core.config import get_settings as core_settings  # noqa: E402
from thinklab_core.logging_utils import get_logger  # noqa: E402

from . import models  # noqa: F401,E402 注册 ORM 模型
from .db import create_tables  # noqa: E402
from .deps import get_ai_agent  # noqa: E402
from .errors import RequestLoggingMiddleware, register_error_handlers  # noqa: E402
from .logging_config import get_logger, setup_logging  # noqa: E402
from .routers import chat, health, knowledge, sessions, summaries  # noqa: E402

setup_logging()
logger = get_logger("main")

settings = get_settings()
core_cfg = core_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="ThinkLab 哲学思考 Agent：知识库检索 + 多轮记忆 + 结构化思考记录",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 注意：后添加的中间件先执行（外层），因此请求日志包住 CORS
app.add_middleware(RequestLoggingMiddleware)

register_error_handlers(app)

router_list = [health.router, sessions.router, chat.router, summaries.router, knowledge.router]
for item in router_list:
    app.include_router(item, prefix=settings.api_prefix)


@app.on_event("startup")
def on_startup() -> None:
    logger.info(
        "ThinkLab API 启动：llm=%s db_mode=%s log_level=%s",
        core_cfg.resolved_llm_mode(),
        settings.db_mode,
        core_cfg.log_level,
    )
    if settings.auto_create_tables:
        try:
            create_tables()
            logger.info("数据库表已就绪")
        except Exception as exc:  # pragma: no cover
            logger.exception("建表失败：%s", exc)
            raise
    if settings.auto_ingest_on_startup:
        try:
            agent = get_ai_agent()
            result = agent.ingest()
            logger.info("知识库预热完成：%s", result)
        except Exception as exc:  # pragma: no cover
            logger.error("知识库预热失败（服务继续启动，首次问答会重试）：%s", exc, exc_info=True)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
    }
