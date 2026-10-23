"""Headless startup, CLI flags, and BridgeFacade smoke tests."""
import json
import subprocess
import sys

from app.bridge.facade import BridgeFacade
from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager
from central_platform.rag.service import RAGService
from central_platform.tutor.orchestrator import TutorOrchestrator


def test_cli_version_flag():
    res = subprocess.run([sys.executable, "-m", "app.main", "--version"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Gayatri AI v4.0.1" in res.stdout

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

    # 3. Send Query (synchronous companion: identical wire format as the async path)
    q_res = json.loads(bridge.process_turn_sync("Explain De Morgan's theorem"))
    assert q_res["success"] is True
    assert q_res["course_id"] == "crs_digital_elec"
    assert q_res["grounded"] is True
    assert len(q_res["evidence_cards"]) > 0
    assert "ref" in q_res

    # 4. Get Analytics
    ana = json.loads(bridge.getAnalytics("crs_digital_elec"))
    assert ana["course_id"] == "crs_digital_elec"
    assert "overall_mastery" in ana


def test_bridge_async_send_query_enqueues_and_completes(tmp_path):
    from PySide6.QtCore import QThreadPool

    cs = CourseService()
    rag = RAGService()
    sm = LearningStateManager(tmp_path / "test_bridge_async.sqlite")
    orch = TutorOrchestrator(cs, rag, sm)
    bridge = BridgeFacade(cs, rag, orch, sm)

    ack = json.loads(bridge.sendQuery("Explain Laplace transform"))
    assert ack["success"] is True
    assert ack["queued"] is True
    assert "ref" in ack

    # Worker executes off-thread and finishes without error path.
    pool = QThreadPool.globalInstance()
    assert pool.waitForDone(15000) is True

    # The turn committed a learning event into the persistence layer.
    mastery = sm.get_mastery("demo_student", "crs_engg_math")
    assert mastery.student_id == "demo_student"


def test_bridge_error_mapping_never_leaks_raw_exceptions(tmp_path):
    cs = CourseService()
    rag = RAGService()
    sm = LearningStateManager(tmp_path / "test_bridge_errors.sqlite")
    orch = TutorOrchestrator(cs, rag, sm)
    bridge = BridgeFacade(cs, rag, orch, sm)

    # Empty prompt -> invalid_request envelope, no traceback text.
    err = json.loads(bridge.process_turn_sync("   "))
    assert err["success"] is False
    assert err["error"]["code"] == "invalid_request"
    assert err["error"]["message"]  # friendly message present
    assert "ref" in err["error"]
    assert "Traceback" not in err["error"]["message"]

    # Unknown course -> invalid_request envelope.
    err = json.loads(bridge.switchCourse("definitely_not_a_course"))
    assert err["success"] is False
    assert err["error"]["code"] == "invalid_request"
    assert "Traceback" not in err["error"]["message"]

    # Missing file -> resource_missing envelope.
    err = json.loads(bridge.uploadCurriculum(str(tmp_path / "nope.txt"), "crs_engg_math"))
    assert err["success"] is False
    assert err["error"]["code"] == "resource_missing"
    assert "Traceback" not in err["error"]["message"]
