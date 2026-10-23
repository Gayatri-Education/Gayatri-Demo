"""Comprehensive Test Suite for Hybrid RAG (BM25 + Semantic + RRF).

Covers:
- RRF ranking algorithm (weights, deduplication, ties, missing candidates, empty lists).
- BM25-only, Semantic-only, and Hybrid retrieval modes.
- Exact keywords, synonyms, and paraphrased conceptual questions.
- Engineering and mathematical curriculum terminology.
- Empty, nonsense, and out-of-scope query handling.
- Strict course-isolation enforcement under Hybrid RAG.
- Dynamic document ingestion and semantic cache updates.
- Offline model-loading behavior and fallback handling.
- End-to-end integration with the Tutor Orchestrator turn lifecycle.
"""
from __future__ import annotations

from pathlib import Path
import pytest

from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager
from central_platform.models.schema import RAGChunk
from central_platform.rag.fusion import reciprocal_rank_fusion
from central_platform.rag.semantic import (
    DeterministicFallbackEmbedder,
    LocalEmbeddingModel,
    LocalSemanticRetriever,
)
from central_platform.rag.service import BM25Retriever, RAGService
from central_platform.tutor.orchestrator import TutorOrchestrator


# ---------------------------------------------------------------------------
# 1. Reciprocal Rank Fusion (RRF) Unit Tests
# ---------------------------------------------------------------------------

def test_rrf_basic_scoring():
    """Verifies that RRF combines ranks correctly: 1/(k + rank_1) + 1/(k + rank_2)."""
    c1 = RAGChunk(id="c1", course_id="crs_test", title="Chunk 1", content="...")
    c2 = RAGChunk(id="c2", course_id="crs_test", title="Chunk 2", content="...")

    # c1 is rank 1 in BM25, rank 2 in Semantic
    # c2 is rank 2 in BM25, rank 1 in Semantic
    bm25 = [c1, c2]
    sem = [c2, c1]

    fused = reciprocal_rank_fusion(bm25, sem, k=60, top_k=2)
    assert len(fused) == 2
    # Both have rank 1 + rank 2 -> equal RRF score = 1/61 + 1/62
    expected_score = round(1.0 / 61 + 1.0 / 62, 6)
    assert fused[0].score == expected_score
    assert fused[1].score == expected_score


def test_rrf_candidate_overlap_boost():
    """Candidate present in both retrievers should rank higher than candidate present in only one."""
    c_both = RAGChunk(id="c_both", course_id="crs_test", title="Both", content="...")
    c_bm25_only = RAGChunk(id="c_bm25", course_id="crs_test", title="BM25 only", content="...")
    c_sem_only = RAGChunk(id="c_sem", course_id="crs_test", title="Semantic only", content="...")

    bm25 = [c_bm25_only, c_both]  # c_both is rank 2
    sem = [c_both, c_sem_only]    # c_both is rank 1

    fused = reciprocal_rank_fusion(bm25, sem, k=60, top_k=3)
    assert fused[0].id == "c_both"
    # c_both score = 1/62 + 1/61 = 0.032522
    # c_bm25 score = 1/61 = 0.016393
    # c_sem score = 1/62 = 0.016129
    assert fused[0].score > fused[1].score
    assert fused[1].id == "c_bm25"
    assert fused[2].id == "c_sem"


def test_rrf_empty_and_single_retriever_lists():
    """Handles empty inputs gracefully without zero division or index errors."""
    c1 = RAGChunk(id="c1", course_id="crs_test", title="Chunk 1", content="...")

    # Both empty
    assert reciprocal_rank_fusion([], [], k=60) == []

    # One empty
    res_one = reciprocal_rank_fusion([c1], [], k=60)
    assert len(res_one) == 1
    assert res_one[0].id == "c1"
    assert res_one[0].score == round(1.0 / 61, 6)

    res_two = reciprocal_rank_fusion([], [c1], k=60)
    assert len(res_two) == 1
    assert res_two[0].id == "c1"


def test_rrf_duplicate_deduplication():
    """Duplicate instances of the same chunk in a single retriever list are deduplicated."""
    c1 = RAGChunk(id="c1", course_id="crs_test", title="Chunk 1", content="...")
    res = reciprocal_rank_fusion([c1, c1], [c1], k=60)
    assert len(res) == 1
    # Should get rank 1 in BM25 (1/61) + rank 1 in Semantic (1/61)
    assert res[0].score == round(2.0 / 61, 6)


def test_rrf_invalid_k():
    c1 = RAGChunk(id="c1", course_id="crs_test", title="Chunk 1", content="...")
    with pytest.raises(ValueError, match="k must be positive"):
        reciprocal_rank_fusion([c1], [c1], k=0)


# ---------------------------------------------------------------------------
# 2. Local Semantic Retriever & Embedding Engine Tests
# ---------------------------------------------------------------------------

def test_deterministic_fallback_embedder_normalization():
    embedder = DeterministicFallbackEmbedder()
    texts = ["Differential equations and integrating factor", "Logic gates and Boolean algebra"]
    vectors = embedder.encode(texts)

    assert vectors.shape == (2, 384)
    # Verify L2 normalization
    for v in vectors:
        norm = float(v @ v)
        assert pytest.approx(norm, 1e-4) == 1.0


