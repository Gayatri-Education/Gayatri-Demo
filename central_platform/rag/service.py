"""Gayatri AI Platform - Scoped RAG Service with Strict Course Isolation."""
from __future__ import annotations

import json
import logging
import math
import re
import uuid
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set

from central_platform.models.schema import RAGChunk
from central_platform.rag.parsers import DocumentParserRouter
from central_platform.rag.security import RAGSecuritySanitizer
from core.config import COURSES_DIR, COURSES_CONTAINER_FILE, DEFAULT_CHUNK_SIZE, MAX_CHUNKS_PER_DOCUMENT, RAG_TOP_K

logger = logging.getLogger("gayatri.central_platform.rag")

class BM25Retriever:
    """Lightweight in-memory BM25 ranker for atomic concept cards."""

    def __init__(self, chunks: List[RAGChunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.corpus_size = len(chunks)
        self.doc_lengths = []
        self.doc_freqs: Dict[str, int] = Counter()
        self.tokenized_corpus: List[List[str]] = []
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
        return tokens

    def _build_index(self) -> None:
        if not self.chunks:
            self.avg_dl = 0.0
            return
        total_len = 0
        for chunk in self.chunks:
            tokens = self._tokenize(f"{chunk.title} {chunk.content} {' '.join(chunk.tags)}")
            self.tokenized_corpus.append(tokens)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len
            for word in set(tokens):
                self.doc_freqs[word] += 1
        self.avg_dl = total_len / self.corpus_size if self.corpus_size > 0 else 0.0

    def query(self, query_text: str, top_k: int = RAG_TOP_K) -> List[RAGChunk]:
        if not self.chunks:
            return []
        q_tokens = self._tokenize(query_text)
        if not q_tokens:
            return []

        scores = [0.0] * self.corpus_size
        for token in q_tokens:
            df = self.doc_freqs.get(token, 0)
            if df == 0:
                continue
            idf = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))
            for idx, doc_tokens in enumerate(self.tokenized_corpus):
                tf = doc_tokens.count(token)
                if tf == 0:
                    continue
                doc_len = self.doc_lengths[idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_dl))
                scores[idx] += idf * (numerator / denominator)

        ranked_indices = sorted(range(self.corpus_size), key=lambda i: scores[i], reverse=True)
        results: List[RAGChunk] = []
        for idx in ranked_indices:
            if scores[idx] > 0.05 and len(results) < top_k:
                chunk_copy = self.chunks[idx].model_copy()
                chunk_copy.score = round(scores[idx], 4)
                results.append(chunk_copy)
        return results


