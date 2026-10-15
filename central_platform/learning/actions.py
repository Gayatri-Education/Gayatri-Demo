"""Gayatri AI Platform — Socratic Next Action & Misconception Engine."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from central_platform.models.schema import PedagogicalAction, RAGChunk


@dataclass
class EvaluationResult:
    """Encapsulates the complete evaluation of a student turn."""
    action: PedagogicalAction
    misconception: Optional[str] = None
    feedback: Optional[str] = None
    correctness: Optional[bool] = None
    module_id: Optional[str] = None
    topic_name: Optional[str] = None

    def __iter__(self):
        """Allows unpacking as (action, misconception, feedback) for backwards compatibility."""
        return iter((self.action, self.misconception, self.feedback))


class NextActionEngine:
    """Evaluates student inputs, diagnoses conceptual misconceptions, and determines next action."""

    # Misconception signatures with associated module and topic mapping
    MISCONCEPTION_RULES: List[Tuple[str, str, str, str, str]] = [
        # Digital Electronics
        (
            r"\b(nand|nor)\b.*(output is 0 when any input is 0|0.*when.*0)",
            "NAND/NOR Logic Inversion Error",
            "Remember that NAND produces 0 ONLY when ALL inputs are 1. If any input is 0, the output is 1.",
            "mod_elec_gates",
            "Logic Gates & Universal Realizations"
        ),
        (
            r"\b(de morgan|demorgan)\b.*(\+.*becomes.*\+|and.*becomes.*and)",
            "De Morgan Dual Complement Error",
            "De Morgan's theorem swaps operations: the complement of a sum (OR) is the product of complements (AND), i.e., (A + B)' = A' · B'.",
            "mod_elec_bool",
            "Boolean Algebra & Logic Simplification"
        ),
        (
            r"\b(half adder)\b.*(carries 3 bits|has carry in)",
            "Half Adder vs Full Adder Misconception",
            "A Half Adder accepts only two 1-bit inputs (A and B). A Full Adder is required to handle a Carry-In (Cin).",
            "mod_elec_comb",
            "Combinational Logic Circuits"
        ),
        # Engineering Mathematics
        (
            r"\b(linear differential equation)\b.*(y\^2|dy/dx\^2|product of y and dy/dx)",
            "Linearity Violation in Differential Equations",
            "An ODE is linear only if the dependent variable and its derivatives appear to the first power and are not multiplied together.",
            "mod_math_ode",
            "First-Order Differential Equations"
        ),
        (
            r"\blaplace\b.*(derivative.*is s\*f\(s\)|no initial condition)",
            "Laplace Derivative Initial Value Omission",
            "The Laplace transform of f'(t) is s·F(s) - f(0). You must subtract the initial condition f(0).",
            "mod_math_laplace",
            "Laplace Transform & Initial Value Problems"
        ),
        (
            r"\bfourier\b.*(only for periodic functions|applies to everything without period)",
            "Fourier Series Periodicity Constraint",
            "Standard Fourier Series applies strictly to periodic functions over a finite interval. Non-periodic functions require the Fourier Transform.",
            "mod_math_fourier",
            "Fourier Series & Harmonic Analysis"
        )
    ]

    # Specific answer rubrics for Socratic comprehension checks
    ANSWER_RUBRICS: List[Dict[str, Any]] = [
        # Engineering Mathematics: ODE Integrating Factor check
        # Check: Given dy/dx + 2y = e^x, what is the integrating factor I(x)...?
        {
            "course_id": "crs_engg_math",
            "module_id": "mod_math_ode",
            "topic": "First-Order Differential Equations",
            "correct_patterns": [
                r"(?:i\s*(?:\(x\))?\s*=\s*)?e\^\{\s*2x\s*\}",
                r"(?:i\s*(?:\(x\))?\s*=\s*)?e\^\(?2x\)?",
                r"exp\(\s*2x\s*\)",
                r"\be\^2x\b"
            ],
            "incorrect_patterns": [
                r"(?:i\s*(?:\(x\))?\s*=\s*)?e\^\{\s*3x\s*\}",
                r"(?:i\s*(?:\(x\))?\s*=\s*)?e\^\(?3x\)?",
                r"(?:i\s*(?:\(x\))?\s*=\s*)?e\^\(?x\)?",
                r"\be\^3x\b"
            ],
            "correct_feedback": "Correct! The integrating factor is I(x) = e^(∫ 2 dx) = e^(2x). Multiplying through makes the equation d/dx [y · e^(2x)] = e^(3x).",
            "incorrect_feedback": "Incorrect integrating factor. For dy/dx + 2y = e^x, the coefficient is P(x) = 2, so I(x) = e^(∫ P(x)dx) = e^(2x), not e^(3x)."
        },
        # Engineering Mathematics: Laplace transform of e^(at)
        {
            "course_id": "crs_engg_math",
            "module_id": "mod_math_laplace",
            "topic": "Laplace Transform & Initial Value Problems",
            "correct_patterns": [
                r"1\s*/\s*\(\s*s\s*-\s*a\s*\)",
                r"1/\(s-a\)"
            ],
            "incorrect_patterns": [
                r"1\s*/\s*\(\s*s\s*\+\s*a\s*\)",
                r"1\s*/\s*s\b",
                r"s\s*/\s*\(\s*s\s*-\s*a\s*\)"
            ],
            "correct_feedback": "Correct! L{e^(at)} = 1 / (s - a) with convergence requirement s > a.",
            "incorrect_feedback": "Incorrect. L{e^(at)} = ∫₀^∞ e^(-(s-a)t) dt = 1 / (s - a) for s > a."
        },
        # Engineering Mathematics: Fourier coefficients for odd functions
        {
            "course_id": "crs_engg_math",
            "module_id": "mod_math_fourier",
            "topic": "Fourier Series & Harmonic Analysis",
            "correct_patterns": [
                r"\b(?:0|zero|all\s+zero|become\s+0|they\s+are\s+0)\b",
                r"\ba_n\s*=\s*0\b"
            ],
            "incorrect_patterns": [
                r"\b(?:1|one|remain|non-?zero|infinite)\b"
            ],
            "correct_feedback": "Correct! For an odd function f(x), f(x)·cos(nx) is odd, so its integral over a symmetric interval [-L, L] vanishes, yielding a_n = 0.",
            "incorrect_feedback": "Incorrect. For an odd function f(x), the cosine coefficients a_n are always 0 because the integrand f(x)·cos(nx) is odd."
        },
        # Digital Electronics: NAND output for (0, 1)
        {
            "course_id": "crs_digital_elec",
            "module_id": "mod_elec_gates",
            "topic": "Logic Gates & Universal Realizations",
            "correct_patterns": [
                r"\b(?:1|high|true|logic\s*1|output\s*is\s*1)\b"
            ],
            "incorrect_patterns": [
                r"\b(?:0|low|false|logic\s*0|output\s*is\s*0)\b"
            ],
            "correct_feedback": "Correct! When Input A = 0 and Input B = 1, the AND operation produces 0, which the NAND gate inverts to 1.",
            "incorrect_feedback": "Incorrect. A NAND gate outputs 0 ONLY when ALL inputs are 1. Since Input A = 0, the output is 1."
        },
        # Digital Electronics: Boolean Absorption A + AB
        {
            "course_id": "crs_digital_elec",
            "module_id": "mod_elec_bool",
            "topic": "Boolean Algebra & Logic Simplification",
            "correct_patterns": [
                r"^\s*a\s*$",
                r"\ba\s*\(\s*1\s*\+\s*b\s*\)\s*=\s*a\b",
                r"\b(?:simplifies\s+to\s+a|result\s+is\s+a|absorption\s+gives\s+a)\b"
            ],
            "incorrect_patterns": [
                r"^\s*b\s*$",
                r"^\s*ab\s*$",
                r"^\s*a\s*\+\s*b\s*$"
            ],
            "correct_feedback": "Correct! By algebraic factoring, A + AB = A(1 + B) = A(1) = A.",
            "incorrect_feedback": "Incorrect. By the absorption theorem, A + AB = A(1 + B) = A."
        }
    ]

    @classmethod
    def evaluate_turn(
        cls,
        prompt: str,
        course_id: str = "",
        evidence_cards: Optional[List[RAGChunk]] = None
    ) -> EvaluationResult:
        """Comprehensive evaluation of a student turn into action, correctness, and module context."""
        lower = prompt.lower().strip()

        # 1. Check for matching misconception
        for rule in cls.MISCONCEPTION_RULES:
            pattern, tag, feedback, mod_id, topic = rule
            if re.search(pattern, lower, re.IGNORECASE):
                return EvaluationResult(
                    action=PedagogicalAction.REMEDIATE,
                    misconception=tag,
                    feedback=feedback,
                    correctness=False,
                    module_id=mod_id,
                    topic_name=topic
                )

        # 2. Check answer rubrics (preferring active course if specified)
        for rubric in cls.ANSWER_RUBRICS:
            if course_id and rubric["course_id"] != course_id:
                continue

            # Check correct patterns
            for pat in rubric["correct_patterns"]:
                if re.search(pat, lower, re.IGNORECASE):
                    return EvaluationResult(
                        action=PedagogicalAction.EVALUATE,
                        misconception=None,
                        feedback=rubric["correct_feedback"],
                        correctness=True,
                        module_id=rubric["module_id"],
                        topic_name=rubric["topic"]
                    )

            # Check incorrect patterns
            for pat in rubric["incorrect_patterns"]:
                if re.search(pat, lower, re.IGNORECASE):
                    return EvaluationResult(
                        action=PedagogicalAction.EVALUATE,
                        misconception=None,
                        feedback=rubric["incorrect_feedback"],
                        correctness=False,
                        module_id=rubric["module_id"],
                        topic_name=rubric["topic"]
                    )

        # 3. Check for questions or concept exploration (Ungraded)
        question_words = ("what", "how", "explain", "derive", "why", "define", "tell me", "can you", "show me", "describe")
        if any(w in lower for w in question_words) or "?" in prompt:
            fallback_mod = evidence_cards[0].module_id if evidence_cards else None
            fallback_topic = evidence_cards[0].title if evidence_cards else None
            return EvaluationResult(
                action=PedagogicalAction.EXPLAIN,
                misconception=None,
                feedback=None,
                correctness=None,
                module_id=fallback_mod,
                topic_name=fallback_topic
            )

        # 4. Check for greetings / conversational / junk (Ungraded)
        if re.search(r"^(hello|hi|hey|test|testing|asdfgh|qwerty|what\s+is\s+2\s*\+\s*2)\b", lower):
            return EvaluationResult(
                action=PedagogicalAction.EXPLAIN,
                misconception=None,
                feedback=None,
                correctness=None,
                module_id=None,
                topic_name=None
            )

        # 5. General fallback: if no known rubric or misconception matched, treat as ungraded
        fallback_mod = evidence_cards[0].module_id if evidence_cards else None
        fallback_topic = evidence_cards[0].title if evidence_cards else None
        return EvaluationResult(
            action=PedagogicalAction.EXPLAIN,
            misconception=None,
            feedback=None,
            correctness=None,
            module_id=fallback_mod,
            topic_name=fallback_topic
        )

    @classmethod
    def evaluate_response(cls, prompt: str) -> Tuple[PedagogicalAction, Optional[str], Optional[str]]:
        """Backwards-compatible wrapper returning (action, misconception, feedback)."""
        result = cls.evaluate_turn(prompt)
        return (result.action, result.misconception, result.feedback)
