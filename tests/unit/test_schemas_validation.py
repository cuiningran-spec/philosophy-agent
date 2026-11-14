"""Pydantic request schema boundary tests."""
import pytest
from pydantic import ValidationError
from app.schemas import CreateSessionIn, SelectLensIn, SendMessageIn


@pytest.mark.parametrize("question", ["焦虑", "我该如何面对选择？", "中" * 300])
def test_b07_create_session_accepts_valid_question(question):
    """B-07: question 长度为 2、典型值、300 时均有效。"""
    assert CreateSessionIn(question=question).question == question


@pytest.mark.parametrize("question", ["愁", "中" * 301, "", None])
def test_b08_create_session_rejects_invalid_question(question):
    """B-08: question 少于 2、超过 300、空字符串或 null 应校验失败。"""
    with pytest.raises(ValidationError):
        CreateSessionIn(question=question)


@pytest.mark.parametrize("lens", ["stoic", "existential", "taoist"])
def test_b09_select_lens_accepts_supported_lens(lens):
    """B-09: 三种已支持视角均应通过校验。"""
    assert SelectLensIn(lens=lens).lens == lens


@pytest.mark.parametrize("lens", ["buddhist", "STOIC", "stoic ", ""])
def test_b10_select_lens_rejects_unsupported_lens(lens):
    """B-10: 未知值、大小写不符、尾随空格和空值应校验失败。"""
    with pytest.raises(ValidationError):
        SelectLensIn(lens=lens)


@pytest.mark.parametrize("content", ["a", "继续探索", "中" * 1000])
def test_b11_send_message_accepts_boundary_content(content):
    """B-11: content 长度为 1、典型值、1000 时均有效。"""
    assert SendMessageIn(content=content).content == content


@pytest.mark.parametrize("content", ["", "中" * 1001])
def test_b12_send_message_rejects_out_of_range_content(content):
    """B-12: content 为空或超过 1000 字符应校验失败。"""
    with pytest.raises(ValidationError):
        SendMessageIn(content=content)


def test_b13_send_message_stream_defaults_to_false():
    """B-13: 未提供 stream 时默认关闭流式输出。"""
    assert SendMessageIn(content="继续").stream is False
