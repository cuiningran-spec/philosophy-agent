"""guardrails 分诊结果 → HTTP 行为的薄适配层。

所有接收自由文本的 API 入口（创建探索、对话、流式对话、FAQ）
统一通过 :func:`guard_text` 处理：

- BLOCK / CRISIS  → 400（拦截，绝不调用 LLM，内容不落库）；
- BOUNDARY        → 400（边界提示，引导回哲学讨论，不调用 LLM）；
- SENSITIVE       → 返回脱敏后的文本继续原流程（避免敏感信息落库/外传）；
- PROFESSIONAL    → 放行（是否跳过 LLM 由各入口的产品策略决定）；
- ALLOW           → 返回原文，完全保持原有流程。
"""

from __future__ import annotations

from typing import Tuple

from fastapi import HTTPException

from thinklab_core.guardrails import TriageDecision, TriageLevel, triage_and_block
from thinklab_core.logging_utils import get_logger

logger = get_logger("guardrails")

__all__ = ["guard_text", "is_boundary_level"]


def guard_text(text: str) -> Tuple[str, TriageDecision]:
    """对用户输入执行 guardrails 分诊。

    返回:
        (text_for_pipeline, decision)：text_for_pipeline 为后续流程应使用的文本
        （SENSITIVE 时为脱敏文本，其余与原文一致）。

    异常:
        HTTPException(400): BLOCK / CRISIS / BOUNDARY —— 请求不进入生成环节，
        detail 为面向用户的友好提示（沿用现有 {"detail": ...} 错误格式）。
    """
    decision = triage_and_block(text)

    if decision.blocked or decision.level == TriageLevel.BOUNDARY:
        logger.warning(
            "guardrails 拦截：%s（%s）：%s",
            decision.level.value,
            decision.category,
            (text or "")[:60],
        )
        raise HTTPException(status_code=400, detail=decision.reason)

    if decision.level == TriageLevel.SENSITIVE:
        logger.info("guardrails 已脱敏输入（%s）", decision.category)

    return decision.sanitized_text, decision


def is_boundary_level(decision: TriageDecision) -> bool:
    """该分诊结果是否应跳过 LLM、直接返回固定提示（专业判断类）。"""
    return decision.level == TriageLevel.PROFESSIONAL
