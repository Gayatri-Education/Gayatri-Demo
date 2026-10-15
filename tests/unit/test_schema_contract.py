"""Contract and validation tests for central_platform.models.schema."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from central_platform.models.schema import (
    Course,
    LearningEvent,
    MasteryState,
    Module,
    PedagogicalAction,
    RAGChunk,
    TutorResponse,
)


def test_pedagogical_action_enum():
    assert PedagogicalAction.EXPLAIN.value == "explain"
    assert PedagogicalAction.EVALUATE.value == "evaluate"
    assert PedagogicalAction.REMEDIATE.value == "remediate"

    with pytest.raises(ValueError):
        PedagogicalAction("invalid_action")


def test_module_schema():
    mod = Module(id="mod_1", title="Test Module", order=1)
    assert mod.id == "mod_1"
    assert mod.title == "Test Module"
    assert mod.prerequisites == []
    assert mod.order == 1

    # Independent list defaults
    mod2 = Module(id="mod_2", title="Mod 2")
    mod.prerequisites.append("mod_0")
    assert mod2.prerequisites == []


def test_course_schema():
    course = Course(
        id="crs_test",
        code="CS101",
        title="Intro to CS",
        description="Core CS",
        modules=[Module(id="m1", title="Basics", order=1)],
    )
    assert course.id == "crs_test"
    assert len(course.modules) == 1
    assert course.is_active is True

    # JSON roundtrip
    dumped = course.model_dump_json()
    loaded = Course.model_validate_json(dumped)
    assert loaded.id == course.id
    assert loaded.modules[0].title == "Basics"


def test_rag_chunk_schema():
    chunk = RAGChunk(
        id="chk_1",
        course_id="crs_test",
        module_id="m1",
        title="Concept 1",
        content="Important content",
        tags=["basics", "intro"],
        score=0.95,
    )
    assert chunk.id == "chk_1"
    assert chunk.score == 0.95

    # Negative score should fail validation if ge=0.0
    dumped = chunk.model_dump()
    loaded = RAGChunk(**dumped)
    assert loaded.id == chunk.id


def test_mastery_state_schema():
    state = MasteryState(
        student_id="std_1",
        course_id="crs_test",
        overall_mastery=0.75,
        topic_mastery={"Math": 0.8},
        weak_topics=["Algebra"],
        recent_misconceptions=["Linearity error"],
    )
    assert state.overall_mastery == 0.75
    assert state.topic_mastery["Math"] == 0.8

    # Serialization roundtrip
    json_data = state.model_dump_json()
    reloaded = MasteryState.model_validate_json(json_data)
    assert reloaded.student_id == "std_1"
    assert reloaded.weak_topics == ["Algebra"]


def test_learning_event_schema():
    event = LearningEvent(
        id="evt_01",
        student_id="std_1",
        course_id="crs_1",
        module_id="mod_1",
        prompt="Solve x",
        response="Here is how",
        action=PedagogicalAction.EXPLAIN,
        correctness=True,
    )
    assert event.id == "evt_01"
    assert event.action == PedagogicalAction.EXPLAIN
    assert event.correctness is True
    assert event.timestamp is not None


def test_tutor_response_schema():
    resp = TutorResponse(
        session_id="sess_1",
        course_id="crs_1",
        action=PedagogicalAction.EVALUATE,
        message="Good attempt",
        grounded=True,
        evidence_cards=[
            RAGChunk(id="c1", course_id="crs_1", title="Card 1", content="Text")
        ],
    )
    assert resp.grounded is True
    assert len(resp.evidence_cards) == 1
    assert resp.evidence_cards[0].id == "c1"
