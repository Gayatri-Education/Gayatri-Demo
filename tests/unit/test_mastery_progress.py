"""Mastery and learning analytics regression test suite.

Verifies fixes for Issue #2:
- Mastery score must NOT rise for arbitrary, junk, or incorrect input.
- Correct evaluated answers increment mastery and topic score.
- Replaying identical event IDs must not re-apply mastery changes (deduplication).
- Weak topics populate on misconceptions / low score and recover on remediation.
- Course and student states are strictly isolated.
- Persistence across process restart / database reload.
"""
from __future__ import annotations

import uuid
from pathlib import Path
import pytest

from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager
from central_platform.models.schema import LearningEvent, PedagogicalAction
from central_platform.rag.service import RAGService
from central_platform.tutor.orchestrator import TutorOrchestrator


def make_event(
    *,
    event_id: str = "evt_test",
    student_id: str = "student_test",
    course_id: str = "course_test",
    module_id: str = "mod_test",
    topic_id: str = "Topic Test",
    correctness: bool | None = None,
    misconception: str | None = None,
) -> LearningEvent:
    return LearningEvent(
        id=event_id,
        student_id=student_id,
        course_id=course_id,
        module_id=module_id,
        topic_id=topic_id,
        prompt="student input",
        response="tutor response",
        action=PedagogicalAction.EVALUATE if correctness is not None else PedagogicalAction.EXPLAIN,
        correctness=correctness,
        misconception=misconception,
    )


def test_ungraded_prompts_do_not_increase_mastery(tmp_path: Path):
    state = LearningStateManager(tmp_path / "mastery.sqlite")
    before = state.get_mastery("student_test", "course_test").overall_mastery

    state.record_event(make_event(event_id="e1", correctness=None))
    state.record_event(make_event(event_id="e2", correctness=None))

    after = state.get_mastery("student_test", "course_test")
    assert after.overall_mastery == before
    assert after.recommended_next_action == "Continue guided practice"


def test_evaluated_correct_answer_increases_mastery_and_topic(tmp_path: Path):
    state = LearningStateManager(tmp_path / "mastery.sqlite")
    before = state.get_mastery("student_test", "course_test").overall_mastery

    state.record_event(make_event(event_id="e_corr", topic_id="Calculus", correctness=True))

    after = state.get_mastery("student_test", "course_test")
    assert round(after.overall_mastery, 2) == round(before + 0.05, 2)
    assert after.topic_mastery.get("Calculus") == 0.55


def test_misconception_decreases_mastery_and_populates_weak_topics(tmp_path: Path):
    state = LearningStateManager(tmp_path / "mastery.sqlite")
    before = state.get_mastery("student_test", "course_test").overall_mastery

    state.record_event(make_event(
        event_id="e_misc",
        topic_id="Logic Gates",
        misconception="NAND/NOR Logic Inversion Error"
    ))

    after = state.get_mastery("student_test", "course_test")
    assert round(after.overall_mastery, 2) == round(before - 0.05, 2)
    assert "NAND/NOR Logic Inversion Error" in after.recent_misconceptions
    assert "Logic Gates" in after.weak_topics
    assert "Remediate" in after.recommended_next_action


def test_evaluated_incorrect_answer_decreases_mastery_and_adds_weak_topic(tmp_path: Path):
    state = LearningStateManager(tmp_path / "mastery.sqlite")
    before = state.get_mastery("student_test", "course_test").overall_mastery

    # Answering wrong drops score and updates topic
    state.record_event(make_event(event_id="e_wrong1", topic_id="Algebra", correctness=False))
    after1 = state.get_mastery("student_test", "course_test")
    assert round(after1.overall_mastery, 2) == round(before - 0.05, 2)
    assert after1.topic_mastery.get("Algebra") == 0.45

    # Second wrong drops below 0.45 threshold -> added to weak_topics
    state.record_event(make_event(event_id="e_wrong2", topic_id="Algebra", correctness=False))
    after2 = state.get_mastery("student_test", "course_test")
    assert round(after2.overall_mastery, 2) == round(before - 0.10, 2)
    assert after2.topic_mastery.get("Algebra") == 0.40
    assert "Algebra" in after2.weak_topics


