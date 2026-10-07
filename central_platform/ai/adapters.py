"""Gayatri AI Platform — Model Provider Abstraction with Offline Pedagogical Engine."""
from __future__ import annotations

import logging
from typing import List, Optional
from central_platform.models.schema import PedagogicalAction, RAGChunk

logger = logging.getLogger("gayatri.central_platform.ai")

class SocraticInferenceEngine:
    """Provides high-quality, course-grounded Socratic explanations and remediation."""

    @staticmethod
    def generate_socratic_response(
        course_title: str,
        user_prompt: str,
        action: PedagogicalAction,
        evidence_cards: List[RAGChunk],
        misconception_feedback: Optional[str] = None
    ) -> str:
        """Generates grounded Socratic pedagogical responses."""
        if action == PedagogicalAction.REMEDIATE and misconception_feedback:
            resp = [
                f"### ⚠️ Misconception Identified in **{course_title}**\n\n",
                f"{misconception_feedback}\n\n",
                "**Socratic Reflection Question:**\n"
            ]
            if "NAND" in misconception_feedback:
                resp.append("Let's test this: If Input A = 0 and Input B = 1, what is the output of an AND gate? Therefore, what must the inverted NAND output be?")
            elif "De Morgan" in misconception_feedback:
                resp.append("Consider two switches in parallel (A + B). If both must NOT be closed, how do you express that with individual negations?")
            elif "Laplace" in misconception_feedback:
                resp.append("Why does transforming a derivative in time require knowing the state of the system at time $t = 0$?")
            else:
                resp.append("Can you trace this step-by-step using the foundational definition?")
            return "".join(resp)

        if evidence_cards:
            primary_card = evidence_cards[0]
            resp = [
                f"### **{primary_card.title}**\n\n",
                f"{primary_card.content}\n\n",
                "---\n\n",
                "#### 💡 Socratic Comprehension Check\n"
            ]
            if "Differential" in primary_card.title:
                resp.append("Given $\\frac{dy}{dx} + 2y = e^x$, what is the integrating factor $I(x)$, and why do we multiply both sides by it?")
            elif "Laplace" in primary_card.title:
                resp.append("What is $\\mathcal{L}\\{e^{at}\\}$ when $s > a$, and where does this restriction originate?")
            elif "Fourier" in primary_card.title:
                resp.append("If a function $f(x)$ is odd ($f(-x) = -f(x)$), what happens to all the cosine coefficients $a_n$?")
            elif "Boolean" in primary_card.title or "Gates" in primary_card.title:
                resp.append("How would you simplify the Boolean expression $A + AB$ using algebraic absorption laws?")
            elif "Sequential" in primary_card.title or "Flip" in primary_card.title:
                resp.append("What is the primary operational distinction between a Level-Sensitive Latch and an Edge-Triggered Flip-Flop?")
            else:
                resp.append(f"How does this concept directly apply to problem-solving in {course_title}?")
            return "".join(resp)

        # Fallback when no direct knowledge cards matched
        return (
            f"I am actively grounded in **{course_title}**. "
            f"Regarding your query on *\"{user_prompt}\"*: Let's explore the core definitions first. "
            f"Could you clarify which specific unit or equation you'd like to work through?"
        )
