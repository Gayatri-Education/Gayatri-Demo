"""Unit tests for Curriculum Binary Container Serializer and Loader."""
import pytest
from pathlib import Path
from central_platform.courses.packer import compile_curriculum_container, load_curriculum_container, MAGIC_HEADER
from core.config import COURSES_DIR

def test_compile_and_load_curriculum_container(tmp_path):
    output_dat = tmp_path / "test_courses.dat"
    count = compile_curriculum_container(COURSES_DIR, output_dat)
    assert count >= 3
    assert output_dat.exists()
    assert output_dat.stat().st_size > 0

    # Test obfuscation: Plaintext strings should NOT appear in raw bytes
    raw_content = output_dat.read_bytes()
    assert b"Engineering Mathematics" not in raw_content
    assert b"Differential Equations" not in raw_content
    assert raw_content.startswith(MAGIC_HEADER)

    # Test load
    bundle = load_curriculum_container(output_dat)
    assert len(bundle) == count
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