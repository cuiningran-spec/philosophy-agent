"""后端日志装配：复用 thinklab_core 的统一格式，API 层使用独立子 logger。"""

from __future__ import annotations

import logging

from thinklab_core.config import get_settings as core_settings
from thinklab_core.logging_utils import configure_logging, get_logger

_configured = False


def setup_logging() -> None:
    """应用启动时调用一次；幂等。日志级别/文件由 THINKLAB_LOG_LEVEL / THINKLAB_LOG_FILE 控制。"""
    global _configured
    if _configured:
        return
    settings = core_settings()
    configure_logging(settings)
    # DEBUG 之外关闭 uvicorn 的逐条访问日志（由请求中间件统一记录，避免重复）
    logging.getLogger("uvicorn.access").setLevel(
        logging.DEBUG if settings.log_level.upper() == "DEBUG" else logging.WARNING
    )
    # SQLAlchemy 只在 DEBUG 时输出 SQL
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.log_level.upper() == "DEBUG" else logging.WARNING
    )
    _configured = True


__all__ = ["setup_logging", "get_logger"]
