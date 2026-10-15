"""Gayatri AI Platform — Runtime Dynamic Deobfuscation Utilities.

Protects proprietary pedagogical prompts, misconception diagnostics, and comprehension
rubrics against static binary string extraction and automated decompilation harvesting.
"""
from __future__ import annotations


def dec_str(encoded_bytes: bytes, key: int = 0x5C) -> str:
    """Decodes obfuscated byte arrays back into runtime strings in-memory only."""
    out = bytearray()
    for i, b in enumerate(encoded_bytes):
        out.append(b ^ ((key + (i * 7)) & 0xFF))
    return out.decode("utf-8")


def enc_str(text: str, key: int = 0x5C) -> bytes:
    """Helper to obfuscate strings into byte literals."""
    raw = text.encode("utf-8")
    out = bytearray()
    for i, b in enumerate(raw):
        out.append(b ^ ((key + (i * 7)) & 0xFF))
    return bytes(out)
