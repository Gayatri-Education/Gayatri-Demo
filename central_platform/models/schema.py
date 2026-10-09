"""Pydantic models shared across courses, retrieval, tutoring, and progress."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

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
    prerequisites: List[str] = Field(default_factory=list)
    order: int = 0


class Course(BaseModel):
    id: str
    code: str = ""
    title: str
    description: str = ""
    modules: List[Module] = Field(default_factory=list)
    is_active: bool = True
    is_optional: bool = False


class RAGChunk(BaseModel):
    id: str
    source_id: str = ""
    course_id: str
    module_id: Optional[str] = None
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    score: float = 0.0


class MasteryState(BaseModel):
    student_id: str
    course_id: str
    overall_mastery: float = 0.0
    topic_mastery: Dict[str, float] = Field(default_factory=dict)
    weak_topics: List[str] = Field(default_factory=list)
    recent_misconceptions: List[str] = Field(default_factory=list)
    recommended_next_action: str = "Continue guided practice"


class LearningEvent(BaseModel):
    id: str
    student_id: str
    course_id: str
    module_id: Optional[str] = None
    prompt: str
    response: str
    action: PedagogicalAction
    misconception: Optional[str] = None
    correctness: Optional[bool] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class TutorResponse(BaseModel):
    session_id: str
    course_id: str
    action: PedagogicalAction
    message: str
    grounded: bool = False
    evidence_cards: List[RAGChunk] = Field(default_factory=list)
    misconception_identified: Optional[str] = None
    recommended_topic: Optional[str] = None
