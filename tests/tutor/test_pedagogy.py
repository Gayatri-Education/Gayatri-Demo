"""Tutor Orchestrator, Adaptive Pedagogy, and Misconception Diagnosis Tests."""
import pytest
from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager
from central_platform.models.schema import PedagogicalAction
from central_platform.rag.service import RAGService
from central_platform.tutor.orchestrator import TutorOrchestrator

@pytest.fixture
def orchestrator(tmp_path):
    cs = CourseService()
    rag = RAGService()
    db_file = tmp_path / "test_learner.sqlite"
    sm = LearningStateManager(db_file)
    return TutorOrchestrator(cs, rag, sm)

def test_socratic_explanation_flow(orchestrator):
    orchestrator.set_active_course("crs_engg_math")
    resp = orchestrator.process_turn("student_01", "What is an integrating factor in first-order differential equations?")

    assert resp.course_id == "crs_engg_math"
    assert resp.action == PedagogicalAction.EXPLAIN
    assert resp.grounded is True
    assert len(resp.evidence_cards) > 0
    assert "First-Order Linear Ordinary Differential Equations" in resp.evidence_cards[0].title
    assert "Socratic Comprehension Check" in resp.message
    assert "?" in resp.message

def test_misconception_detection_and_remediation(orchestrator):
    orchestrator.set_active_course("crs_digital_elec")
    prompt = "For a NAND gate, the output is 0 when any input is 0"
    resp = orchestrator.process_turn("student_01", prompt)

    assert resp.course_id == "crs_digital_elec"
    assert resp.action == PedagogicalAction.REMEDIATE
    assert resp.misconception_identified == "NAND/NOR Logic Inversion Error"
    assert "Misconception Identified" in resp.message
    assert "NAND produces 0 ONLY when ALL inputs are 1" in resp.message

    mastery = orchestrator.state_manager.get_mastery("student_01", "crs_digital_elec")
    assert "NAND/NOR Logic Inversion Error" in mastery.recent_misconceptions
    assert "Remediate" in mastery.recommended_next_action

def test_tutor_course_switching(orchestrator):
    # Start in Engineering Mathematics
    orchestrator.set_active_course("crs_engg_math")
    resp_math = orchestrator.process_turn("student_01", "Explain Laplace transform")
    assert resp_math.course_id == "crs_engg_math"
    assert "Laplace" in resp_math.evidence_cards[0].title

    # Switch to Digital Electronics
    ok = orchestrator.set_active_course("crs_digital_elec")
    assert ok is True
    resp_elec = orchestrator.process_turn("student_01", "Explain flip flops and sequential circuits")
    assert resp_elec.course_id == "crs_digital_elec"
    assert "Flip-Flops" in resp_elec.evidence_cards[0].title
    # Zero math cards in electronics turn
    for card in resp_elec.evidence_cards:
        assert card.course_id in ("crs_digital_elec", "digital_electronics")