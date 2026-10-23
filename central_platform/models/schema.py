"""Pydantic models shared across courses, retrieval, tutoring, and progress."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class PedagogicalAction(str, Enum):
    """Action selected by the Socratic tutoring policy."""

    EXPLAIN = "explain"
    EVALUATE = "evaluate"
    REMEDIATE = "remediate"


class Module(BaseModel):
    id: str
    course_id: str = ""
    title: str
    description: str = ""
    prerequisites: list[str] = Field(default_factory=list)
    order: int = 0


class Course(BaseModel):
    id: str
    code: str = ""
    title: str
    description: str = ""
    modules: list[Module] = Field(default_factory=list)
    is_active: bool = True
    is_optional: bool = False


class RAGChunk(BaseModel):
    id: str
    source_id: str = ""
    course_id: str
    module_id: str | None = None
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    score: float = 0.0


class MasteryState(BaseModel):
    student_id: str
    course_id: str
    overall_mastery: float = 0.0
    topic_mastery: dict[str, float] = Field(default_factory=dict)
    weak_topics: list[str] = Field(default_factory=list)
    recent_misconceptions: list[str] = Field(default_factory=list)
    recommended_next_action: str = "Continue guided practice"


class LearningEvent(BaseModel):
    id: str
    student_id: str
    course_id: str
    module_id: str | None = None
    topic_id: str | None = None
    prompt: str
    response: str
    action: PedagogicalAction
    misconception: str | None = None
    correctness: bool | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class TutorResponse(BaseModel):
    session_id: str
    course_id: str
    action: PedagogicalAction
    message: str
    grounded: bool = False
    evidence_cards: list[RAGChunk] = Field(default_factory=list)
    misconception_identified: str | None = None
    recommended_topic: str | None = None
