"""Security & Air-Gapped Network Audit Tests."""
import re
import socket
from pathlib import Path
from unittest.mock import patch
import pytest

from core.config import BASE_DIR, LOOPBACK_HOST
from central_platform.courses.service import CourseService
from central_platform.rag.service import RAGService
from central_platform.learning.state import LearningStateManager
from central_platform.tutor.orchestrator import TutorOrchestrator

def test_loopback_binding_configuration():
    assert LOOPBACK_HOST == "127.0.0.1"

def test_codebase_zero_public_binding_and_telemetry():
    """Scans all source code for 0.0.0.0 bindings and telemetry URLs."""
    forbidden_patterns = [
        re.compile(r'["\']0\.0\.0\.0["\']'),
        re.compile(r'telemetry|google-analytics|segment\.io|sentry\.io', re.IGNORECASE)
    ]

    py_files = list((BASE_DIR / "app").rglob("*.py")) + \
               list((BASE_DIR / "central_platform").rglob("*.py")) + \
               list((BASE_DIR / "core").rglob("*.py"))

    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8", errors="replace")
        for pat in forbidden_patterns:
            matches = pat.findall(content)
            assert len(matches) == 0, f"Forbidden network pattern {pat.pattern} found in {py_file}"

def test_air_gapped_offline_execution(tmp_path):
    """Simulates complete network disconnection (socket connections blocked)."""
    def blocked_connect(*args, **kwargs):
        raise OSError("Air-gapped mode: Outbound network connections strictly blocked.")

    with patch("socket.create_connection", side_effect=blocked_connect):
        cs = CourseService()
        rag = RAGService()
        sm = LearningStateManager(tmp_path / "offline_state.sqlite")
        orch = TutorOrchestrator(cs, rag, sm)

        # 1. Course Listing works offline
        courses = cs.list_courses()
        assert len(courses) >= 2

        # 2. Math Socratic Turn works offline
        orch.set_active_course("crs_engg_math")
        resp_math = orch.process_turn("std_offline", "Explain differential equations integrating factor")
        assert resp_math.grounded is True
        assert len(resp_math.evidence_cards) > 0

        # 3. Electronics Socratic Turn works offline
        orch.set_active_course("crs_digital_elec")
        resp_elec = orch.process_turn("std_offline", "Explain NAND gate truth table")
        assert resp_elec.grounded is True
        assert len(resp_elec.evidence_cards) > 0