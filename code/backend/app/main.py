"""应用入口：装配路由、建表、预热知识库。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401 注册 ORM 模型
from .config import get_settings
from .db import create_tables
from .deps import get_ai_agent
from .routers import chat, health, knowledge, sessions, summaries

settings = get_settings()

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

router_list = [health.router, sessions.router, chat.router, summaries.router, knowledge.router]
for item in router_list:
    app.include_router(item, prefix=settings.api_prefix)


@app.on_event("startup")
def on_startup() -> None:
    if settings.auto_create_tables:
        create_tables()
    if settings.auto_ingest_on_startup:
        try:
            agent = get_ai_agent()
            print(f"[thinklab] 知识库预热：{agent.ingest()}")
        except Exception as exc:  # pragma: no cover
            print(f"[thinklab] 知识库预热失败：{exc}")


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
    }
