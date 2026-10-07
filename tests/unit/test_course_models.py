"""Unit tests verifying course packages, metadata, and prerequisite DAG integrity."""
import pytest
from central_platform.courses.service import CourseService
from central_platform.rag.service import RAGService

def test_course_packages_load():
    cs = CourseService()
    courses = cs.list_courses(include_optional=True)
    assert len(courses) >= 3

    math_course = cs.get_course("engineering_mathematics")
    elec_course = cs.get_course("digital_electronics")
    chem_course = cs.get_course("chemistry_optional")

    assert math_course is not None
    assert math_course.code == "MATH201"
    assert math_course.is_optional is False
    assert len(math_course.modules) == 4

    assert elec_course is not None
    assert elec_course.code == "EC202"
    assert elec_course.is_optional is False
    assert len(elec_course.modules) == 4

    assert chem_course is not None
    assert chem_course.is_optional is True

def test_prerequisite_graph_no_cycles():
    cs = CourseService()
    for course in cs.list_courses(include_optional=True):
        modules = {m.id: m for m in course.modules}
        # Check prerequisites reference valid modules
        for m in course.modules:
            for prereq in m.prerequisites:
                assert prereq in modules, f"Prerequisite {prereq} not found in course {course.id}"
                # Prerequisite order must be strictly less than current order
                assert modules[prereq].order < m.order, f"Cycle or backward dependency: {prereq} -> {m.id}"

def test_rag_cards_loaded_correctly():
    rag = RAGService()
    math_cards = rag.get_course_chunk_count("engineering_mathematics")
    elec_cards = rag.get_course_chunk_count("digital_electronics")
    chem_cards = rag.get_course_chunk_count("chemistry_optional")

    assert math_cards >= 4
    assert elec_cards >= 4
    assert chem_cards >= 1
