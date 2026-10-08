"""Curriculum Binary Container — In-Memory Serializer & Loader."""
from __future__ import annotations

import json
import logging
import zlib
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("gayatri.central_platform.courses.packer")

MAGIC_HEADER = b"GYTR_CRSE_v4"
OBF_MASK = 0x5A

def compile_curriculum_container(courses_dir: Path, output_file: Path) -> int:
    """Serializes all course folders, modules, and RAG knowledge cards into an obfuscated binary container."""
    bundle: Dict[str, Any] = {}
    if not courses_dir.exists():
        raise FileNotFoundError(f"Courses directory does not exist: {courses_dir}")

    for course_folder in courses_dir.iterdir():
        if course_folder.is_dir():
            folder_data: Dict[str, Any] = {
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
    masked = bytes([b ^ OBF_MASK for b in compressed])
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_bytes(MAGIC_HEADER + masked)
    logger.info("Compiled %d courses into binary container: %s (%d bytes)", len(bundle), output_file, len(masked))
    return len(bundle)

def load_curriculum_container(container_file: Path) -> Dict[str, Any]:
    """Loads courses directly into memory from the binary container without writing files to disk."""
    if not container_file.exists():
        raise FileNotFoundError(f"Container file does not exist: {container_file}")

    data = container_file.read_bytes()
    if not data.startswith(MAGIC_HEADER):
        raise ValueError("Invalid curriculum container header: magic mismatch")

    masked = data[len(MAGIC_HEADER):]
    compressed = bytes([b ^ OBF_MASK for b in masked])
    raw_bytes = zlib.decompress(compressed)
    bundle: Dict[str, Any] = json.loads(raw_bytes.decode("utf-8"))
    return bundle