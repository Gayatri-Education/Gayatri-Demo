import numpy as np

from central_platform.models.schema import RAGChunk
from central_platform.rag.semantic import LocalSemanticRetriever


def test_embedding_cache_is_pickle_free(tmp_path, monkeypatch):
    chunks = [
        RAGChunk(
            id="chunk_1",
            course_id="test_course",
            title="Test title",
            content="Test embedding cache security.",
        )
    ]

    cache_dir = tmp_path / "embedding_cache"

    retriever = LocalSemanticRetriever(
        chunks,
        "test_course",
        cache_dir=cache_dir,
    )

    cache_file = cache_dir / "test_course.npz"
    assert cache_file.exists()

    with np.load(cache_file, allow_pickle=False) as data:
        assert data["chunk_ids"].dtype.kind == "U"
        assert data["content_hashes"].dtype.kind == "U"
        assert data["embeddings"].dtype.kind == "f"

    original_load = np.load

    def safe_load(*args, **kwargs):
        assert kwargs.get("allow_pickle") is False
        return original_load(*args, **kwargs)

    monkeypatch.setattr(np, "load", safe_load)

    cached_retriever = LocalSemanticRetriever(
        chunks,
        "test_course",
        cache_dir=cache_dir,
    )

    np.testing.assert_array_equal(
        cached_retriever.embeddings,
        retriever.embeddings,
    )
