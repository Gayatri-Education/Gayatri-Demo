"""Mastery changes only when an answer has an evaluated learning outcome."""

from central_platform.learning.state import LearningStateManager
from central_platform.models.schema import LearningEvent, PedagogicalAction


def make_event(*, correctness=None, misconception=None):
    return LearningEvent(
        id="evt_test",
        student_id="student_test",
        course_id="course_test",
        prompt="student input",
        response="tutor response",
        action=PedagogicalAction.EVALUATE,
        correctness=correctness,
        misconception=misconception,
    )


def test_ungraded_prompts_do_not_increase_mastery(tmp_path):
    state = LearningStateManager(tmp_path / "mastery.sqlite")
    before = state.get_mastery("student_test", "course_test").overall_mastery

    state.record_event(make_event())
    state.record_event(make_event())

    after = state.get_mastery("student_test", "course_test")
    assert after.overall_mastery == before
    assert after.recommended_next_action == "Continue guided practice"


def test_evaluated_correct_answer_increases_mastery(tmp_path):
    state = LearningStateManager(tmp_path / "mastery.sqlite")
    before = state.get_mastery("student_test", "course_test").overall_mastery

    state.record_event(make_event(correctness=True))

    assert state.get_mastery("student_test", "course_test").overall_mastery == before + 0.05


def test_misconception_decreases_mastery(tmp_path):
    state = LearningStateManager(tmp_path / "mastery.sqlite")
    before = state.get_mastery("student_test", "course_test").overall_mastery

    state.record_event(make_event(misconception="known misconception"))

    after = state.get_mastery("student_test", "course_test")
    assert after.overall_mastery == before - 0.05
    assert "known misconception" in after.recent_misconceptions
