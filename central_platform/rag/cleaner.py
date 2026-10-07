"""Gayatri AI Platform — Safe Document Cleaners."""
from __future__ import annotations

import re

class DocumentCleaner:
    @staticmethod
    def clean(text: str) -> str:
        """Removes null bytes, control characters, and excess whitespace."""
        if not text:
            return ""
        text = text.replace("\x00", "")
        # Remove non-printable characters except standard whitespace
        text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or (32 <= ord(ch) <= 126) or ord(ch) > 127)
        # Normalize whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
