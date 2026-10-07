"""Headless startup, CLI flags, and BridgeFacade smoke tests."""
import subprocess
import sys
import json
import pytest

from app.bridge.facade import BridgeFacade
from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager
from central_platform.rag.service import RAGService
from central_platform.tutor.orchestrator import TutorOrchestrator

def test_cli_version_flag():
    res = subprocess.run([sys.executable, "-m", "app.main", "--version"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Gayatri AI v4.0.0" in res.stdout

def test_cli_check_startup_flag():
    res = subprocess.run([sys.executable, "-m", "app.main", "--check-startup"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "startup verification passed" in res.stdout

def test_bridge_facade_turn_and_course_switching(tmp_path):
    cs = CourseService()
    rag = RAGService()
    sm = LearningStateManager(tmp_path / "test_bridge.sqlite")
    orch = TutorOrchestrator(cs, rag, sm)
    bridge = BridgeFacade(cs, rag, orch, sm)

    # 1. List Courses
    courses_json = bridge.listCourses()
    courses = json.loads(courses_json)
    assert len(courses) >= 2
    ids = [c["id"] for c in courses]
    assert "crs_engg_math" in ids
    assert "crs_digital_elec" in ids

    # 2. Switch Course
    sw_res = json.loads(bridge.switchCourse("crs_digital_elec"))
    assert sw_res["success"] is True
    assert sw_res["course"]["id"] == "crs_digital_elec"

    # 3. Send Query
    q_res = json.loads(bridge.sendQuery("Explain De Morgan's theorem"))
    assert q_res["success"] is True
    assert q_res["course_id"] == "crs_digital_elec"
    assert q_res["grounded"] is True
    assert len(q_res["evidence_cards"]) > 0

    # 4. Get Analytics
    ana = json.loads(bridge.getAnalytics("crs_digital_elec"))
    assert ana["course_id"] == "crs_digital_elec"
    assert "overall_mastery" in ana