def test_local_semantic_retriever_caching(tmp_path):
    chunks = [
        RAGChunk(id="chk_1", course_id="crs_math", title="ODEs", content="Solving first order linear ODEs."),
        RAGChunk(id="chk_2", course_id="crs_math", title="Laplace", content="Laplace transform s-domain."),
    ]
    cache_dir = tmp_path / "test_embeddings"
    retriever = LocalSemanticRetriever(chunks, "crs_math", cache_dir=cache_dir)

    # Cache file should be created
    cache_file = cache_dir / "crs_math.npz"
    assert cache_file.exists()

    # Re-instantiate retriever: should hit cache without rebuilding
    retriever2 = LocalSemanticRetriever(chunks, "crs_math", cache_dir=cache_dir)
    assert len(retriever2.chunks) == 2
    assert retriever2.embeddings.shape == retriever.embeddings.shape


def test_offline_model_loading_fallback():
    """Verify that pointing to a nonexistent model directory logs cleanly and falls back."""
    fake_path = Path("/nonexistent/model/path/all-MiniLM")
    model = LocalEmbeddingModel(model_dir=fake_path)
    assert model.is_neural is False
    assert model.dimension == 384
    q_vec = model.encode_query("test query")
    assert q_vec.shape == (384,)


# ---------------------------------------------------------------------------
# 3. Hybrid RAG Modes & Course Isolation Tests
# ---------------------------------------------------------------------------

def test_hybrid_rag_exact_keyword_retrieval():
    """Exact keyword query matches relevant card across BM25, Semantic, and Hybrid."""
    rag = RAGService()
    # Engineering Mathematics exact query
    q = "first-order linear ordinary differential equations integrating factor"
    res_bm25 = rag.query(q, "crs_engg_math", mode="bm25")
    res_sem = rag.query(q, "crs_engg_math", mode="semantic")
    res_hyb = rag.query(q, "crs_engg_math", mode="hybrid")

    assert len(res_bm25) > 0
    assert len(res_sem) > 0
    assert len(res_hyb) > 0

    assert "differential" in res_hyb[0].title.lower()


def test_hybrid_rag_synonym_and_paraphrased_query():
    """Conceptual/paraphrased query retrieves relevant card in hybrid mode."""
    rag = RAGService()
    # Paraphrased Digital Electronics query using conceptual terms
    q = "gate inversion duality and complement logic rules"
    res = rag.query(q, "crs_digital_elec", top_k=3, mode="hybrid")

    assert len(res) > 0
    # Top card should be De Morgan or Universal Gates
    titles = [c.title.lower() for c in res]
    assert any("de morgan" in t or "universal" in t for t in titles)


def test_hybrid_rag_course_isolation_enforcement():
    """Hybrid retrieval must never return chunks outside the requested course scope."""
    rag = RAGService()

    # 1. Math query in Digital Electronics scope
    elec_res = rag.query("integrating factor for differential equations", "crs_digital_elec", mode="hybrid")
    for chunk in elec_res:
        assert chunk.course_id in ("crs_digital_elec", "digital_electronics")
        assert "differential equations" not in chunk.title.lower()

    # 2. Electronics query in Math scope
    math_res = rag.query("NAND NOR universal gates", "crs_engg_math", mode="hybrid")
    for chunk in math_res:
        assert chunk.course_id in ("crs_engg_math", "engineering_mathematics")
        assert "logic gates" not in chunk.title.lower()


def test_hybrid_rag_empty_and_nonsense_queries():
    rag = RAGService()
    assert rag.query("", "crs_engg_math", mode="hybrid") == []
    assert rag.query("   ", "crs_engg_math", mode="hybrid") == []
    assert rag.query("asdfghjklqwerty12345nonexistent", "crs_engg_math", mode="hybrid") == []


def test_hybrid_rag_document_ingestion_updates_both_retrievers(tmp_path):
    """Document ingestion must update both BM25 and Semantic retriever indices."""
    rag = RAGService()
    fixture = Path("tests/fixtures/sample_control_systems.txt")
    course_id = "crs_hybrid_control_test"

    ok, msg, count = rag.ingest_document(fixture, course_id)
    assert ok is True
    assert count >= 2

    # Query in BM25 mode
    bm25_res = rag.query("Routh Hurwitz stability criterion", course_id, mode="bm25")
    assert len(bm25_res) > 0

    # Query in Semantic mode
    sem_res = rag.query("Routh Hurwitz stability criterion", course_id, mode="semantic")
    assert len(sem_res) > 0

    # Query in Hybrid mode
    hyb_res = rag.query("Routh Hurwitz stability criterion", course_id, mode="hybrid")
    assert len(hyb_res) > 0
    assert hyb_res[0].course_id == course_id
    assert "routh" in hyb_res[0].content.lower()


# ---------------------------------------------------------------------------
# 4. Tutor Orchestrator Integration
# ---------------------------------------------------------------------------

def test_tutor_orchestrator_integration_with_hybrid_rag(tmp_path):
    """Verifies closed-loop turn execution using Hybrid RAG in the Socratic orchestrator."""
    cs = CourseService()
    rag = RAGService(retrieval_mode="hybrid")
    sm = LearningStateManager(tmp_path / "test_hybrid_tutor.sqlite")
    orch = TutorOrchestrator(cs, rag, sm)

    orch.set_active_course("crs_engg_math")
    resp = orch.process_turn("student_hybrid", "Explain solving first order ordinary differential equations")

    assert resp.grounded is True
    assert len(resp.evidence_cards) > 0
    assert "Differential" in resp.evidence_cards[0].title
    assert resp.course_id == "crs_engg_math"
