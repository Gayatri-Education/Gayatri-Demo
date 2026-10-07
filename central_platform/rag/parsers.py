"""Gayatri AI Platform — Document Parsers."""
from __future__ import annotations

from pathlib import Path
from typing import List
from central_platform.rag.cleaner import DocumentCleaner

class DocumentParserRouter:
    """Routes files to appropriate safe text parsers."""

    @classmethod
    def parse_file(cls, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in (".txt", ".md"):
            return cls._parse_text(path)
        elif suffix == ".pdf":
            return cls._parse_pdf(path)
        elif suffix == ".docx":
            return cls._parse_docx(path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    @staticmethod
    def _parse_text(path: Path) -> str:
        text = path.read_text(encoding="utf-8", errors="replace")
        return DocumentCleaner.clean(text)

    @staticmethod
    def _parse_pdf(path: Path) -> str:
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            pages = []
            for i, page in enumerate(reader.pages):
                extracted = page.extract_text() or ""
                pages.append(extracted)
            return DocumentCleaner.clean("\n".join(pages))
        except Exception:
            # Fallback for plain reading if pypdf unavailable
            return ""

    @staticmethod
    def _parse_docx(path: Path) -> str:
        try:
            import docx
            doc = docx.Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text]
            return DocumentCleaner.clean("\n".join(paragraphs))
        except Exception:
            return ""
