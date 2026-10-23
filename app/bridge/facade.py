"""Gayatri AI Platform — QWebChannel Bridge Facade (async, hardened).

Protocol (v4.0.1+):
- Long-running turns are executed on a QThreadPool *off the Qt UI thread*.
  `sendQuery` / `uploadCurriculum` / `selectAndUploadCurriculum` validate the
  request, enqueue a worker, and return an acknowledgment payload
  (`{"success": true, "queued": true, "ref": ...}`) immediately.
- The completed result or error is delivered asynchronously through the
  `responseReady(str)` / `curriculumIngested(str)` signals (cross-thread queued
  delivery into the web page).
- Errors never leak raw exception text into the UI: exceptions are mapped to
  {code, message, ref} envelopes; the correlation id is linked to full details
  in the application log.

Synchronous companion methods (`process_turn_sync`) exist for headless users
(CLI startup verification and pytest smoke tests) that share the exact same
turn/serialization code path.
"""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager
from central_platform.models.schema import TutorResponse
from central_platform.rag.service import RAGService
from central_platform.tutor.orchestrator import TutorOrchestrator

logger = logging.getLogger("gayatri.app.bridge")

# Ordered: subclasses must be checked before their base classes.
_ERROR_SIGNATURES = (
    (json.JSONDecodeError, "invalid_request"),
    (FileNotFoundError, "resource_missing"),
    (PermissionError, "forbidden"),
    (ValueError, "invalid_request"),
)

_FRIENDLY_MESSAGES = {
    "invalid_request": "The request could not be processed. Try rephrasing it or clearing the session.",
    "resource_missing": "A required resource is unavailable. Verify the file location and try again.",
    "forbidden": "Access was denied. Close other windows using this file and retry.",
    "internal_error": "Something went wrong while processing your request. Please try again shortly.",
}


def _classify_exception(exc: Exception) -> str:
    for exception_class, code in _ERROR_SIGNATURES:
        if isinstance(exc, exception_class):
            return code
    return "internal_error"


def error_payload(
    exc: Exception,
    ref: str | None = None,
    extra: dict | None = None,
) -> dict:
    """Builds the user-facing error envelope; raw details stay in the log."""
    code = _classify_exception(exc)
    reference = ref or f"err_{uuid.uuid4().hex[:8]}"
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": _FRIENDLY_MESSAGES[code],
            "ref": reference,
        },
    }
    if extra:
        payload.update(extra)
    return payload


def build_turn_success_payload(response: TutorResponse) -> dict:
    """Serializes a completed tutor turn into the wire format for the UI."""
    evidence_cards = [
        {
            "id": card.id,
            "title": card.title,
            "content": card.content,
            "tags": card.tags,
            "score": card.score,
        }
        for card in response.evidence_cards
    ]
    return {
        "success": True,
        "session_id": response.session_id,
        "course_id": response.course_id,
        "action": response.action.value,
        "message": response.message,
        "grounded": response.grounded,
        "evidence_cards": evidence_cards,
        "misconception": response.misconception_identified,
        "recommended_topic": response.recommended_topic,
    }


class _TurnWorker(QRunnable):
    """Executes one Socratic turn off the UI thread; reports via signal."""

    def __init__(self, facade: BridgeFacade, prompt: str, student_id: str, ref: str) -> None:
        super().__init__()
        self.setAutoDelete(True)
        self._facade = facade
        self._prompt = prompt
        self._student_id = student_id
        self._ref = ref

    def run(self) -> None:  # worker thread — no widget access here
        try:
            response = self._facade.orchestrator.process_turn(self._student_id, self._prompt)
            payload = build_turn_success_payload(response)
        except Exception as exc:  # noqa: BLE001 - boundary layer: normalize everything
            logger.exception("Turn processing failed (ref=%s).", self._ref)
            payload = error_payload(exc, self._ref)
        payload["ref"] = self._ref
        # Cross-thread: Qt queues this delivery onto the receiving side.
        self._facade.responseReady.emit(json.dumps(payload))


class _IngestWorker(QRunnable):
    """Indexes one uploaded curriculum document off the UI thread."""

    def __init__(self, facade: BridgeFacade, path: Path, course_id: str, ref: str) -> None:
        super().__init__()
        self.setAutoDelete(True)
        self._facade = facade
        self._path = path
        self._course_id = course_id
        self._ref = ref

    def run(self) -> None:  # worker thread
        payload: dict
        try:
            ok, message, chunks = self._facade.rag_service.ingest_document(self._path, self._course_id)
            payload = {
                "success": ok,
                "cancelled": False,
                "message": message,
                "chunks_indexed": chunks,
                "filename": self._path.name,
            }
        except Exception as exc:  # noqa: BLE001 - boundary layer
            logger.exception("Curriculum ingestion failed (ref=%s).", self._ref)
            payload = error_payload(exc, self._ref, extra={"cancelled": False, "chunks_indexed": 0})
        payload["ref"] = self._ref
        self._facade.curriculumIngested.emit(json.dumps(payload))


