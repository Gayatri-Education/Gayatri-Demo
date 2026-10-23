"""Gayatri AI Platform — Course-Independent Socratic Tutor Orchestrator."""
from __future__ import annotations

import logging
import uuid

from central_platform.ai.adapters import SocraticInferenceEngine
from central_platform.courses.service import CourseService
from central_platform.learning.actions import NextActionEngine
from central_platform.learning.state import LearningStateManager
from central_platform.models.schema import LearningEvent, PedagogicalAction, TutorResponse
from central_platform.rag.service import RAGService
from central_platform.tutor.guardrails import redact_leaked_answers

logger = logging.getLogger("gayatri.central_platform.tutor")

class TutorOrchestrator:
    """Coordinates course context, scoped RAG retrieval, Socratic policy, and learner state."""

    def __init__(
        self,
        course_service: CourseService,
        rag_service: RAGService,
        state_manager: LearningStateManager | None = None
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
        session_id: str | None = None
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
        # On ungrounded turns, pass the course's real topic coverage so the
        # reply guides the student toward available material (or their own
        # curriculum) instead of a repetitive generic clarification.
        available_topics: list[str] | None = None
        if not evidence_cards:
            course_topics = self.rag_service.get_course_topic_titles(self.active_course_id)
            if course_topics:
                available_topics = course_topics[:8]

        bot_message = SocraticInferenceEngine.generate_socratic_response(
            course_title=course_title,
            user_prompt=user_prompt,
            action=action,
            evidence_cards=evidence_cards,
            misconception_feedback=mis_feedback,
            evaluation_feedback=eval_result.feedback if correctness is not None else None,
            available_topics=available_topics
        )

        # 4. Anti-Answer-Leakage Invariant Check
        #     During evaluation/remediation the tutor must teach the principle and
        #     elicit the student's own reasoning — never hand over the final numeric
        #     answer carried by the retrieved knowledge cards. Card-sourced answers
        #     are redacted before the turn is committed/persisted.
        if action in (PedagogicalAction.EVALUATE, PedagogicalAction.REMEDIATE):
            raw_bot_message = bot_message
            bot_message, leaked_values = redact_leaked_answers(
                message=bot_message,
                action=action,
                evidence_cards=evidence_cards,
            )
            if leaked_values:
                logger.warning(
                    "Answer-leakage guard redacted final answers %s in a %s turn "
                    "(course=%s, interpreted message %d chars -> %d chars).",
                    leaked_values,
                    action.value,
                    self.active_course_id,
                    len(raw_bot_message),
                    len(bot_message),
                )

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
