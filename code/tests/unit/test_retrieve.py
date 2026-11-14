
import pytest
from langchain_core.documents import Document

from thinklab_core.chains import (
    _boost,
    _safe_json,
    format_context,
    retrieve,
)


class FakeVectorStore:
    """用于测试的模拟向量数据库。"""

    def __init__(self, documents):
        self.documents = documents

    def similarity_search_with_score(self, query, k=4):
        return self.documents[:k]


class FallbackVectorStore:
    """模拟不支持带分数检索的向量库。"""

    def __init__(self, documents):
        self.documents = documents

    def similarity_search_with_score(self, query, k=4):
        raise RuntimeError("模拟检索异常")

    def similarity_search(self, query, k=4):
        return self.documents[:k]


def test_boost_same_school():
    """TC-RET-01：相同哲学流派应获得 0.18 加权分。"""
    assert _boost(
        "stoic",
        {"school": "stoic"},
    ) == pytest.approx(0.18)


def test_boost_general_school():
    """TC-RET-02：通用语料应获得 0.06 加权分。"""
    assert _boost(
        "stoic",
        {"school": "general"},
    ) == pytest.approx(0.06)


def test_boost_other_school():
    """TC-RET-03：其他流派语料不应获得额外加权分。"""
    assert _boost(
        "stoic",
        {"school": "taoist"},
    ) == pytest.approx(0.0)


def test_retrieve_returns_ranked_results(test_settings):
    """TC-RET-04：检索结果应按照加权分从高到低排序。"""
    documents = [
        (
            Document(
                page_content="道家关于自然的讨论",
                metadata={
                    "doc_id": "doc1",
                    "title": "道家思想",
                    "school": "taoist",
                },
            ),
            0.5,
        ),
        (
            Document(
                page_content="斯多葛主义关于控制的讨论",
                metadata={
                    "doc_id": "doc2",
                    "title": "控制二分法",
                    "school": "stoic",
                },
            ),
            0.4,
        ),
    ]

    store = FakeVectorStore(documents)

    results = retrieve(
        store,
        query="如何面对无法控制的事情",
        school="stoic",
        k=2,
        settings=test_settings,
    )

    assert len(results) == 2
    assert results[0].doc_id == "doc2"
    assert results[0].score > results[1].score


def test_retrieve_respects_top_k(test_settings):
    """TC-RET-05：检索结果数量不应超过 k。"""
    documents = [
        (
            Document(
                page_content=f"内容{i}",
                metadata={
                    "doc_id": f"doc{i}",
                    "title": f"标题{i}",
                    "school": "general",
                },
            ),
            0.5,
        )
        for i in range(5)
    ]

    store = FakeVectorStore(documents)

    results = retrieve(
        store,
        query="哲学",
        k=2,
        settings=test_settings,
    )

    assert len(results) <= 2


def test_retrieve_filters_low_scores(test_settings):
    """TC-RET-06：低于最低分数阈值的结果应被过滤。"""
    documents = [
        (
            Document(
                page_content="低分内容",
                metadata={
                    "doc_id": "doc1",
                    "title": "低分文档",
                    "school": "general",
                },
            ),
            0.01,
        )
    ]

    test_settings.retrieval_min_score = 0.5
    store = FakeVectorStore(documents)

    results = retrieve(
        store,
        query="哲学",
        k=1,
        settings=test_settings,
    )

    assert results == []


def test_retrieve_fallback_when_scored_search_fails(test_settings):
    """TC-RET-07：带分数检索失败时应回退普通检索。"""
    documents = [
        Document(
            page_content="回退检索内容",
            metadata={
                "doc_id": "fallback1",
                "title": "回退文档",
                "school": "general",
            },
        )
    ]

    store = FallbackVectorStore(documents)

    results = retrieve(
        store,
        query="哲学",
        k=1,
        settings=test_settings,
    )

    assert len(results) == 1
    assert results[0].doc_id == "fallback1"
    assert results[0].score == pytest.approx(0.06)


def test_format_context_with_empty_list():
    """TC-RET-08：没有检索结果时应返回默认提示。"""
    result = format_context([])

    assert "本次没有命中语料" in result


def test_format_context_with_sources():
    """TC-RET-09：有检索结果时应包含标题、思想家和片段。"""
    from thinklab_core.schemas import SourceItem

    items = [
        SourceItem(
            doc_id="doc1",
            title="沉思录",
            school="stoic",
            thinker="马可·奥勒留",
            snippet="你能控制自己的判断与行动。",
            score=0.8,
        )
    ]

    result = format_context(items)

    assert "沉思录" in result
    assert "马可·奥勒留" in result
    assert "你能控制自己的判断与行动。" in result


@pytest.mark.parametrize(
    "raw, expected",
    [
        ('{"reading": "正常文本"}', {"reading": "正常文本"}),
        (
            '模型回答如下：{"reading": "提取成功"} 请继续。',
            {"reading": "提取成功"},
        ),
        ("无法解析的内容", {}),
        ("", {}),
        ('{"reading": invalid}', {}),
    ],
)
def test_safe_json_handles_valid_and_invalid_text(raw, expected):
    """TC-RET-10：应提取合法 JSON，无法解析时返回空字典。"""
    assert _safe_json(raw) == expected