class BridgeFacade(QObject):
    """Facade registered on QWebChannel exposing backend platform services to UI."""

    # Qt Signals for asynchronous events
    courseChanged = Signal(str)
    responseReady = Signal(str)
    analyticsUpdated = Signal(str)
    curriculumIngested = Signal(str)

    def __init__(
        self,
        course_service: CourseService,
        rag_service: RAGService,
        orchestrator: TutorOrchestrator,
        state_manager: LearningStateManager,
        window: Any | None = None
    ) -> None:
        super().__init__()
        self.course_service = course_service
        self.rag_service = rag_service
        self.orchestrator = orchestrator
        self.state_manager = state_manager
        self.window = window
        # Global pool: shared worker capacity; waitForDone() semantics in tests
        # and interplay with other Qt workers stay coherent.
        self._worker_pool = QThreadPool.globalInstance()

    # ------------------------------------------------------------------
    # Synchronous companions (headless consumers: CLI checks, pytest smoke)
    # ------------------------------------------------------------------
    def process_turn_sync(self, prompt: str, student_id: str = "demo_student") -> str:
        """Runs a Socratic turn inline and returns the same wire payload as
        the async path (validation + error mapping included)."""
        ref = f"turn_{uuid.uuid4().hex[:8]}"
        try:
            if not prompt or not str(prompt).strip():
                raise ValueError("Prompt is empty")
            response = self.orchestrator.process_turn(student_id, prompt)
            payload = build_turn_success_payload(response)
        except Exception as exc:  # noqa: BLE001 - boundary layer
            logger.exception("Synchronous turn failed (ref=%s).", ref)
            payload = error_payload(exc, ref)
        payload["ref"] = ref
        return json.dumps(payload)

    # ------------------------------------------------------------------
    # Course management slots
    # ------------------------------------------------------------------
    @Slot(result=str)
    def listCourses(self) -> str:
        """Returns JSON list of registered courses."""
        try:
            courses = self.course_service.list_courses(include_optional=True)
            data = [
                {
                    "id": course.id,
                    "code": course.code,
                    "title": course.title,
                    "description": course.description,
                    "is_optional": course.is_optional,
                    "module_count": len(course.modules),
                    "card_count": self.rag_service.get_course_chunk_count(course.id)
                }
                for course in courses
            ]
            return json.dumps(data)
        except Exception as exc:  # noqa: BLE001 - boundary layer
            logger.exception("listCourses failed.")
            return json.dumps(error_payload(exc))

    @Slot(str, result=str)
    def switchCourse(self, course_id: str) -> str:
        """Switches active course context and flushes memory."""
        try:
            ok = self.orchestrator.set_active_course(course_id)
            if not ok:
                raise ValueError(f"Unknown course id: {course_id}")

            course = self.course_service.get_course(course_id)
            if course is None:
                raise ValueError(f"Unknown course id: {course_id}")
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
        except Exception as exc:  # noqa: BLE001 - boundary layer
            logger.exception("switchCourse failed (course_id=%s).", course_id)
            return json.dumps(error_payload(exc))

    # ------------------------------------------------------------------
    # Socratic turn slots (async)
    # ------------------------------------------------------------------
    @Slot(str, str, result=str)
    def sendQuery(self, prompt: str, student_id: str = "demo_student") -> str:
        """Enqueues a Socratic turn; the result arrives via responseReady."""
        ref = f"turn_{uuid.uuid4().hex[:8]}"
        try:
            if not prompt or not str(prompt).strip():
                raise ValueError("Prompt is empty")
            self._worker_pool.start(_TurnWorker(self, prompt, student_id, ref))
            return json.dumps({"success": True, "queued": True, "ref": ref})
        except Exception as exc:  # noqa: BLE001 - boundary layer
            logger.exception("sendQuery failed (ref=%s).", ref)
            return json.dumps(error_payload(exc, ref))

    @Slot(str, str, result=str)
    def getAnalytics(self, course_id: str, student_id: str = "demo_student") -> str:
        """Returns learner mastery state."""
        try:
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
        except Exception as exc:  # noqa: BLE001 - boundary layer
            logger.exception("getAnalytics failed (course_id=%s).", course_id)
            return json.dumps(error_payload(exc))

    # ------------------------------------------------------------------
    # Curriculum ingestion slots (async)
    # ------------------------------------------------------------------
    @Slot(str, str, result=str)
    def uploadCurriculum(self, file_path_str: str, course_id: str) -> str:
        """Indexes an explicitly referenced document into course_id (async)."""
        ref = f"ing_{uuid.uuid4().hex[:8]}"
        try:
            path = Path(file_path_str)
            if not path.exists():
                raise FileNotFoundError(f"Document not found: {path.name}")
            self._worker_pool.start(_IngestWorker(self, path, course_id, ref))
            return json.dumps({
                "success": True, "queued": True, "ref": ref, "filename": path.name,
            })
        except Exception as exc:  # noqa: BLE001 - boundary layer
            logger.exception("uploadCurriculum failed (ref=%s).", ref)
            return json.dumps(error_payload(exc, ref, extra={"cancelled": False}))

    @Slot(str, result=str)
    def selectAndUploadCurriculum(self, course_id: str) -> str:
        """Lets the user choose a local curriculum file and indexes it (async).

        Dialog interaction is synchronous (fast), indexing runs on the pool.
        """
        ref = f"ing_{uuid.uuid4().hex[:8]}"
        try:
            from PySide6.QtWidgets import QFileDialog  # deferred: keeps QObject import cost low

            file_path, _ = QFileDialog.getOpenFileName(
                self.window,
                "Select Curriculum Document",
                "",
                "Curriculum files (*.pdf *.docx *.txt *.md)",
            )
            if not file_path:
                return json.dumps({
                    "success": False, "cancelled": True,
                    "message": "Upload cancelled", "chunks_indexed": 0,
                })

            path = Path(file_path)
            self._worker_pool.start(_IngestWorker(self, path, course_id, ref))
            return json.dumps({
                "success": True, "queued": True, "ref": ref,
                "cancelled": False, "filename": path.name,
            })
        except Exception as exc:  # noqa: BLE001 - boundary layer
            logger.exception("selectAndUploadCurriculum failed (ref=%s).", ref)
            return json.dumps(error_payload(exc, ref, extra={"cancelled": False}))

    # ------------------------------------------------------------------
    # Window control slots
    # ------------------------------------------------------------------
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