class RAGService:
    """Manages course-partitioned knowledge indices and document ingestion."""

    def __init__(self, courses_dir: Optional[Path] = None, container_file: Optional[Path] = None) -> None:
        self.courses_dir = courses_dir or COURSES_DIR
        self.container_file = container_file or COURSES_CONTAINER_FILE
        self._course_indices: Dict[str, BM25Retriever] = {}
        self._course_chunks: Dict[str, List[RAGChunk]] = {}
        self._id_alias: Dict[str, str] = {}
        self.reload_all_courses()

    def reload_all_courses(self) -> None:
        """Loads and builds isolated BM25 indices for every course."""
        self._course_indices.clear()
        self._course_chunks.clear()
        self._id_alias.clear()

        # 1. Try binary container first
        if self.container_file and self.container_file.exists():
            try:
                from central_platform.courses.packer import load_curriculum_container
                bundle = load_curriculum_container(self.container_file)
                for folder_name, data in bundle.items():
                    c_data = data.get("course") or {}
                    course_id = c_data.get("id", folder_name)

                    self._id_alias[folder_name] = course_id
                    self._id_alias[course_id] = course_id

                    chunks: List[RAGChunk] = []
                    for item in data.get("cards", []):
                        item_copy = dict(item)
                        item_copy["course_id"] = course_id
                        chunks.append(RAGChunk(**item_copy))

                    retriever = BM25Retriever(chunks)
                    self._course_chunks[course_id] = chunks
                    self._course_indices[course_id] = retriever
                    if folder_name != course_id:
                        self._course_chunks[folder_name] = chunks
                        self._course_indices[folder_name] = retriever
                logger.info("Loaded %d courses into RAG from binary container: %s", len(bundle), self.container_file)
                return
            except Exception as exc:
                logger.warning("Failed loading courses.dat into RAG, falling back to directory: %s", exc)

        # 2. Fall back to raw directory
        if not self.courses_dir or not self.courses_dir.exists():
            return

        for course_folder in self.courses_dir.iterdir():
            if course_folder.is_dir():
                folder_name = course_folder.name
                course_id = folder_name
                course_file = course_folder / "course.json"
                if course_file.exists():
                    try:
                        with open(course_file, "r", encoding="utf-8-sig") as cf:
                            c_data = json.load(cf)
                            if "id" in c_data:
                                course_id = c_data["id"]
                    except Exception:
                        pass
                
                self._id_alias[folder_name] = course_id
                self._id_alias[course_id] = course_id
                self._load_course_cards(course_folder, course_id, folder_name)

    def _load_course_cards(self, course_folder: Path, course_id: str, folder_name: str) -> None:
        rag_dir = course_folder / "rag"
        chunks: List[RAGChunk] = []
        if rag_dir.exists():
            for file_path in rag_dir.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8-sig") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            item["course_id"] = course_id
                            chunks.append(RAGChunk(**item))
                except Exception as exc:
                    logger.error("Failed to parse RAG cards from %s: %s", file_path, exc)

        retriever = BM25Retriever(chunks)
        self._course_chunks[course_id] = chunks
        self._course_indices[course_id] = retriever
        if folder_name != course_id:
            self._course_chunks[folder_name] = chunks
            self._course_indices[folder_name] = retriever

    def query(self, query_text: str, course_id: str, top_k: int = RAG_TOP_K) -> List[RAGChunk]:
        """Strict course-isolated retrieval. Returns only chunks belonging to course_id."""
        retriever = self._course_indices.get(course_id)
        if not retriever:
            canonical = self._id_alias.get(course_id)
            if canonical:
                retriever = self._course_indices.get(canonical)
        if not retriever:
            return []

        results = retriever.query(query_text, top_k=top_k)
        target_canonical = self._id_alias.get(course_id, course_id)

        for r in results:
            card_canonical = self._id_alias.get(r.course_id, r.course_id)
            if card_canonical != target_canonical:
                raise RuntimeError(f"RAG Isolation Violation: chunk {r.id} ({card_canonical}) leaked into {course_id} ({target_canonical})")
        return results

    def get_course_chunk_count(self, course_id: str) -> int:
        return len(self._course_chunks.get(course_id, []))

    def ingest_document(self, file_path: Path, course_id: str) -> tuple[bool, str, int]:
        ok, reason = RAGSecuritySanitizer.validate_upload(file_path)
        if not ok:
            return False, reason, 0

        try:
            content = DocumentParserRouter.parse_file(file_path)
            if not content.strip():
                return False, "Document contains no readable text", 0

            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            new_chunks: List[RAGChunk] = []
            source_id = f"src_{uuid.uuid4().hex[:8]}"

            canonical_id = self._id_alias.get(course_id, course_id)
            self._id_alias[course_id] = canonical_id

            for i, para in enumerate(paragraphs[:MAX_CHUNKS_PER_DOCUMENT]):
                title = para.split("\n")[0][:60]
                chunk = RAGChunk(
                    id=f"chk_up_{uuid.uuid4().hex[:8]}",
                    source_id=source_id,
                    course_id=canonical_id,
                    title=f"Custom: {title}",
                    content=para,
                    tags=["custom_upload", RAGSecuritySanitizer.sanitize_filename(file_path.name)]
                )
                new_chunks.append(chunk)

            existing = self._course_chunks.setdefault(canonical_id, [])
            existing.extend(new_chunks)
            retriever = BM25Retriever(existing)
            self._course_indices[canonical_id] = retriever
            self._course_indices[course_id] = retriever

            return True, f"Successfully indexed {len(new_chunks)} knowledge cards", len(new_chunks)
        except Exception as exc:
            logger.error("Document ingestion error: %s", exc)
            return False, str(exc), 0