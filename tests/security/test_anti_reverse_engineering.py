"""Security and Anti-Reverse Engineering Verification Tests."""
import sys
from pathlib import Path
import pytest

from core.obfuscation import enc_str, dec_str
from core.tamper import is_debugger_present, verify_environment_integrity, sanitize_runtime_arguments
from central_platform.courses.packer import (
    compile_curriculum_container,
    load_curriculum_container,
    MAGIC_HEADER,
    CONTAINER_VERSION,
)
from central_platform.learning.actions import NextActionEngine, _RAW_MISCONCEPTIONS, _RAW_RUBRICS
from central_platform.ai.adapters import SocraticInferenceEngine, _RAW_PROMPTS
from core.config import COURSES_DIR

def test_obfuscation_codec_integrity():
    text = "Proprietary Socratic Remediation Template v4"
    encoded = enc_str(text)
    assert isinstance(encoded, bytes)
    assert b"Proprietary" not in encoded
    assert b"Socratic" not in encoded
    assert dec_str(encoded) == text

def test_misconception_rules_obfuscated_in_code():
    # Verify that raw stored constants in actions.py do NOT contain plaintext error tags
    for raw_rule in _RAW_MISCONCEPTIONS:
        assert b"NAND" not in raw_rule[1]
        assert b"De Morgan" not in raw_rule[1]
        assert b"Laplace" not in raw_rule[1]

    # Verify that at runtime, NextActionEngine deobfuscates them properly
    rules = NextActionEngine.MISCONCEPTION_RULES
    assert len(rules) == len(_RAW_MISCONCEPTIONS)
    tags = [r[1] for r in rules]
    assert "NAND/NOR Logic Inversion Error" in tags
    assert "De Morgan Dual Complement Error" in tags
    assert "Laplace Derivative Initial Value Omission" in tags

def test_adapters_prompts_obfuscated_in_code():
    for key, raw_val in _RAW_PROMPTS.items():
        assert b"NAND produces" not in raw_val
        assert b"integrating factor" not in raw_val
        assert b"De Morgan" not in raw_val

    # Verify runtime prompt reconstruction
    nand_prompt = SocraticInferenceEngine._prompt("nand_reflection")
    assert "Input A = 0 and Input B = 1" in nand_prompt

def test_container_cryptographic_integrity(tmp_path):
    container_file = tmp_path / "test_secure_courses.dat"
    count = compile_curriculum_container(COURSES_DIR, container_file)
    assert count >= 3

    raw = container_file.read_bytes()
    assert raw.startswith(MAGIC_HEADER + CONTAINER_VERSION)
    assert b"MATH201" not in raw
    assert b"EC202" not in raw

    # Tamper with encrypted bytes
    tampered = bytearray(raw)
    tampered[-20] ^= 0xAA
    tampered_file = tmp_path / "tampered.dat"
    tampered_file.write_bytes(tampered)

    with pytest.raises(ValueError, match="tampering detected"):
        load_curriculum_container(tampered_file)

def test_tamper_detection_utilities(monkeypatch):
    assert isinstance(is_debugger_present(), bool)
    assert verify_environment_integrity() is True

    # Test argument sanitization
    test_argv = ["Gayatri.exe", "--remote-debugging-port=9222", "--check-startup", "--js-flags=--expose-gc"]
    monkeypatch.setattr(sys, "argv", test_argv)
    sanitize_runtime_arguments()
    assert "--remote-debugging-port=9222" not in sys.argv
    assert "--js-flags=--expose-gc" not in sys.argv
    assert "--check-startup" in sys.argv
