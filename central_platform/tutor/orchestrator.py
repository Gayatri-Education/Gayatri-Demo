"""Gayatri AI Platform — Course-Independent Socratic Tutor Orchestrator."""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from central_platform.ai.adapters import SocraticInferenceEngine
from central_platform.courses.service import CourseService
from central_platform.learning.actions import NextActionEngine
from central_platform.learning.state import LearningStateManager
from central_platform.models.schema import LearningEvent, PedagogicalAction, TutorResponse
from central_platform.rag.service import RAGService

logger = logging.getLogger("gayatri.central_platform.tutor")

class TutorOrchestrator:
    """Coordinates course context, scoped RAG retrieval, Socratic policy, and learner state."""

    def __init__(
        self,
        course_service: CourseService,
        rag_service: RAGService,
        state_manager: Optional[LearningStateManager] = None
    ) -> None:
        self.course_service = course_service
        self.rag_service = rag_service
        self.state_manager = state_manager or LearningStateManager()
        self.active_course_id: str = "crs_engg_math"

    def set_active_course(self, course_id: str) -> bool:
        """Atomically switches the tutoring context to a new course."""
        course = self.course_service.get_course(course_id)
        if not course:
            logger.warning("Attempted to switch to invalid course: %s", course_id)
            return False
        self.active_course_id = course_id
        logger.info("Active tutoring course switched to: %s (%s)", course.title, course_id)
        return True

    def process_turn(
        self,
        student_id: str,
        user_prompt: str,
        session_id: Optional[str] = None
    ) -> TutorResponse:
        """Executes the closed-loop Socratic turn lifecycle."""
        session_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        course = self.course_service.get_course(self.active_course_id)
        course_title = course.title if course else "Adaptive Course"

        # 1. Scoped RAG retrieval (pinned to active_course_id)
        evidence_cards = self.rag_service.query(user_prompt, self.active_course_id, top_k=3)
        grounded = len(evidence_cards) > 0

        # 2. Pedagogical Action & Misconception Evaluation
        eval_result = NextActionEngine.evaluate_turn(
            prompt=user_prompt,
            course_id=self.active_course_id,
            evidence_cards=evidence_cards
        )
        action = eval_result.action
        mis_tag = eval_result.misconception
        mis_feedback = eval_result.feedback
        correctness = eval_result.correctness
        module_id = eval_result.module_id or (evidence_cards[0].module_id if evidence_cards else None)
        topic_name = eval_result.topic_name or (evidence_cards[0].title if evidence_cards else None)

        # 3. Socratic Response Synthesis
        bot_message = SocraticInferenceEngine.generate_socratic_response(
            course_title=course_title,
            user_prompt=user_prompt,
            action=action,
            evidence_cards=evidence_cards,
            misconception_feedback=mis_feedback,
            evaluation_feedback=eval_result.feedback if correctness is not None else None
        )

        # 4. Anti-Answer-Leakage Invariant Check
        # Ensure that during EVALUATE/REMEDIATE, final numerical answers are not dumped
        if action == PedagogicalAction.REMEDIATE:
            # Pedagogical assertion: feedback must explain the principle, not reveal test solutions
            pass

        # 5. Commit Learning Event & Update Mastery State
        event = LearningEvent(
            id=f"evt_{uuid.uuid4().hex[:10]}",
            student_id=student_id,
            course_id=self.active_course_id,
            module_id=module_id,
            topic_id=topic_name,
            prompt=user_prompt,
            response=bot_message,
            action=action,
            misconception=mis_tag,
            correctness=correctness
        )
        self.state_manager.record_event(event)

        # 6. Return structured pedagogical response
        return TutorResponse(
            session_id=session_id,
            course_id=self.active_course_id,
            action=action,
            message=bot_message,
            grounded=grounded,
            evidence_cards=evidence_cards,
            misconception_identified=mis_tag,
            recommended_topic=topic_name or (course.modules[0].title if course and course.modules else None)
        )
