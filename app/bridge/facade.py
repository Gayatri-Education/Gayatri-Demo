"""Gayatri AI Platform — QWebChannel Bridge Facade."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from PySide6.QtCore import QObject, Signal, Slot

from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager
from central_platform.rag.service import RAGService
from central_platform.tutor.orchestrator import TutorOrchestrator

logger = logging.getLogger("gayatri.app.bridge")

class BridgeFacade(QObject):
    """Facade registered on QWebChannel exposing backend platform services to UI."""

    # Qt Signals for asynchronous events
    courseChanged = Signal(str)
    responseReady = Signal(str)
    analyticsUpdated = Signal(str)

    def __init__(
        self,
        course_service: CourseService,
        rag_service: RAGService,
        orchestrator: TutorOrchestrator,
        state_manager: LearningStateManager,
        window: Optional[Any] = None
    ) -> None:
        super().__init__()
        self.course_service = course_service
        self.rag_service = rag_service
        self.orchestrator = orchestrator
        self.state_manager = state_manager
        self.window = window

    @Slot(result=str)
    def listCourses(self) -> str:
        """Returns JSON list of registered courses."""
        courses = self.course_service.list_courses(include_optional=True)
        data = [
            {
                "id": c.id,
                "code": c.code,
                "title": c.title,
                "description": c.description,
                "is_optional": c.is_optional,
                "module_count": len(c.modules),
                "card_count": self.rag_service.get_course_chunk_count(c.id)
            }
            for c in courses
        ]
        return json.dumps(data)

    @Slot(str, result=str)
    def switchCourse(self, course_id: str) -> str:
        """Switches active course context and flushes memory."""
        ok = self.orchestrator.set_active_course(course_id)
        if not ok:
            return json.dumps({"success": False, "error": "Invalid course ID"})
        
        course = self.course_service.get_course(course_id)
        self.courseChanged.emit(course_id)
        return json.dumps({
            "success": True,
            "course": {
                "id": course.id,
                "code": course.code,
                "title": course.title,
                "modules": [{"id": m.id, "title": m.title, "order": m.order} for m in course.modules]
            }
        })

    @Slot(str, str, result=str)
    def sendQuery(self, prompt: str, student_id: str = "demo_student") -> str:
        """Processes a Socratic turn."""
        try:
            resp = self.orchestrator.process_turn(student_id, prompt)
            cards_data = [
                {
                    "id": c.id,
                    "title": c.title,
                    "content": c.content,
                    "tags": c.tags,
                    "score": c.score
                }
                for c in resp.evidence_cards
            ]
            result = {
                "success": True,
                "session_id": resp.session_id,
                "course_id": resp.course_id,
                "action": resp.action.value,
                "message": resp.message,
                "grounded": resp.grounded,
                "evidence_cards": cards_data,
                "misconception": resp.misconception_identified,
                "recommended_topic": resp.recommended_topic
            }
            self.responseReady.emit(json.dumps(result))
            return json.dumps(result)
        except Exception as exc:
            logger.error("Bridge sendQuery error: %s", exc)
            return json.dumps({"success": False, "error": str(exc)})

    @Slot(str, str, result=str)
    def getAnalytics(self, course_id: str, student_id: str = "demo_student") -> str:
        """Returns learner mastery state."""
        state = self.state_manager.get_mastery(student_id, course_id)
        return json.dumps({
            "student_id": state.student_id,
            "course_id": state.course_id,
            "overall_mastery": state.overall_mastery,
            "topic_mastery": state.topic_mastery,
            "weak_topics": state.weak_topics,
            "recent_misconceptions": state.recent_misconceptions,
            "recommended_next_action": state.recommended_next_action
        })

    @Slot(str, str, result=str)
    def uploadCurriculum(self, file_path_str: str, course_id: str) -> str:
        """Indexes uploaded document into course_id."""
        from pathlib import Path
        p = Path(file_path_str)
        ok, msg, count = self.rag_service.ingest_document(p, course_id)
        return json.dumps({"success": ok, "message": msg, "chunks_indexed": count})

    # Window Control Slots
    @Slot()
    def minimizeWindow(self) -> None:
        if self.window:
            self.window.showMinimized()

    @Slot()
    def maximizeWindow(self) -> None:
        if self.window:
            if self.window.isMaximized():
                self.window.showNormal()
            else:
                self.window.showMaximized()

    @Slot()
    def closeWindow(self) -> None:
        if self.window:
            self.window.close()