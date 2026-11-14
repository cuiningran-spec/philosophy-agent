
import pytest

from thinklab_core.embeddings import HashingEmbeddings


def test_embedding_dimension():
    """TC-EMB-01：生成的向量维度应与初始化参数一致。"""
    embeddings = HashingEmbeddings(dim=128)

    vector = embeddings.embed_query("哲学与生活")

    assert len(vector) == 128


def test_empty_text_returns_zero_vector():
    """TC-EMB-02：空文本应返回全零向量。"""
    embeddings = HashingEmbeddings(dim=64)

    vector = embeddings.embed_query("")

    assert len(vector) == 64
    assert all(value == 0.0 for value in vector)


def test_whitespace_text_returns_zero_vector():
    """TC-EMB-03：只有空白字符的文本应返回全零向量。"""
    embeddings = HashingEmbeddings(dim=64)

    vector = embeddings.embed_query("   \n\t ")

    assert all(value == 0.0 for value in vector)


def test_embedding_is_deterministic():
    """TC-EMB-04：相同文本重复向量化，结果应一致。"""
    embeddings = HashingEmbeddings(dim=128)
    text = "自由与责任"

    vector1 = embeddings.embed_query(text)
    vector2 = embeddings.embed_query(text)

    assert vector1 == vector2


def test_non_empty_vector_is_normalized():
    """TC-EMB-05：非空文本生成的向量应完成 L2 归一化。"""
    embeddings = HashingEmbeddings(dim=128)

    vector = embeddings.embed_query("存在主义哲学")

    norm = sum(value * value for value in vector) ** 0.5

    assert norm == pytest.approx(1.0, abs=1e-6)


def test_embed_documents_batch():
    """TC-EMB-06：批量文本应逐条生成向量。"""
    embeddings = HashingEmbeddings(dim=128)
    texts = ["斯多葛主义", "存在主义", "道家思想"]

    vectors = embeddings.embed_documents(texts)

    assert len(vectors) == 3
    assert all(len(vector) == 128 for vector in vectors)


def test_embed_documents_empty_list():
    """TC-EMB-07：空列表输入应返回空列表。"""
    embeddings = HashingEmbeddings(dim=128)

    assert embeddings.embed_documents([]) == []
