"""Anti-Answer-Leakage guardrail tests (Invariant step 4 enforcement).

Verifies that:
- evaluation/remediation turns never disclose card-sourced final numeric answers;
- explain turns (which legitimately quote card content) are exempt;
- the guard is precise: principle statements like "NAND produces 0 ONLY when
  ALL inputs are 1" and truth-table values are NOT redacted.
"""
from __future__ import annotations

import pytest

from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager
from central_platform.models.schema import PedagogicalAction, RAGChunk
from central_platform.rag.service import RAGService
from central_platform.tutor.guardrails import (
    REDACTION_NOTICE,
    extract_card_final_answers,
    redact_leaked_answers,
)
from central_platform.tutor.orchestrator import SocraticInferenceEngine, TutorOrchestrator


def _card(content: str, title: str = "Knowledge Card") -> RAGChunk:
    return RAGChunk(id=f"card_{abs(hash(title)) % 10**8}", course_id="crs_test", title=title, content=content)


class TestExtractCardFinalAnswers:
    def test_extracts_phrase_marked_answers(self):
        cards = [
            _card("Compute the support reaction. The final answer is 42."),
            _card("Result should be -15.625 for negative inputs."),
        ]
        answers = extract_card_final_answers(cards)
        assert "42.0" in answers
        assert "-15.625" in answers

    def test_truth_tables_are_not_extracted(self):
        cards = [_card("Truth table: A=0, B=1 -> output is 1. NAND produces 0 ONLY when ALL inputs are 1.")]
        assert extract_card_final_answers(cards) == set()


class TestRedactLeakedAnswers:
    def test_remediation_message_with_card_answer_is_redacted(self):
        card = _card("Solve dy/dx + 2y = 0. The answer is 42.")
        message = "Let's check step TWO first. The answer is 42 for the supporting reaction."
        cleaned, leaked = redact_leaked_answers(message, PedagogicalAction.REMEDIATE, [card])
        assert "42" not in cleaned.replace(REDACTION_NOTICE, "")  # only notice remains
        assert REDACTION_NOTICE in cleaned
        assert leaked == ["42.0"]

    def test_evaluate_message_redacts_multiple_leaks(self):
        card = _card("The answer is 7. The result is 13.5.")
        message = "Answer is 7, and the result is 13.5 — but WHY?"
        cleaned, leaked = redact_leaked_answers(message, PedagogicalAction.EVALUATE, [card])
        assert cleaned.count(REDACTION_NOTICE) == 2
        assert "7" not in cleaned and "13.5" not in cleaned
        assert len(leaked) == 2

    def test_explain_action_is_exempt(self):
        card = _card("The answer is 42.")
        message = "The answer is 42 — full worked derivation follows."
        cleaned, leaked = redact_leaked_answers(message, PedagogicalAction.EXPLAIN, [card])
        assert cleaned == message
        assert leaked == []

    def test_numbers_not_sourced_from_cards_stay(self):
        card = _card("The answer is 42.")
        message = "You applied the factor twice, so the answer is 84. Where do you think the extra factor came from?"
        cleaned, leaked = redact_leaked_answers(message, PedagogicalAction.REMEDIATE, [card])
        # 84 is the student's own arithmetic result, not a card answer: untouched.
        assert "84" in cleaned
        assert "42" not in cleaned
        assert leaked == []

    def test_principle_statements_with_one_or_zero_survive(self):
        card = _card("NAND produces 0 ONLY when ALL inputs are 1.")
        message = "Review the duality: NAND produces 0 ONLY when ALL inputs are 1. What gate pair mirrors this?"
        cleaned, leaked = redact_leaked_answers(message, PedagogicalAction.REMEDIATE, [card])
        assert cleaned == message
        assert leaked == []

    def test_empty_cards_short_circuits(self):
        message = "The answer is 42."
        cleaned, leaked = redact_leaked_answers(message, PedagogicalAction.EVALUATE, [])
        assert cleaned == message
        assert leaked == []


class TestOrchestratorEnforcesInvariant:
    @pytest.fixture
    def orchestrator(self, tmp_path):
        cs = CourseService()
        rag = RAGService()
        sm = LearningStateManager(tmp_path / "test_guardrail.sqlite")
        orch = TutorOrchestrator(cs, rag, sm)
        orch.set_active_course("crs_engg_math")
        return orch

    def test_remediation_turn_never_leaks_card_answer(self, orchestrator, monkeypatch):
        # The NAND duality misconception rubric runs under Digital Electronics.
        orchestrator.set_active_course("crs_digital_elec")
        # Inject an evidence corpus containing an explicit final answer.
        leaking_card = _card(
            "Analyse the NAND duality. Final answer: 42.", title="Universal Gates"
        )
        monkeypatch.setattr(orchestrator.rag_service, "query", lambda *args, **kwargs: [leaking_card])

        # Force the synthesis layer to attempt to disclose the card answer.
        monkeypatch.setattr(
            SocraticInferenceEngine,
            "generate_socratic_response",
            lambda *args, **kwargs: "Misconception Identified. The answer is 42 — recheck your dual gate mapping.",
        )

        prompt = "For a NAND gate, the output is 0 when any input is 0"
        resp = orchestrator.process_turn("student_guard", prompt)

        assert resp.action == PedagogicalAction.REMEDIATE
        assert "42" not in resp.message
        assert REDACTION_NOTICE in resp.message

    def test_explain_turn_still_quotes_card_content(self, orchestrator, monkeypatch):
        leaking_card = _card("Laplace transform pairs. The answer is 42.", title="Laplace Transforms")
        monkeypatch.setattr(orchestrator.rag_service, "query", lambda *args, **kwargs: [leaking_card])
        monkeypatch.setattr(
            SocraticInferenceEngine,
            "generate_socratic_response",
            lambda *args, **kwargs: "### **Laplace Transforms**\n\nThe answer is 42.\n\nSocratic check?",
        )
        prompt = "Explain Laplace transform"
        resp = orchestrator.process_turn("student_guard", prompt)

        assert resp.action == PedagogicalAction.EXPLAIN
        assert "42" in resp.message
        assert REDACTION_NOTICE not in resp.message
