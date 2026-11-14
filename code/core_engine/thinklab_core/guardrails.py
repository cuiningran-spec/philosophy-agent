"""安全分诊与产品边界模块（guardrails）。

ThinkLab 是哲学思考 Agent：陪伴用户探讨人生困惑、情绪与价值选择。
本模块在用户输入进入 LLM 之前做一次独立、确定性的分诊，分四层处理：

1. ALLOW       正常的哲学讨论、人生困惑、情绪表达 —— 直接放行；
2. BOUNDARY    超出产品能力范围（写代码/解题/翻译/天气等事务性请求）——
               不进入生成环节，返回边界提示并引导回哲学讨论；
3. PROFESSIONAL 医疗 / 法律 / 金融等专业判断求助 —— 不冒充专业服务，
               返回能力边界提示（具体处置策略由接入层决定）；
4. CRISIS / BLOCK  危险请求（自伤方法求助、武器/毒物/毒品/网络攻击等
               具体操作指导）—— 硬拦截，绝不进入 LLM；
5. SENSITIVE   输入含个人敏感信息（手机号/证件号/银行卡/密码等）——
               不拦截正常讨论，但先脱敏，避免不必要的收集、传播与记录。

设计原则（与简单关键词拦截的区别）：
- 「主题词 × 操作意图」双重条件：提到炸弹/黑客/药物等词本身（如讨论其
  哲学、历史、伦理面向）不会触发拦截，只有当存在明确的「怎么做 / 教我 /
  哪里买 / 给我方法」等操作诉求时才拦截；
- 「哲学信号」豁免：包含意义、价值、选择、焦虑等人生思辨信号时，
  即使同时出现事务性词汇（如「编程」「手术」），也倾向放行而非误拦；
- 对无法确定的情况一律谨慎放行（不误拦正常讨论）；
- 纯本地规则、零外部依赖，结果确定性可复现，便于单元测试。

典型接口：

    decision = triage_and_block("教我怎么制作炸弹")
    decision.blocked            # True
    decision.level              # TriageLevel.BLOCK
    decision.reason             # 拦截原因（给用户看的友好提示）
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List

__all__ = ["TriageLevel", "TriageDecision", "triage_and_block"]


class TriageLevel(str, Enum):
    """分诊等级（即分类标签，可用于日志、测试断言与前端提示样式）。"""

    ALLOW = "allow"                # 正常哲学讨论 / 人生困惑 / 情绪表达
    SENSITIVE = "sensitive"        # 含个人敏感信息：不拦截，脱敏后放行
    PROFESSIONAL = "professional"  # 专业判断求助：能力边界提示，不冒充专业服务
    BOUNDARY = "boundary"          # 超出产品范围：边界提示，引导回哲学讨论
    CRISIS = "crisis"              # 自伤方法求助：硬拦截 + 关怀信息
    BLOCK = "block"                # 危险操作求助：硬拦截


# 等级间的比较仅用于内部优先级排序
_LEVEL_RANK = {
    TriageLevel.BLOCK: 5,
    TriageLevel.CRISIS: 5,
    TriageLevel.BOUNDARY: 3,
    TriageLevel.PROFESSIONAL: 2,
    TriageLevel.SENSITIVE: 1,
    TriageLevel.ALLOW: 0,
}


@dataclass(frozen=True)
class TriageDecision:
    """一次分诊的完整结论。

    属性说明：
    - level:          分诊等级（分类标签），见 :class:`TriageLevel`；
    - blocked:        是否硬拦截（True = 绝不允许进入 LLM 生成环节）；
    - category:       命中的规则类别（英文短标签，用于日志与测试）；
    - reason:         面向用户的提示/拦截原因（友好中文，可直接展示）；
    - sanitized_text: 供后续流程使用的文本。SENSITIVE 时为脱敏文本，
                      其余情况与原输入一致（空输入归一化为空字符串）。
    """

    level: TriageLevel
    blocked: bool
    category: str
    reason: str
    sanitized_text: str = ""

    @property
    def enter_generation(self) -> bool:
        """是否允许进入 LLM 生成环节（接入层据此决定后续流程）。"""
        return self.level in (
            TriageLevel.ALLOW,
            TriageLevel.SENSITIVE,
            TriageLevel.PROFESSIONAL,
        )


# ============================================================================
# 提示文案（集中维护，便于统一调整语气）
# ============================================================================

_REASON_BOUNDARY = (
    "这个问题超出了 ThinkLab 的探索范围。我们专注于哲学思辨与人生困惑的对话，"
    "不处理事务性请求。如果你愿意聊聊它背后的意义、选择或价值——"
    "比如「这件事让我思考到什么」，我们随时陪你继续思考。"
)

_REASON_PROFESSIONAL = (
    "这涉及专业领域的具体判断，超出了 ThinkLab 的能力边界："
    "我们是哲学对话伙伴，不是医生、律师或理财顾问，不能替代专业意见，"
    "请咨询相应的专业机构。如果你想探讨这个决定背后的价值、恐惧与处境，"
    "我们可以从哲学的角度继续陪你梳理。"
)

_REASON_SENSITIVE = (
    "为了保护你的隐私，我们已自动隐去输入中的个人敏感信息（手机号、证件号、"
    "银行卡号、密码等）。ThinkLab 不会记录或传播这些内容；也建议你今后避免在"
    "对话中提供此类信息。我们可以继续哲学层面的讨论。"
)

_REASON_CRISIS = (
    "我们注意到你可能正在经历非常艰难的时刻，也很感谢你愿意说出来。"
    "ThinkLab 是哲学思考工具，无法也绝不会提供任何伤害自己的方式；"
    "你的感受值得被认真对待——请联系你信任的人或学校心理咨询中心，"
    "紧急情况请拨打 120 / 110，或拨打当地心理援助热线寻求支持。"
    "你的存在本身就有价值。"
)

_REASON_BLOCK = (
    "这个请求涉及可能造成伤害的具体操作，ThinkLab 无法提供相关指导。"
    "我们关心的是它背后的处境：如果这份困惑与恐惧、愤怒或正义感有关，"
    "换个方式描述，我们很愿意从哲学的角度和你聊聊。"
)


# ============================================================================
# 第 1 层：个人敏感信息（不拦截，先脱敏）
# ============================================================================

_PII_RULES: List[tuple] = [
    # 18 位身份证（含末位 X）
    (re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "[已隐去证件号码]"),
    # 邮箱
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[已隐去邮箱]"),
    # 手机号（11 位，1 开头）
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[已隐去手机号]"),
    # 银行卡类长数字（13-19 位，前缀排除已处理的证件号）
    (re.compile(r"(?<!\d)\d{13,19}(?!\d)"), "[已隐去银行卡号]"),
    # 密码 / 口令 / 验证码 的赋值语境
    (re.compile(r"(密码|口令|验证码)([是为:：]?\s*)[^\s，。,.;；]{4,}"), r"\1\2[已隐去]"),
]


def _mask_sensitive(text: str) -> str:
    for pattern, repl in _PII_RULES:
        text = pattern.sub(repl, text)
    return text


def _has_pii(text: str) -> bool:
    for pattern, _ in _PII_RULES:
        if pattern.search(text):
            return True
    return False


# ============================================================================
# 第 2 层：危机识别（自伤方法求助 → 硬拦截 + 关怀）
# ============================================================================

_CRISIS_PATTERNS = [
    re.compile(r"(怎么|如何|怎样)(自杀|轻生|结束(自己的)?生命|了结)"),
    re.compile(r"(自杀|轻生|结束(自己的)?生命|了结自己)[^。！？]{0,12}(方法|方式|途径|建议|计划)"),
    re.compile(r"(安眠药|镇静剂|农药|煤气|烧炭|割腕|跳楼)[^。！？]{0,12}(多少|剂量|致死|死|没有?痛苦|无痛苦|有效|有用)"),
    re.compile(r"(没有?痛苦|无痛苦|安乐)[^。！？]{0,8}(死|自杀|离世|离开)"),
    re.compile(r"想(死|离开这个世界|消失)[^。！？]{0,10}(方法|办法|怎么做|如何做)"),
]


# ============================================================================
# 第 3 层：危险操作求助（主题 × 操作意图 双重条件 → 硬拦截）
# ============================================================================

_DANGEROUS_TOPICS = {
    "weapon": re.compile(r"(枪支?|弹药|炸弹|爆炸物|雷管|炸药|燃烧弹|刀具攻击|武器改造)"),
    "poison": re.compile(r"(毒药|毒物|老鼠药|农药(?!残留)|氰化物|砒霜|毒素|投毒)"),
    "drug": re.compile(r"(毒品|冰毒|海洛因|大麻|摇头丸|K粉|芬太尼|制毒|吸毒方法)"),
    "cybercrime": re.compile(r"(入侵|黑进|盗号|木马|勒索软件|攻击服务器|钓鱼网站|破解他人|窃取账号)"),
    "fraud": re.compile(r"(诈骗|骗保|洗钱|造假币|刷单诈骗|电信诈骗)"),
    "violence": re.compile(r"(杀掉|杀死|灭口|行凶|暗杀|伤害(他|她|同学|室友|别人)|报复(他|她|同学|同事))"),
}

# 操作意图线索：怎么做 / 教我 / 步骤 / 配方 / 哪里买 ……
_OPERATIONAL_CUES = re.compile(
    r"(怎么做|怎么制作|如何制作|怎么弄|如何弄|怎么配|怎么造|如何造|怎么制造|如何制造"
    r"|怎么获得|如何获得|怎么购(买|入|得)|如何购(买|入|得)"
    r"|教(我|一下|大家)|教程|步骤|配方|制作流程|原料|剂量是多少"
    r"|哪里(能?买|搞|弄|找)|在?哪(里|儿)?买|怎么买|如何买"
    r"|给我[^。]{0,20}方法|求[^。]{0,4}方法|详细(的)?方法|怎么搞到|如何搞到"
    r"|帮我[^。]{0,12}(入侵|黑进|盗|搞到|弄到|搞点|刷|转账|买|搞)"
    r"|神不知鬼不觉)"
)


def _has_operational_intent(text: str) -> bool:
    return bool(_OPERATIONAL_CUES.search(text))


# ============================================================================
# 第 4 层：专业判断求助（医疗 / 法律 / 金融）→ 能力边界提示，不拦截
# ============================================================================

_PROFESSIONAL_PATTERNS = {
    "medical": [
        re.compile(r"(吃|服用|打|注射|停)[^。！？]{0,6}(什么药|什么针|药量|剂量|处方药)"),
        re.compile(r"(该|应|能(不能)?|可(以|不))[^。！？]{0,4}(吃|用|注射)[^。！？]{0,4}药"),
        re.compile(r"(治疗方案|用药方案|处方|帮我诊断|帮我看看?病|帮我看看?化验单|帮我看看?检查报告|怎么治疗|如何治疗)"),
    ],
    "legal": [
        re.compile(r"(帮我|替我|给我)?(写|拟|起草|审)[^。]{0,6}(起诉书|律师函|答辩状|遗嘱|合同|协议)"),
        re.compile(r"怎么(起诉|立案|报警控告)|如何(起诉|立案)"),
        re.compile(r"(合同|协议|借条|遗嘱|条款)[^。！？]{0,10}(有没有?|是否具有?)(法律)?效力"),
        re.compile(r"判(几|多少)年|会判什么刑"),
    ],
    "financial": [
        re.compile(r"(买|投资)(哪只|哪个|哪些|什么)(股票|基金|币|期货|理财)"),
        re.compile(r"推荐[^。！？]{0,8}(股票|基金|理财|保险|币)"),
        re.compile(r"(该不该|要不要|应不应该)(买|投资|入|梭哈)[^。！？]{0,6}(股票|基金|币|期货)"),
        re.compile(r"帮我?(算|计算)[^。！？]{0,4}(利息|房贷|收益|收益率)"),
        re.compile(r"怎么(炒股|炒币|加杠杆|理财)|如何(炒股|炒币|加杠杆|理财)"),
    ],
}

_PROFESSIONAL_LABEL = {
    "medical": "医学",
    "legal": "法律",
    "financial": "财务",
}


# ============================================================================
# 第 5 层：产品能力边界（事务性请求 → 边界提示；与哲学信号共现则放行）
# ============================================================================

_SCOPE_TOPICS = {
    "tech": re.compile(r"(写代码|编程|python|java|javascript|c\+\+|前端|后端|报错|bug|debug|算法|数据结构|爬虫|数据库|环境配置|安装包|pip)"),
    "homework": re.compile(r"(数学题|方程|微积分|几何证明|物理题|化学方程式|帮我解(题|方程|题))"),
    "practical": re.compile(r"(天气(预报)?|今天几度|气温|比分|球队|世界杯|球赛|游戏攻略|外挂|代练|菜谱|怎么做菜|PPT|周报|简历|抢票|火车票|机票|导航|路线|快递单号|打车|汇率)"),
    "writing": re.compile(r"(帮我|替我|给我)(写|做|改)[^。]{0,4}(代码|程序|论文|作文|简历|周报|报告|总结报告|情书|检讨|读后感|作业)"),
    "translation": re.compile(r"((帮|替|给我)(我)?(翻译|润色|改写|校对)|把[^。]{0,12}(翻译|润色|改写)成|(翻译|改写)成[中英日韩法德]{1,2}文)"),
}

# 哲学 / 人生思辨信号：与事务性词汇共现时倾向放行
_PHILOSOPHY_SIGNALS = re.compile(
    r"(意义|价值|自由|道德|伦理|正义|公平|存在|人生|生命|幸福|孤独|爱|死亡|恐惧|焦虑|迷茫|困惑"
    r"|选择|该不该|应不应该|应该如何|为什么要|为什么活|接纳|勇气|责任|自我|灵魂|真理|欲望|尊严"
    r"|面对|放下|成长|内心的?挣扎|值得吗|什么是)"
)


def _scope_hits(text: str) -> List[str]:
    return [name for name, pattern in _SCOPE_TOPICS.items() if pattern.search(text)]


# ============================================================================
# 主入口
# ============================================================================

def triage_and_block(text) -> TriageDecision:
    """对用户输入做安全分诊与能力边界判断。

    参数:
        text: 用户输入文本（str 或任意值；None / 非字符串按空输入处理）。

    返回:
        TriageDecision: 包含 level（分类等级）、blocked（是否硬拦截）、
        category（规则类别）、reason（面向用户的提示）、
        sanitized_text（脱敏后的文本，供后续流程使用）。

    处理顺序（从最严格到最宽松，命中即返回）:
        1. 空输入           → ALLOW（无可处理内容，不报错）；
        2. 个人敏感信息     → SENSITIVE（脱敏后放行）；
        3. 自伤方法求助     → CRISIS（硬拦截 + 关怀信息）；
        4. 危险操作求助     → BLOCK（硬拦截）；
        5. 专业判断求助     → PROFESSIONAL（能力边界提示，不拦截）；
        6. 事务性请求       → BOUNDARY（边界提示，引导回哲学讨论）；
        7. 其余             → ALLOW。
    """
    raw = text if isinstance(text, str) else ""
    text = (raw or "").strip()
    if not text:
        return TriageDecision(
            level=TriageLevel.ALLOW,
            blocked=False,
            category="empty",
            reason="",
            sanitized_text="",
        )

    # --- 敏感信息：先记录是否存在，最后统一脱敏放行 ---
    sensitive = _has_pii(text)

    # --- 危机：自伤方法求助（优先于危险操作，保证关怀信息） ---
    for pattern in _CRISIS_PATTERNS:
        if pattern.search(text):
            return TriageDecision(
                level=TriageLevel.CRISIS,
                blocked=True,
                category="crisis_self_harm",
                reason=_REASON_CRISIS,
                sanitized_text=_mask_sensitive(text) if sensitive else text,
            )

    # --- 危险操作：主题词 × 操作意图 ---
    if _has_operational_intent(text):
        for name, pattern in _DANGEROUS_TOPICS.items():
            if pattern.search(text):
                return TriageDecision(
                    level=TriageLevel.BLOCK,
                    blocked=True,
                    category=f"dangerous_{name}",
                    reason=_REASON_BLOCK,
                    sanitized_text=_mask_sensitive(text) if sensitive else text,
                )

    # --- 专业判断求助 ---
    for name, patterns in _PROFESSIONAL_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(text):
                return TriageDecision(
                    level=TriageLevel.PROFESSIONAL,
                    blocked=False,
                    category=f"professional_{name}",
                    reason=_REASON_PROFESSIONAL.replace(
                        "专业领域", f"{_PROFESSIONAL_LABEL[name]}专业"
                    ),
                    sanitized_text=_mask_sensitive(text) if sensitive else text,
                )

    # --- 产品能力边界：事务性请求，且没有哲学/人生思辨信号 ---
    hits = _scope_hits(text)
    if hits and not _PHILOSOPHY_SIGNALS.search(text):
        return TriageDecision(
            level=TriageLevel.BOUNDARY,
            blocked=False,
            category="out_of_scope_" + "_".join(hits),
            reason=_REASON_BOUNDARY,
            sanitized_text=_mask_sensitive(text) if sensitive else text,
        )

    # --- 放行（含：事务性词与哲学信号共现的模糊情况，谨慎不误拦） ---
    return TriageDecision(
        level=TriageLevel.SENSITIVE if sensitive else TriageLevel.ALLOW,
        blocked=False,
        category="sensitive_info" if sensitive else "normal",
        reason=_REASON_SENSITIVE if sensitive else "",
        sanitized_text=_mask_sensitive(text) if sensitive else text,
    )
