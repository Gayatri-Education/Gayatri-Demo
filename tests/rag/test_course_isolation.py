"""RAG Course Isolation and Cross-Contamination Acceptance Tests."""
import pytest
from central_platform.rag.service import RAGService

def test_engineering_mathematics_retrieval_isolation():
    rag = RAGService()
    results = rag.query("integrating factor for differential equations", "engineering_mathematics", top_k=3)
    assert len(results) > 0
    # Top card must be the differential equations card
    assert "differential" in results[0].title.lower() or "differential" in results[0].content.lower()
    for chunk in results:
        assert chunk.course_id == "engineering_mathematics"
        # Zero cross-contamination with digital electronics
        assert "logic gates" not in chunk.content.lower()
        assert "nand" not in chunk.content.lower()

def test_digital_electronics_retrieval_isolation():
    rag = RAGService()
    results = rag.query("universal logic gates NAND and NOR", "digital_electronics", top_k=3)
    assert len(results) > 0
    # Top card must be universal gates card
    assert "universal" in results[0].title.lower() or "nand" in results[0].content.lower()
    for chunk in results:
        assert chunk.course_id == "digital_electronics"
        # Zero cross-contamination with engineering mathematics
        assert "laplace" not in chunk.content.lower()
        assert "fourier" not in chunk.content.lower()

def test_cross_course_query_isolation():
    rag = RAGService()
    # Asking a math query within digital electronics scope must return 0 math cards
    math_in_elec = rag.query("integrating factor for differential equations", "digital_electronics", top_k=3)
    for chunk in math_in_elec:
        assert chunk.course_id == "digital_electronics"
        assert "differential equations" not in chunk.title.lower()

    # Asking an electronics query within math scope must return 0 electronics cards
    elec_in_math = rag.query("De Morgan theorem and logic gates", "engineering_mathematics", top_k=3)
    for chunk in elec_in_math:
        assert chunk.course_id == "engineering_mathematics"
        assert "logic gates" not in chunk.title.lower()

def test_empty_or_nonsense_query_graceful():
    rag = RAGService()
    empty_res = rag.query("", "engineering_mathematics", top_k=3)
    assert empty_res == []
    nonsense_res = rag.query("xyzqwerty12345nonexistent", "engineering_mathematics", top_k=3)
    assert nonsense_res == []