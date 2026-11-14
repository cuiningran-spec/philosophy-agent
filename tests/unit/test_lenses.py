
import pytest

from thinklab_core.lenses import (
    LENS_PROFILES,
    LENS_ORDER,
    get_lens,
    reading_for,
    default_reading,
)


def test_lens_profiles_contain_three_lenses():
    """TC-LENS-01：检查三种哲学视角是否完整。"""
    assert set(LENS_ORDER) == {"stoic", "existential", "taoist"}
    assert set(LENS_PROFILES.keys()) == {"stoic", "existential", "taoist"}


@pytest.mark.parametrize(
    "key, expected_name",
    [
        ("stoic", "斯多葛主义"),
        ("existential", "存在主义"),
        ("taoist", "道家 · 庄子"),
    ],
)
def test_get_lens_returns_correct_profile(key, expected_name):
    """TC-LENS-02：根据合法视角标识获取对应画像。"""
    profile = get_lens(key)

    assert profile.key == key
    assert profile.name == expected_name
    assert profile.core_ask
    assert profile.description


def test_get_lens_unknown_key_falls_back_to_stoic():
    """TC-LENS-03：未知视角应回退到斯多葛主义。"""
    profile = get_lens("unknown")

    assert profile.key == "stoic"


@pytest.mark.parametrize(
    "question, expected_keyword",
    [
        ("我最近总是焦虑和担心", "焦虑"),
        ("我不知道应该选择哪条路", "选择"),
        ("我对未来的工作和人生很迷茫", "工作"),
        ("我和朋友之间的关系出现了问题", "关系"),
        ("我正在经历亲人的离别", "死亡"),
    ],
)
def test_reading_for_matches_question_keywords(question, expected_keyword):
    """TC-LENS-04：包含指定关键词的问题应匹配对应阅读规则。"""
    result = reading_for(question)

    assert isinstance(result, str)
    assert result
    assert result != default_reading(question)


def test_reading_for_unmatched_question_returns_default():
    """TC-LENS-05：没有匹配关键词时返回默认阅读。"""
    question = "今天的天气怎么样"

    assert reading_for(question) == default_reading(question)

