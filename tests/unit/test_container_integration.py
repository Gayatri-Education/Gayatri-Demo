"""Unit tests verifying full platform execution from binary container without raw JSON files."""
import pytest
from pathlib import Path
from central_platform.courses.packer import compile_curriculum_container
from central_platform.courses.service import CourseService
from central_platform.rag.service import RAGService
from central_platform.learning.state import LearningStateManager
from central_platform.tutor.orchestrator import TutorOrchestrator
from core.config import COURSES_DIR

def test_full_platform_from_binary_container_only(tmp_path):
    # 1. Compile real courses into binary container
    container_file = tmp_path / "courses.dat"
    compile_curriculum_container(COURSES_DIR, container_file)
    assert container_file.exists()

    # 2. Point to an EMPTY non-existent courses directory to prove zero reliance on raw files
    empty_dir = tmp_path / "non_existent_courses_dir"

    # 3. Initialize CourseService from container only
    cs = CourseService(courses_dir=empty_dir, container_file=container_file)
    courses = cs.list_courses(include_optional=True)
    assert len(courses) >= 3

    math_course = cs.get_course("engineering_mathematics")
    assert math_course is not None
    assert math_course.code == "MATH201"
    assert len(cs.get_modules("engineering_mathematics")) == 4

    elec_course = cs.get_course("digital_electronics")
    assert elec_course is not None
    assert elec_course.code == "EC202"

    # 4. Initialize RAGService from container only
    rag = RAGService(courses_dir=empty_dir, container_file=container_file)
    assert rag.get_course_chunk_count("crs_engg_math") >= 3
    assert rag.get_course_chunk_count("crs_digital_elec") >= 3

    # Retrieval in Math
    math_res = rag.query("differential equations", "crs_engg_math", top_k=2)
    assert len(math_res) > 0
    assert "linear" in math_res[0].content.lower() or "differential" in math_res[0].content.lower()

    # Verify zero cross-course leakage
    cross_res = rag.query("differential equations", "crs_digital_elec", top_k=2)
    for r in cross_res:
        assert "ode" not in r.content.lower()

    # 5. Full Socratic Tutor turn from container only
    sm = LearningStateManager(tmp_path / "state.sqlite")
    orch = TutorOrchestrator(cs, rag, sm)
    orch.set_active_course("crs_digital_elec")

    resp = orch.process_turn("student_demo", "For a NAND gate, the output is 0 when any input is 0")
    assert resp.course_id == "crs_digital_elec"
    assert resp.misconception_identified == "NAND/NOR Logic Inversion Error"
    assert len(resp.evidence_cards) > 0