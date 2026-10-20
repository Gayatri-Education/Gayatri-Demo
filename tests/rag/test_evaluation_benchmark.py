"""Comparative Evaluation Benchmark: BM25 vs. Semantic vs. Hybrid RAG.

Evaluates retrieval quality across the GayatriAI curriculum dataset using:
- Recall@5
- MRR (Mean Reciprocal Rank)
- nDCG@5 (Normalized Discounted Cumulative Gain)
- Average Retrieval Latency (ms)
- Course-Isolation Violation Rate
"""
from __future__ import annotations

import math
import time
from typing import Dict, List, NamedTuple
import pytest

from central_platform.rag.service import RAGService


class BenchmarkQuery(NamedTuple):
    query: str
    course_id: str
    expected_title_keywords: List[str]
    category: str  # "exact" or "paraphrase"


EVALUATION_DATASET: List[BenchmarkQuery] = [
    # Engineering Mathematics (MATH201)
    BenchmarkQuery(
        query="first-order linear ordinary differential equations integrating factor",
        course_id="crs_engg_math",
        expected_title_keywords=["differential equations"],
        category="exact",
    ),
    BenchmarkQuery(
        query="rate of change problem solution using exponential multiplier",
        course_id="crs_engg_math",
        expected_title_keywords=["differential equations"],
        category="paraphrase",
    ),
    BenchmarkQuery(
        query="definition and properties of the laplace transform s-domain",
        course_id="crs_engg_math",
        expected_title_keywords=["laplace transform"],
        category="exact",
    ),
    BenchmarkQuery(
        query="converting time domain functions into complex frequency domain representation",
        course_id="crs_engg_math",
        expected_title_keywords=["laplace transform"],
        category="paraphrase",
    ),
    BenchmarkQuery(
        query="Fourier series and harmonic analysis of periodic functions",
        course_id="crs_engg_math",
        expected_title_keywords=["fourier series"],
        category="exact",
    ),
    # Digital Electronics (EC202)
    BenchmarkQuery(
        query="universal logic gates NAND and NOR implementation",
        course_id="crs_digital_elec",
        expected_title_keywords=["universal logic gates"],
        category="exact",
    ),
    BenchmarkQuery(
        query="building all fundamental boolean operations using only one type of gate",
        course_id="crs_digital_elec",
        expected_title_keywords=["universal logic gates"],
        category="paraphrase",
    ),
    BenchmarkQuery(
        query="De Morgan's theorems and boolean duality complementation",
        course_id="crs_digital_elec",
        expected_title_keywords=["de morgan"],
        category="exact",
    ),
    BenchmarkQuery(
        query="bubble pushing and inverting sums into products of inverted literals",
        course_id="crs_digital_elec",
        expected_title_keywords=["de morgan"],
        category="paraphrase",
    ),
    BenchmarkQuery(
        query="edge-triggered flip-flops and sequential state elements",
        course_id="crs_digital_elec",
        expected_title_keywords=["flip-flops"],
        category="exact",
    ),
    BenchmarkQuery(
        query="memory storage elements that toggle state on clock signal transitions",
        course_id="crs_digital_elec",
        expected_title_keywords=["flip-flops"],
        category="paraphrase",
    ),
    BenchmarkQuery(
        query="half adders and full adders in combinational arithmetic circuits",
        course_id="crs_digital_elec",
        expected_title_keywords=["adders"],
        category="exact",
    ),
    BenchmarkQuery(
        query="hardware logic for calculating sum bits and carry generation",
        course_id="crs_digital_elec",
        expected_title_keywords=["adders"],
        category="paraphrase",
    ),
]


def _is_relevant(chunk_title: str, expected_keywords: List[str]) -> bool:
    t_lower = chunk_title.lower()
    return any(kw.lower() in t_lower for kw in expected_keywords)


