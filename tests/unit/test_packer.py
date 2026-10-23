"""Unit tests for Curriculum Binary Container Serializer and Loader."""
from pathlib import Path

import pytest

from central_platform.courses.packer import (
    CONTAINER_VERSION,
    MAGIC_HEADER,
    compile_curriculum_container,
    load_curriculum_container,
)
from core.config import COURSES_CONTAINER_FILE


def _make_sample_courses_dir(tmp_path: Path) -> Path:
    """Creates a temporary sample course directory for packaging tests."""
    courses_dir = tmp_path / "sample_curricula"
    c_dir = courses_dir / "sample_math"
    c_dir.mkdir(parents=True, exist_ok=True)
    (c_dir / "course.json").write_text(
        '{"id": "crs_sample_math", "code": "SMP201", "title": "Sample Advanced Mathematics", "is_active": true}',
        encoding="utf-8"
    )
    (c_dir / "modules.json").write_text(
        '[{"id": "mod_smp_01", "title": "Sample Differential Module"}]',
        encoding="utf-8"
    )
    rag_dir = c_dir / "rag"
    rag_dir.mkdir(parents=True, exist_ok=True)
    (rag_dir / "cards.json").write_text(
        '[{"id": "card_01", "title": "Sample Theorem Card", "content": "Proprietary calculus formulas and derivations", "tags": ["math"]}]',
        encoding="utf-8"
    )
    return courses_dir

def test_compile_and_load_curriculum_container(tmp_path):
    sample_dir = _make_sample_courses_dir(tmp_path)
    output_dat = tmp_path / "test_courses.dat"
    count = compile_curriculum_container(sample_dir, output_dat)
    assert count == 1
    assert output_dat.exists()
    assert output_dat.stat().st_size > 0

    # Test obfuscation: Plaintext strings should NOT appear in raw bytes
    raw_content = output_dat.read_bytes()
    assert b"Sample Advanced Mathematics" not in raw_content
    assert b"Proprietary calculus formulas" not in raw_content
    assert raw_content.startswith(MAGIC_HEADER + CONTAINER_VERSION)

    # Test load
    bundle = load_curriculum_container(output_dat)
    assert len(bundle) == 1
    assert "sample_math" in bundle
    math_data = bundle["sample_math"]
    assert math_data["course"]["code"] == "SMP201"
    assert len(math_data["modules"]) == 1
    assert len(math_data["cards"]) == 1

def test_production_container_loading():
    """Verifies that the release distribution binary container loads cleanly in-memory."""
    assert COURSES_CONTAINER_FILE.exists()
    bundle = load_curriculum_container(COURSES_CONTAINER_FILE)
    assert len(bundle) >= 3
    assert "engineering_mathematics" in bundle
    assert "digital_electronics" in bundle

    math_data = bundle["engineering_mathematics"]
    assert math_data["course"]["code"] == "MATH201"
    assert len(math_data["modules"]) == 4
    assert len(math_data["cards"]) >= 3

def test_corrupt_header_rejection(tmp_path):
    corrupt_dat = tmp_path / "corrupt.dat"
    corrupt_dat.write_bytes(b"CORRUPT_HEADER_XYZ" + b"\x00" * 20)
    with pytest.raises(ValueError, match="magic mismatch"):
        load_curriculum_container(corrupt_dat)

def test_missing_file_rejection(tmp_path):
    missing_dat = tmp_path / "non_existent.dat"
    with pytest.raises(FileNotFoundError):
        load_curriculum_container(missing_dat)

def test_tamper_detection_rejection(tmp_path):
    sample_dir = _make_sample_courses_dir(tmp_path)
    output_dat = tmp_path / "tamper_test.dat"
    compile_curriculum_container(sample_dir, output_dat)

    raw = bytearray(output_dat.read_bytes())
    # Flip a byte in the encrypted payload
    raw[-10] ^= 0xFF
    output_dat.write_bytes(raw)

    with pytest.raises(ValueError, match="tampering detected"):
        load_curriculum_container(output_dat)
