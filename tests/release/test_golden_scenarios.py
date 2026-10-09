"""End-to-End Test Suite for All 10 Institutional Golden Demo Scenarios."""
import json
import pytest
from pathlib import Path

from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager
from central_platform.models.schema import PedagogicalAction
from central_platform.rag.service import RAGService
from central_platform.tutor.orchestrator import TutorOrchestrator
from app.portals.teacher.controller import TeacherPortalController
from app.portals.admin.controller import AdminPortalController
from core.config import APP_VERSION, WINDOW_TITLE

@pytest.fixture
def test_env(tmp_path):
    cs = CourseService()
    rag = RAGService()
    sm = LearningStateManager(tmp_path / "golden_learner.sqlite")
    orch = TutorOrchestrator(cs, rag, sm)
    teacher = TeacherPortalController(cs, sm)
    admin = AdminPortalController(cs, rag)
    return {
        "cs": cs,
        "rag": rag,
        "sm": sm,
        "orch": orch,
        "teacher": teacher,
        "admin": admin,
        "tmp_path": tmp_path
    }

def test_scenario_01_first_impression(test_env):
    """Scenario 1: Platform Positioning, Title, and Startup Metadata."""
    assert APP_VERSION == "4.0.0"
    assert "Adaptive Learning Platform" in WINDOW_TITLE
    assert "Chemistry Tutor" not in WINDOW_TITLE

def test_scenario_02_engineering_mathematics(test_env):
    """Scenario 2: Scoped Engineering Mathematics Socratic Turn."""
    orch = test_env["orch"]
    orch.set_active_course("crs_engg_math")
    resp = orch.process_turn("student_demo", "Explain first-order differential equations and integrating factor")

    assert resp.course_id == "crs_engg_math"
    assert resp.grounded is True
    assert len(resp.evidence_cards) > 0
    assert "First-Order Linear Ordinary Differential Equations" in resp.evidence_cards[0].title
    # Zero cross-course leakage
    for card in resp.evidence_cards:
        assert "logic gates" not in card.content.lower()

def test_scenario_03_digital_electronics(test_env):
    """Scenario 3: Scoped Digital Electronics Socratic Turn."""
    orch = test_env["orch"]
    orch.set_active_course("crs_digital_elec")
    resp = orch.process_turn("student_demo", "What is De Morgan's theorem and how is it used?")

    assert resp.course_id == "crs_digital_elec"
    assert resp.grounded is True
    assert len(resp.evidence_cards) > 0
    assert "De Morgan" in resp.evidence_cards[0].title
    # Zero cross-course leakage
    for card in resp.evidence_cards:
        assert "differential" not in card.content.lower()

def test_scenario_04_course_switching_isolation(test_env):
    """Scenario 4: Course Switch Flushes Context and Resets RAG Scope."""
    orch = test_env["orch"]
    # 1. Math query
    orch.set_active_course("crs_engg_math")
    resp_math = orch.process_turn("student_demo", "What is a Laplace transform?")
    assert resp_math.course_id == "crs_engg_math"
    assert "Laplace" in resp_math.evidence_cards[0].title

    # 2. Switch course
    switched = orch.set_active_course("crs_digital_elec")
    assert switched is True
    assert orch.active_course_id == "crs_digital_elec"

    # 3. Electronics query
    resp_elec = orch.process_turn("student_demo", "Explain edge-triggered flip-flops")
    assert resp_elec.course_id == "crs_digital_elec"
    assert "Flip-Flops" in resp_elec.evidence_cards[0].title
    # Verify zero residual math cards
    for card in resp_elec.evidence_cards:
        assert card.course_id in ("crs_digital_elec", "digital_electronics")

def test_scenario_05_adaptive_misconception_remediation(test_env):
    """Scenario 5: Socratic Misconception Diagnosis & Gap Remediation."""
    orch = test_env["orch"]
    orch.set_active_course("crs_digital_elec")
    wrong_prompt = "For a NAND gate, the output is 0 when any input is 0"
    resp = orch.process_turn("student_demo", wrong_prompt)

    assert resp.action == PedagogicalAction.REMEDIATE
    assert resp.misconception_identified == "NAND/NOR Logic Inversion Error"
    assert "NAND produces 0 ONLY when ALL inputs are 1" in resp.message
    # Check learner state was updated
    state = test_env["sm"].get_mastery("student_demo", "crs_digital_elec")
    assert "NAND/NOR Logic Inversion Error" in state.recent_misconceptions

def test_scenario_06_bring_your_curriculum(test_env):
    """Scenario 6: Document Ingestion and Query against Uploaded Material."""
    rag = test_env["rag"]
    fixture = Path("tests/fixtures/sample_control_systems.txt")
    assert fixture.exists()

    custom_id = "crs_sandbox_control"
    ok, msg, count = rag.ingest_document(fixture, custom_id)
    assert ok is True
    assert count >= 2

    # Query newly ingested knowledge
    results = rag.query("Bode plots gain margin and phase margin", custom_id, top_k=2)
    assert len(results) > 0
    assert results[0].course_id == custom_id
    assert "bode" in results[0].content.lower()

def test_scenario_07_student_progress_tracking(test_env):
    """Scenario 7: Mastery State Analytics Retrieval."""
    sm = test_env["sm"]
    state = sm.get_mastery("student_demo", "crs_engg_math")
    assert isinstance(state.overall_mastery, float)
    assert state.course_id == "crs_engg_math"
    assert state.recommended_next_action is not None

def test_scenario_08_teacher_copilot_preview(test_env):
    """Scenario 8: Teacher Cohort Aggregation and Misconception Alerts."""
    teacher = test_env["teacher"]
    cohort = teacher.get_cohort_summary("crs_engg_math")
    assert cohort["is_preview"] is True
    assert cohort["enrolled_count"] > 0
    assert len(cohort["students"]) >= 4
    assert len(cohort["alerts"]) > 0

def test_scenario_09_offline_air_gapped_operation(test_env):
    """Scenario 9: Verification of Zero Network Sockets During Core Flows."""
    from unittest.mock import patch
    def blocked_socket(*args, **kwargs):
        raise OSError("Air-gapped operation active.")

    with patch("socket.create_connection", side_effect=blocked_socket):
        orch = test_env["orch"]
        orch.set_active_course("crs_engg_math")
        resp = orch.process_turn("student_airgapped", "Explain Fourier series periodic functions")
        assert resp.grounded is True
        assert len(resp.evidence_cards) > 0

def test_scenario_10_clean_packaging_artifacts_verification(test_env):
    """Scenario 10: Portable Distribution Package Integrity."""
    zip_path = Path("dist/Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip")
    if not zip_path.exists():
        pytest.skip("Portable package verification requires running scripts/build_demo.py first.")
    assert zip_path.exists(), "Expected portable distribution ZIP in dist/"
    assert zip_path.stat().st_size > 100_000, "Package must be non-empty"