def _compute_ndcg(retrieved_relevance: List[int], k: int = 5) -> float:
    relevance = retrieved_relevance[:k]
    dcg = sum(rel / math.log2(idx + 2) for idx, rel in enumerate(relevance))
    ideal_relevance = sorted(retrieved_relevance, reverse=True)[:k]
    idcg = sum(rel / math.log2(idx + 2) for idx, rel in enumerate(ideal_relevance))
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_retrieval_mode(rag: RAGService, mode: str, k: int = 5) -> Dict[str, float]:
    recalls = []
    rr_scores = []
    ndcgs = []
    latencies = []
    isolation_violations = 0

    for item in EVALUATION_DATASET:
        t0 = time.perf_counter()
        results = rag.query(item.query, item.course_id, top_k=k, mode=mode)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed_ms)

        # Check course isolation
        for r in results:
            if r.course_id not in (item.course_id, rag._id_alias.get(item.course_id)):
                isolation_violations += 1

        relevance_vector = [1 if _is_relevant(r.title, item.expected_title_keywords) else 0 for r in results]

        # Recall@k
        has_hit = 1.0 if any(relevance_vector) else 0.0
        recalls.append(has_hit)

        # Reciprocal Rank (MRR)
        rr = 0.0
        for rank_0, is_rel in enumerate(relevance_vector):
            if is_rel:
                rr = 1.0 / (rank_0 + 1)
                break
        rr_scores.append(rr)

        # nDCG@k
        ndcgs.append(_compute_ndcg(relevance_vector, k=k))

    n = len(EVALUATION_DATASET)
    return {
        "recall_at_5": round(sum(recalls) / n, 4),
        "mrr": round(sum(rr_scores) / n, 4),
        "ndcg_at_5": round(sum(ndcgs) / n, 4),
        "avg_latency_ms": round(sum(latencies) / n, 2),
        "isolation_violations": isolation_violations,
    }


def test_retrieval_benchmark_comparison():
    rag = RAGService()

    bm25_metrics = evaluate_retrieval_mode(rag, "bm25")
    sem_metrics = evaluate_retrieval_mode(rag, "semantic")
    hyb_metrics = evaluate_retrieval_mode(rag, "hybrid")

    print("\n" + "=" * 78)
    print("GAYATRI AI — RETRIEVAL EVALUATION BENCHMARK RESULTS (v4.0.0)")
    print("=" * 78)
    print(f"{'Metric':<25} | {'BM25-only':<14} | {'Semantic-only':<14} | {'Hybrid (RRF)':<14}")
    print("-" * 78)
    print(f"{'Recall@5':<25} | {bm25_metrics['recall_at_5']:<14.4f} | {sem_metrics['recall_at_5']:<14.4f} | {hyb_metrics['recall_at_5']:<14.4f}")
    print(f"{'MRR':<25} | {bm25_metrics['mrr']:<14.4f} | {sem_metrics['mrr']:<14.4f} | {hyb_metrics['mrr']:<14.4f}")
    print(f"{'nDCG@5':<25} | {bm25_metrics['ndcg_at_5']:<14.4f} | {sem_metrics['ndcg_at_5']:<14.4f} | {hyb_metrics['ndcg_at_5']:<14.4f}")
    print(f"{'Avg Latency (ms)':<25} | {bm25_metrics['avg_latency_ms']:<14.2f} | {sem_metrics['avg_latency_ms']:<14.2f} | {hyb_metrics['avg_latency_ms']:<14.2f}")
    print(f"{'Isolation Violations':<25} | {bm25_metrics['isolation_violations']:<14} | {sem_metrics['isolation_violations']:<14} | {hyb_metrics['isolation_violations']:<14}")
    print("=" * 78 + "\n")

    # Invariant assertions:
    # 1. Zero course isolation violations across all modes
    assert bm25_metrics["isolation_violations"] == 0
    assert sem_metrics["isolation_violations"] == 0
    assert hyb_metrics["isolation_violations"] == 0

    # 2. Hybrid RAG must achieve high recall (>= 0.85)
    assert hyb_metrics["recall_at_5"] >= 0.85
    assert hyb_metrics["mrr"] >= 0.70
