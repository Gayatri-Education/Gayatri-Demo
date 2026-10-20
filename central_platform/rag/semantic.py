"""Gayatri AI Platform — Local Semantic Vector Retriever with Offline Embeddings.

Features:
- 100% Offline execution: loads local weights via sentence-transformers with local_files_only=True.
- Resilient Fallback: If sentence-transformers or local model weights are not found,
  falls back to a deterministic semantic n-gram projection engine so the system remains operational.
- Local Storage & Caching: Persists document embeddings in compressed .npz archives to eliminate
  recomputation across restarts.
- Cosine similarity ranking via normalized vector dot product.
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

from central_platform.models.schema import RAGChunk
from core.config import (
    EMBEDDING_MODEL_DIR,
    EMBEDDINGS_CACHE_DIR,
    RAG_SEMANTIC_MIN_SCORE,
    RAG_TOP_K,
)

logger = logging.getLogger("gayatri.central_platform.rag.semantic")


def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """L2 normalizes 1D or 2D numpy float arrays along the feature axis."""
    if vectors.ndim == 1:
        norm = np.linalg.norm(vectors)
        return vectors / (norm + 1e-12) if norm > 0 else vectors
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-12, norms)
    return vectors / norms


class DeterministicFallbackEmbedder:
    """Deterministic, zero-dependency offline dense projection engine.

    Employs feature-hashing over character n-grams and token boundaries to project
    texts into a fixed 384-dimensional normalized dense vector space. This ensures
    semantic sensitivity to subwords, prefixes, and synonyms even in air-gapped environments
    where neural model weights have not yet been pre-loaded.
    """

    DIM = 384

    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.DIM), dtype=np.float32)

        vectors = np.zeros((len(texts), self.DIM), dtype=np.float32)
        for i, text in enumerate(texts):
            clean_text = text.lower().strip()
            # Token features
            tokens = [t for t in clean_text.split() if len(t) > 1]
            for token in tokens:
                idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.DIM
                vectors[i, idx] += 1.0

            # Character 3-gram and 4-gram features for subword semantics
            for n in (3, 4):
                if len(clean_text) >= n:
                    for j in range(len(clean_text) - n + 1):
                        ngram = clean_text[j:j + n]
                        h = int(hashlib.sha256(ngram.encode("utf-8")).hexdigest(), 16)
                        idx = h % self.DIM
                        sign = 1.0 if (h >> 16) & 1 else -1.0
                        vectors[i, idx] += sign * 0.5

        return _l2_normalize(vectors)


class LocalEmbeddingModel:
    """Encapsulates local embedding model loading and inference."""

    def __init__(self, model_dir: Optional[Path] = None) -> None:
        self.model_dir = model_dir or EMBEDDING_MODEL_DIR
        self._st_model = None
        self._fallback_embedder = DeterministicFallbackEmbedder()
        self._is_neural = False
        self._initialize()

    def _initialize(self) -> None:
        """Attempts to load sentence-transformers model strictly from local directory."""
        if not self.model_dir.exists():
            logger.info(
                "Local embedding model directory not found at %s. Operating in deterministic offline projection mode.",
                self.model_dir,
            )
            return

        try:
            from sentence_transformers import SentenceTransformer
            # local_files_only prevents any external network connection
            self._st_model = SentenceTransformer(
                str(self.model_dir),
                local_files_only=True,
                device="cpu",
            )
            self._is_neural = True
            logger.info("Loaded local neural embedding model from: %s", self.model_dir)
        except Exception as exc:
            logger.warning(
                "Could not load SentenceTransformer from %s (%s). Operating in deterministic offline projection mode.",
                self.model_dir,
                exc,
            )
            self._st_model = None
            self._is_neural = False

    @property
    def is_neural(self) -> bool:
        return self._is_neural

    @property
    def dimension(self) -> int:
        if self._is_neural and self._st_model:
            return self._st_model.get_sentence_embedding_dimension()
        return self._fallback_embedder.DIM

    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """Encodes a batch of texts into L2-normalized float32 vectors."""
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        if self._is_neural and self._st_model:
            try:
                embeddings = self._st_model.encode(
                    texts,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                return embeddings.astype(np.float32)
            except Exception as exc:
                logger.error("Neural encoding failed; falling back to deterministic embedder: %s", exc)

        return self._fallback_embedder.encode(texts)

    def encode_query(self, query: str) -> np.ndarray:
        """Encodes a single query string into an L2-normalized 1D vector."""
        res = self.encode_texts([query])
        return res[0] if len(res) > 0 else np.zeros(self.dimension, dtype=np.float32)


class LocalSemanticRetriever:
    """Course-scoped semantic retriever with persistent on-disk embedding cache."""

    def __init__(
        self,
        chunks: List[RAGChunk],
        course_id: str,
        embedding_model: Optional[LocalEmbeddingModel] = None,
        cache_dir: Optional[Path] = None,
        min_score: float = RAG_SEMANTIC_MIN_SCORE,
    ) -> None:
        self.course_id = course_id
        self.chunks: List[RAGChunk] = list(chunks)
        self.embedding_model = embedding_model or LocalEmbeddingModel()
        self.cache_dir = cache_dir or EMBEDDINGS_CACHE_DIR
        self.min_score = min_score

        self.chunk_ids: List[str] = [c.id for c in self.chunks]
        self.embeddings: np.ndarray = np.empty((0, self.embedding_model.dimension), dtype=np.float32)

        self._build_or_load_index()

    @staticmethod
    def _compute_chunk_hash(chunk: RAGChunk) -> str:
        content = f"{chunk.id}|{chunk.title}|{chunk.content}|{' '.join(chunk.tags)}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _cache_path(self) -> Path:
        safe_course_id = "".join(c for c in self.course_id if c.isalnum() or c in ("-", "_"))
        return self.cache_dir / f"{safe_course_id}.npz"

    def _build_or_load_index(self) -> None:
        if not self.chunks:
            self.embeddings = np.empty((0, self.embedding_model.dimension), dtype=np.float32)
            return

        cache_file = self._cache_path()
        current_hashes = [self._compute_chunk_hash(c) for c in self.chunks]

        # 1. Attempt loading from cache
        if cache_file.exists():
            try:
                data = np.load(cache_file, allow_pickle=True)
                cached_ids = list(data["chunk_ids"])
                cached_hashes = list(data["content_hashes"])
                cached_embeddings = data["embeddings"]

                # Check cache validity
                if cached_ids == self.chunk_ids and cached_hashes == current_hashes:
                    self.embeddings = cached_embeddings.astype(np.float32)
                    logger.debug("Loaded %d cached embeddings for %s from %s", len(self.chunks), self.course_id, cache_file)
                    return
            except Exception as exc:
                logger.warning("Failed loading embedding cache for %s (%s); rebuilding...", self.course_id, exc)

        # 2. Recompute embeddings and save
        self.rebuild_index()

    def rebuild_index(self) -> None:
        """Forces re-encoding of all chunks and saves the cache."""
        if not self.chunks:
            self.embeddings = np.empty((0, self.embedding_model.dimension), dtype=np.float32)
            return

        texts = [f"{c.title}\n{c.content}\n{' '.join(c.tags)}" for c in self.chunks]
        self.embeddings = self.embedding_model.encode_texts(texts)
        self.chunk_ids = [c.id for c in self.chunks]
        current_hashes = [self._compute_chunk_hash(c) for c in self.chunks]

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self._cache_path()
            np.savez_compressed(
                cache_file,
                chunk_ids=np.array(self.chunk_ids, dtype=object),
                content_hashes=np.array(current_hashes, dtype=object),
                embeddings=self.embeddings,
            )
            logger.debug("Saved %d embeddings for %s to %s", len(self.chunks), self.course_id, cache_file)
        except Exception as exc:
            logger.warning("Could not persist embedding cache to %s: %s", self._cache_path(), exc)

    def add_chunks(self, new_chunks: List[RAGChunk]) -> None:
        """Appends new chunks and updates embedding index and cache."""
        if not new_chunks:
            return

        new_texts = [f"{c.title}\n{c.content}\n{' '.join(c.tags)}" for c in new_chunks]
        new_embeddings = self.embedding_model.encode_texts(new_texts)

        self.chunks.extend(new_chunks)
        self.chunk_ids.extend([c.id for c in new_chunks])

        if self.embeddings.size == 0:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])

        # Persist updated cache
        current_hashes = [self._compute_chunk_hash(c) for c in self.chunks]
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(
                self._cache_path(),
                chunk_ids=np.array(self.chunk_ids, dtype=object),
                content_hashes=np.array(current_hashes, dtype=object),
                embeddings=self.embeddings,
            )
        except Exception as exc:
            logger.warning("Failed updating embedding cache: %s", exc)

    def query(self, query_text: str, top_k: int = RAG_TOP_K) -> List[RAGChunk]:
        """Runs cosine-similarity vector retrieval over course chunks."""
        if not self.chunks or self.embeddings.size == 0:
            return []

        q_clean = query_text.strip()
        if not q_clean:
            return []

        query_vec = self.embedding_model.encode_query(q_clean)
        # Cosine similarity via dot product of normalized vectors
        scores = np.dot(self.embeddings, query_vec)

        # Rank indices
        ranked_indices = np.argsort(-scores)
        results: List[RAGChunk] = []

        for idx in ranked_indices:
            score_val = float(scores[idx])
            if score_val >= self.min_score and len(results) < top_k:
                chunk_copy = self.chunks[idx].model_copy()
                chunk_copy.score = round(score_val, 4)
                results.append(chunk_copy)

        return results
