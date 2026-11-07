"""统一异常与错误处理：请求 ID、访问日志、结构化错误响应。

- ``RequestLoggingMiddleware``：为每个请求生成/透传 request_id，记录方法、路径、
  状态码与耗时；健康检查等噪声路由降为 DEBUG。
- ``register_error_handlers``：
  - ``RequestValidationError`` → 422，记录 warning，响应体保留 ``detail``
  - ``HTTPException`` → 按原状态码返回 ``{"detail": ...}``（兼容前端解析），记录 warning
  - 未捕获异常 → 500，记录完整堆栈，响应体为通用提示（不泄露内部细节）
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from thinklab_core.logging_utils import get_logger

logger = get_logger("api")

# 这些路由只记 DEBUG，避免健康检查/探活刷屏
_QUIET_PATHS = ("/api/health", "/api/lenses", "/api/faq")


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or uuid.uuid4().hex[:12]


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志 + request_id 注入 + 响应头回传。"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        start = time.perf_counter()
        quiet = request.url.path in _QUIET_PATHS

        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - 全局异常处理器会先接管
            logger.exception(
                "[rid=%s] 请求异常 %s %s：%s", request_id, request.method, request.url.path, exc
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        log = logger.debug if quiet else logger.info
        log(
            "[rid=%s] %s %s -> %s（%.0fms）",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


def register_error_handlers(app: FastAPI) -> None:
    """注册全局异常处理器（在 FastAPI 默认行为基础上补充日志与结构化响应）。"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> Response:
        rid = _request_id(request)
        log = logger.debug if exc.status_code < 500 else logger.error
        log("[rid=%s] %s %s -> %s：%s", rid, request.method, request.url.path, exc.status_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc.detail), "request_id": rid},
            headers=getattr(exc, "headers", None) or {},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> Response:
        rid = _request_id(request)
        logger.warning(
            "[rid=%s] 请求参数校验失败 %s %s：%s",
            rid,
            request.method,
            request.url.path,
            exc.errors()[:5],
        )
        return JSONResponse(
            status_code=422,
            content={
                "detail": "请求参数不合法",
                "errors": [
                    {"loc": err.get("loc"), "msg": err.get("msg")} for err in exc.errors()[:10]
                ],
                "request_id": rid,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> Response:
        rid = _request_id(request)
        logger.exception(
            "[rid=%s] 未处理异常 %s %s：%s", rid, request.method, request.url.path, exc
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "服务内部错误，请稍后重试",
                "request_id": rid,
            },
        )
