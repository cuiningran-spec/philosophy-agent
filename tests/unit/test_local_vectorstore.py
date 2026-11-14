
"""LocalVectorStore unit tests."""
import pytest
from thinklab_core.embeddings import HashingEmbeddings
from thinklab_core.vectorstore import LocalVectorStore


@pytest.fixture
def store(tmp_path):
    return LocalVectorStore(HashingEmbeddings(dim=64), str(tmp_path / "vectors.json"))


def test_b01_add_texts_and_count(store):
    """B-01: 添加三条文本后 count 应为 3。"""
    ids = store.add_texts(["斯多葛主义", "存在主义", "道家思想"], ids=["a", "b", "c"])
    assert ids == ["a", "b", "c"]
    assert store.count() == 3


def test_b02_similarity_search_returns_documents(store):
    """B-02: 检索应返回 Document，且最相关内容排在前面。"""
    store.add_texts(["自由与责任", "天气预报"], ids=["philosophy", "weather"])
    results = store.similarity_search_with_score("自由与责任", k=2)
    assert len(results) == 2
    assert results[0][0].page_content == "自由与责任"
    assert results[0][1] >= results[1][1]


def test_b03_delete_by_id(store):
    """B-03: 删除指定 ID 后记录数量减少，其他记录保留。"""
    store.add_texts(["甲", "乙"], ids=["a", "b"])
    assert store.delete(ids=["a"]) is True
    assert store.count() == 1
    assert [d.page_content for d in store.similarity_search("乙", k=2)] == ["乙"]


def test_b04_persistence_reload(tmp_path):
    """B-04: 写入 JSON 后重新加载应保留记录及元数据。"""
    path = tmp_path / "persist.json"
    first = LocalVectorStore(HashingEmbeddings(dim=64), str(path), namespace="test")
    first.add_texts(["庄子思想"], metadatas=[{"school": "taoist"}], ids=["zhuangzi"])
    second = LocalVectorStore(HashingEmbeddings(dim=64), str(path), namespace="test")
    assert second.count() == 1
    doc, _ = second.similarity_search_with_score("庄子思想", k=1)[0]
    assert doc.metadata["school"] == "taoist"


def test_b05_filter_by_metadata(store):
    """B-05: metadata filter 应仅返回匹配记录。"""
    store.add_texts(["斯多葛", "道家"], metadatas=[{"school": "stoic"}, {"school": "taoist"}])
    results = store.similarity_search("哲学", k=5, filter={"school": "taoist"})
    assert len(results) == 1
    assert results[0].metadata["school"] == "taoist"


def test_b06_clear_removes_all_records(store):
    """B-06: clear 应清空记录。"""
    store.add_texts(["文本"])
    store.clear()
    assert store.count() == 0
