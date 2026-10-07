"""Gayatri AI Platform — Document Security and Sanitization."""
from __future__ import annotations

import os
from pathlib import Path
from core.config import ALLOWED_EXTENSIONS, RAG_MAX_UPLOAD_BYTES

class RAGSecuritySanitizer:
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Strips path traversal attempts and special characters."""
        base = os.path.basename(filename)
        # Keep only alphanumeric, hyphen, underscore, and dot
        clean = "".join(c for c in base if c.isalnum() or c in ("-", "_", "."))
        return clean or "uploaded_document.txt"

    @staticmethod
    def validate_upload(path: Path) -> tuple[bool, str]:
        """Validates file extension and size constraints."""
        if not path.exists():
            return False, "File does not exist"
        
        ext = path.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Extension {ext} not permitted. Allowed: {ALLOWED_EXTENSIONS}"
        
        size = path.stat().st_size
        if size > RAG_MAX_UPLOAD_BYTES:
            return False, f"File size ({size} bytes) exceeds {RAG_MAX_UPLOAD_BYTES} bytes limit"
        
        return True, "Valid"
