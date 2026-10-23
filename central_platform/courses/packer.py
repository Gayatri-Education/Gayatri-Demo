"""Curriculum Binary Container — Cryptographic Authenticated Serializer & Loader."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import zlib
from pathlib import Path
from typing import Any

logger = logging.getLogger("gayatri.central_platform.courses.packer")

MAGIC_HEADER = b"GYTR_CRSE_v4"
CONTAINER_VERSION = b"\x02"
SALT_SIZE = 16
MAC_SIZE = 32
PBKDF2_ROUNDS = 10000

# Legacy fallback mask
OBF_MASK = 0x5A


def _get_container_seed() -> bytes:
    """Dynamically reconstructs cryptographic key material from non-contiguous byte constants.

    Prevents static string extraction and signature harvesting in compiled binary distributions.
    """
    c1 = bytes([0x47, 0x59, 0x54, 0x52, 0x49, 0x5F, 0x41, 0x44, 0x41, 0x50, 0x54])
    c2 = bytes([b ^ 0x6C for b in [0x09, 0x05, 0x0D, 0x1E, 0x0A, 0x05, 0x00, 0x1E]])
    c3 = bytes([b ^ 0x53 for b in [0x30, 0x36, 0x30, 0x27, 0x26, 0x36, 0x31, 0x33]])
    h = hashlib.sha256(c1)
    h.update(c2)
    h.update(c3)
    return h.digest()


def _derive_keys(salt: bytes) -> tuple[bytes, bytes]:
    """Derives distinct 256-bit encryption and authentication keys using PBKDF2-HMAC-SHA256."""
    seed = _get_container_seed()
    derived = hashlib.pbkdf2_hmac("sha256", seed, salt, PBKDF2_ROUNDS, dklen=64)
    return derived[:32], derived[32:64]


def _apply_keystream(data: bytes, enc_key: bytes, salt: bytes) -> bytes:
    """CTR-mode stream cipher using HMAC-SHA256 keystream blocks."""
    block_size = 32
    num_blocks = (len(data) + block_size - 1) // block_size
    keystream = bytearray()
    for block_idx in range(num_blocks):
        counter_bytes = block_idx.to_bytes(8, byteorder="big")
        keystream.extend(hmac.digest(enc_key, salt + counter_bytes, "sha256"))
    return bytes(b ^ k for b, k in zip(data, keystream[:len(data)], strict=True))


def compile_curriculum_container(courses_dir: Path, output_file: Path) -> int:
    """Serializes all course folders, modules, and RAG knowledge cards into an authenticated binary container."""
    bundle: dict[str, Any] = {}
    if not courses_dir.exists():
        raise FileNotFoundError(f"Courses directory does not exist: {courses_dir}")

    for course_folder in courses_dir.iterdir():
        if course_folder.is_dir():
            folder_data: dict[str, Any] = {
                "course": None,
                "modules": [],
                "cards": [],
                "golden_queries": []
            }
            # 1. Course definition
            course_file = course_folder / "course.json"
            if course_file.exists():
                folder_data["course"] = json.loads(course_file.read_text(encoding="utf-8-sig"))

            # 2. Modules
            modules_file = course_folder / "modules.json"
            if modules_file.exists():
                folder_data["modules"] = json.loads(modules_file.read_text(encoding="utf-8-sig"))

            # 3. Golden queries
            gq_file = course_folder / "golden_queries.json"
            if gq_file.exists():
                folder_data["golden_queries"] = json.loads(gq_file.read_text(encoding="utf-8-sig"))

            # 4. RAG cards
            rag_dir = course_folder / "rag"
            if rag_dir.exists():
                for card_file in rag_dir.glob("*.json"):
                    card_data = json.loads(card_file.read_text(encoding="utf-8-sig"))
                    if isinstance(card_data, list):
                        folder_data["cards"].extend(card_data)
                    elif isinstance(card_data, dict):
                        folder_data["cards"].append(card_data)

            bundle[course_folder.name] = folder_data

    raw_bytes = json.dumps(bundle, ensure_ascii=False).encode("utf-8")
    compressed = zlib.compress(raw_bytes, level=9)

    # Cryptographic hardening: Random Salt + PBKDF2 + CTR stream cipher + HMAC-SHA256
    salt = os.urandom(SALT_SIZE)
    enc_key, hmac_key = _derive_keys(salt)
    ciphertext = _apply_keystream(compressed, enc_key, salt)
    mac = hmac.digest(hmac_key, salt + ciphertext, "sha256")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    payload = MAGIC_HEADER + CONTAINER_VERSION + salt + mac + ciphertext
    output_file.write_bytes(payload)
    logger.info("Compiled %d courses into cryptographic container: %s (%d bytes)", len(bundle), output_file, len(payload))
    return len(bundle)


def load_curriculum_container(container_file: Path) -> dict[str, Any]:
    """Loads courses directly into memory from the authenticated container without writing files to disk."""
    if not container_file.exists():
        raise FileNotFoundError(f"Container file does not exist: {container_file}")

    data = container_file.read_bytes()
    if not data.startswith(MAGIC_HEADER):
        raise ValueError("Invalid curriculum container header: magic mismatch")

    after_magic = data[len(MAGIC_HEADER):]

    # Authenticated v2 container format
    if after_magic.startswith(CONTAINER_VERSION):
        offset = len(CONTAINER_VERSION)
        salt = after_magic[offset:offset + SALT_SIZE]
        offset += SALT_SIZE
        expected_mac = after_magic[offset:offset + MAC_SIZE]
        offset += MAC_SIZE
        ciphertext = after_magic[offset:]

        if len(salt) != SALT_SIZE or len(expected_mac) != MAC_SIZE:
            raise ValueError("Curriculum container payload truncated or corrupt")

        enc_key, hmac_key = _derive_keys(salt)
        computed_mac = hmac.digest(hmac_key, salt + ciphertext, "sha256")
        if not hmac.compare_digest(expected_mac, computed_mac):
            raise ValueError("Container integrity check failed: tampering detected")

        compressed = _apply_keystream(ciphertext, enc_key, salt)
        raw_bytes = zlib.decompress(compressed)
        bundle: dict[str, Any] = json.loads(raw_bytes.decode("utf-8"))
        return bundle

    # Legacy v1 fallback container format (single-byte XOR)
    compressed = bytes([b ^ OBF_MASK for b in after_magic])
    raw_bytes = zlib.decompress(compressed)
    bundle = json.loads(raw_bytes.decode("utf-8"))
    return bundle
