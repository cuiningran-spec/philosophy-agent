
from thinklab_core.memory import DialogueMemory


def test_empty_history_initialization(test_settings):
    """TC-MEM-01：没有历史记录时应正常初始化。"""
    memory = DialogueMemory(settings=test_settings)

    assert memory.history == []
    assert memory.rolling_summary == ""
    assert memory.user_turns == 0


def test_user_turns_count(test_settings):
    """TC-MEM-02：应正确统计用户发言轮数。"""
    history = [
        {"role": "user", "content": "什么是自由？"},
        {"role": "assistant", "content": "可以从存在主义理解。"},
        {"role": "user", "content": "自由为什么伴随焦虑？"},
    ]

    memory = DialogueMemory(history, settings=test_settings)

    assert memory.user_turns == 2


def test_transcript_content(test_settings):
    """TC-MEM-03：应正确生成对话文本记录。"""
    history = [
        {"role": "user", "content": "什么是自由？"},
        {"role": "assistant", "content": "自由意味着选择。"},
    ]

    memory = DialogueMemory(history, settings=test_settings)
    transcript = memory.transcript()

    assert "用户：什么是自由？" in transcript
    assert "Agent：自由意味着选择。" in transcript


def test_transcript_limit(test_settings):
    """TC-MEM-04：transcript 应只保留指定数量的最近记录。"""
    history = [
        {"role": "user", "content": f"问题{i}"}
        for i in range(5)
    ]

    memory = DialogueMemory(history, settings=test_settings)
    transcript = memory.transcript(limit=2)

    assert "问题3" in transcript
    assert "问题4" in transcript
    assert "问题0" not in transcript


def test_history_window_limit(test_settings):
    """TC-MEM-05：近期消息数量不应超过窗口限制。"""
    history = [
        {"role": "user", "content": f"问题{i}"}
        for i in range(6)
    ]

    memory = DialogueMemory(history, settings=test_settings)
    messages = memory.history_messages()

    # memory_window_turns=2，每轮最多两条消息
    assert len(messages) <= 4


def test_should_compress_when_turns_exceed_limit(test_settings):
    """TC-MEM-06：用户轮数超过压缩阈值时应触发压缩。"""
    history = [
        {"role": "user", "content": f"问题{i}"}
        for i in range(4)
    ]

    memory = DialogueMemory(history, settings=test_settings)

    assert memory.should_compress() is True


def test_should_not_compress_within_limit(test_settings):
    """TC-MEM-07：用户轮数未超过压缩阈值时不应触发压缩。"""
    history = [
        {"role": "user", "content": f"问题{i}"}
        for i in range(3)
    ]

    memory = DialogueMemory(history, settings=test_settings)

    assert memory.should_compress() is False


def test_compress_without_old_history_returns_existing_summary(test_settings):
    """TC-MEM-08：没有旧消息和已有摘要时，压缩应返回空摘要。"""
    memory = DialogueMemory(
        history=[],
        rolling_summary="",
        settings=test_settings,
    )

    result = memory.compress(llm=None)

    assert result == ""