def test_weak_topics_recovery_on_successful_remediation(tmp_path: Path):
    state = LearningStateManager(tmp_path / "mastery.sqlite")

    # Step 1: Misconception flags weak topic
    state.record_event(make_event(
        event_id="e_misc",
        topic_id="Logic Gates",
        misconception="NAND/NOR Logic Inversion Error"
    ))
    assert "Logic Gates" in state.get_mastery("student_test", "course_test").weak_topics

    # Step 2: Remediate with correct answer -> topic score reaches >= 0.50
    state.record_event(make_event(
        event_id="e_remed",
        topic_id="Logic Gates",
        correctness=True
    ))
    after = state.get_mastery("student_test", "course_test")
    assert "Logic Gates" not in after.weak_topics
    assert len(after.recent_misconceptions) == 0


def test_repeated_event_id_deduplication(tmp_path: Path):
    state = LearningStateManager(tmp_path / "mastery.sqlite")
    before = state.get_mastery("student_test", "course_test").overall_mastery

    # Record event once
    event = make_event(event_id="dup_001", correctness=True)
    state.record_event(event)
    after_first = state.get_mastery("student_test", "course_test").overall_mastery
    assert round(after_first, 2) == round(before + 0.05, 2)

    # Replay same event ID 5 times
    for _ in range(5):
        state.record_event(event)

    after_replays = state.get_mastery("student_test", "course_test").overall_mastery
    assert after_replays == after_first


def test_course_and_student_isolation(tmp_path: Path):
    state = LearningStateManager(tmp_path / "mastery.sqlite")

    # Student 1 in Course A
    state.record_event(make_event(
        event_id="s1_cA",
        student_id="student_1",
        course_id="crs_math",
        topic_id="Calculus",
        correctness=True
    ))

    # Student 1 in Course B should be initial default
    m_s1_cB = state.get_mastery("student_1", "crs_elec")
    assert m_s1_cB.overall_mastery == 0.45
    assert "Calculus" not in m_s1_cB.topic_mastery

    # Student 2 in Course A should be initial default
    m_s2_cA = state.get_mastery("student_2", "crs_math")
    assert m_s2_cA.overall_mastery == 0.45
    assert "Calculus" not in m_s2_cA.topic_mastery


def test_persistence_across_process_restart(tmp_path: Path):
    db_file = tmp_path / "mastery.sqlite"
    state1 = LearningStateManager(db_file)
    state1.record_event(make_event(
        event_id="persist_1",
        student_id="std_p",
        course_id="crs_p",
        topic_id="Linear Algebra",
        correctness=True
    ))
    saved_mastery = state1.get_mastery("std_p", "crs_p").overall_mastery

    # Re-instantiate from same DB file (simulates restart)
    state2 = LearningStateManager(db_file)
    loaded = state2.get_mastery("std_p", "crs_p")
    assert loaded.overall_mastery == saved_mastery
    assert loaded.topic_mastery.get("Linear Algebra") == 0.55


def test_end_to_end_orchestrator_turn_evaluations(tmp_path: Path):
    cs = CourseService()
    rag = RAGService()
    sm = LearningStateManager(tmp_path / "orch_test.sqlite")
    orch = TutorOrchestrator(cs, rag, sm)
    orch.set_active_course("crs_engg_math")

    initial_mastery = sm.get_mastery("student_demo", "crs_engg_math").overall_mastery

    # 1. Junk / conversational prompts must NOT change mastery
    for junk in ["asdfgh qwerty", "hello", "what is 2+2"]:
        orch.process_turn("student_demo", junk)
        assert sm.get_mastery("student_demo", "crs_engg_math").overall_mastery == initial_mastery

    # 2. General conceptual question must NOT change mastery
    orch.process_turn("student_demo", "What is an integrating factor?")
    assert sm.get_mastery("student_demo", "crs_engg_math").overall_mastery == initial_mastery

    # 3. Wrong evaluated answer: "I = e^(3x)"
    orch.process_turn("student_demo", "I = e^(3x)")
    after_wrong = sm.get_mastery("student_demo", "crs_engg_math")
    assert round(after_wrong.overall_mastery, 2) == round(initial_mastery - 0.05, 2)
    assert "Review" in after_wrong.recommended_next_action

    # 4. Correct evaluated answer: "I = e^(2x)"
    orch.process_turn("student_demo", "I = e^(2x)")
    after_correct = sm.get_mastery("student_demo", "crs_engg_math")
    assert round(after_correct.overall_mastery, 2) == round(initial_mastery, 2)
