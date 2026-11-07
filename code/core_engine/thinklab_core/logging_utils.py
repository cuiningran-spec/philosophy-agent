"""统一日志：thinklab 命名空间 + 可选文件输出。

- 所有模块通过 ``get_logger(__name__)`` 获取子 logger，继承统一格式与级别
- 级别由 ``THINKLAB_LOG_LEVEL``（默认 INFO）控制
- 可选 ``THINKLAB_LOG_FILE`` 追加文件输出（目录不存在时自动创建）
- 配置幂等：多次调用只会装配一次 handler，避免重复输出
"""

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path
from typing import Optional

from .config import Settings, get_settings

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_CONFIGURED = False
_LOCK = threading.Lock()


def _level_from(value: Optional[str]) -> int:
    try:
        return getattr(logging, str(value or "INFO").upper(), logging.INFO)
    except Exception:
        return logging.INFO


def configure_logging(settings: Optional[Settings] = None) -> logging.Logger:
    """装配 thinklab 根 logger（幂等），返回根 logger。"""
    global _CONFIGURED
    root = logging.getLogger("thinklab")

    with _LOCK:
        if _CONFIGURED:
            return root

        settings = settings or get_settings()
        root.setLevel(_level_from(settings.log_level))
        root.propagate = False  # 避免重复透传到 root logger

        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(formatter)
        root.addHandler(console)

        if settings.log_file:
            try:
                log_path = Path(settings.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_path, encoding="utf-8")
                file_handler.setFormatter(formatter)
                root.addHandler(file_handler)
            except Exception as exc:  # pragma: no cover - 文件不可写时仅告警
                root.warning("日志文件不可用（%s），仅保留控制台输出", exc)

        root.debug("日志已装配：level=%s file=%s", settings.log_level, settings.log_file or "-")
        _CONFIGURED = True
        return root


def get_logger(name: str = "") -> logging.Logger:
    """获取 thinklab 子 logger；首次调用时自动完成配置。"""
    root = configure_logging()
    return logging.getLogger(f"thinklab.{name}") if name else root
