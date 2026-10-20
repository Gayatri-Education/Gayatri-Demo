"""Gayatri AI Platform — Reciprocal Rank Fusion (RRF) for Hybrid RAG.

Merges ranked candidate lists from disparate retrieval systems (BM25 keyword search
and local dense semantic vector search) using reciprocal rank scoring:
    RRF_score(d) = sum_{r in retrievers} 1 / (k + rank_r(d))
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional
from central_platform.models.schema import RAGChunk
from core.config import RAG_RRF_K, RAG_TOP_K

logger = logging.getLogger("gayatri.central_platform.rag.fusion")


def reciprocal_rank_fusion(
    bm25_results: List[RAGChunk],
    semantic_results: List[RAGChunk],
    k: int = RAG_RRF_K,
    top_k: int = RAG_TOP_K,
) -> List[RAGChunk]:
    """Combines BM25 and semantic retrieval candidates using Reciprocal Rank Fusion.

    Args:
        bm25_results: Ranked candidates from BM25 retriever (0-indexed list).
        semantic_results: Ranked candidates from semantic vector retriever.
        k: Smoothing constant to avoid undue weight on top positions (default: 60).
        top_k: Maximum number of merged results to return.

    Returns:
        Deduplicated list of RAGChunk instances ordered by descending RRF score.
    """
    if k <= 0:
        raise ValueError(f"RRF smoothing constant k must be positive, got {k}")

    # Map chunk_id -> (accumulated_rrf_score, RAGChunk)
    candidates: Dict[str, RAGChunk] = {}
    rrf_scores: Dict[str, float] = {}

    def _process_ranking_list(results: List[RAGChunk], retriever_name: str) -> None:
        seen_in_this_list = set()
        for rank_0, chunk in enumerate(results):
            if chunk.id in seen_in_this_list:
                # Deduplicate repeated chunks within the same candidate list
                continue
            seen_in_this_list.add(chunk.id)

            rank_1 = rank_0 + 1  # 1-indexed rank
            reciprocal_score = 1.0 / (k + rank_1)

            if chunk.id not in candidates:
                candidates[chunk.id] = chunk.model_copy()
                rrf_scores[chunk.id] = 0.0

            rrf_scores[chunk.id] += reciprocal_score

    _process_ranking_list(bm25_results, "BM25")
    _process_ranking_list(semantic_results, "Semantic")

    if not candidates:
        return []

    # Sort candidates by descending RRF score, breaking ties by chunk ID for deterministic ordering
    sorted_ids = sorted(
        candidates.keys(),
        key=lambda cid: (rrf_scores[cid], cid),
        reverse=True,
    )

    fused_results: List[RAGChunk] = []
    for cid in sorted_ids[:top_k]:
        chunk = candidates[cid]
        chunk.score = round(rrf_scores[cid], 6)
        fused_results.append(chunk)

    return fused_results
