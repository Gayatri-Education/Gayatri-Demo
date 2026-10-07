"""Gayatri AI Platform — Socratic Next Action & Misconception Engine."""
from __future__ import annotations

import re
from typing import Optional, Tuple
from central_platform.models.schema import PedagogicalAction

class NextActionEngine:
    """Evaluates student inputs, diagnoses conceptual misconceptions, and determines next action."""

    # Misconception signatures for Engineering Mathematics & Digital Electronics
    MISCONCEPTION_RULES = [
        # Digital Electronics
        (
            r"\b(nand|nor)\b.*(output is 0 when any input is 0|0.*when.*0)",
            "NAND/NOR Logic Inversion Error",
            "Remember that NAND produces 0 ONLY when ALL inputs are 1. If any input is 0, the output is 1."
        ),
        (
            r"\b(de morgan|demorgan)\b.*(\+.*becomes.*\+|and.*becomes.*and)",
            "De Morgan Dual Complement Error",
            "De Morgan's theorem swaps operations: the complement of a sum (OR) is the product of complements (AND), i.e., (A + B)' = A' · B'."
        ),
        (
            r"\b(half adder)\b.*(carries 3 bits|has carry in)",
            "Half Adder vs Full Adder Misconception",
            "A Half Adder accepts only two 1-bit inputs (A and B). A Full Adder is required to handle a Carry-In (Cin)."
        ),
        # Engineering Mathematics
        (
            r"\b(linear differential equation)\b.*(y\^2|dy/dx\^2|product of y and dy/dx)",
            "Linearity Violation in Differential Equations",
            "An ODE is linear only if the dependent variable and its derivatives appear to the first power and are not multiplied together."
        ),
        (
            r"\blaplace\b.*(derivative.*is s\*f\(s\)|no initial condition)",
            "Laplace Derivative Initial Value Omission",
            "The Laplace transform of f'(t) is s·F(s) - f(0). You must subtract the initial condition f(0)."
        ),
        (
            r"\bfourier\b.*(only for periodic functions|applies to everything without period)",
            "Fourier Series Periodicity Constraint",
            "Standard Fourier Series applies strictly to periodic functions over a finite interval. Non-periodic functions require the Fourier Transform."
        )
    ]

    @classmethod
    def evaluate_response(cls, prompt: str) -> Tuple[PedagogicalAction, Optional[str], Optional[str]]:
        """Analyzes prompt for misconceptions; selects EXPLAIN, CHECK, or REMEDIATE."""
        lower = prompt.lower()

        # Check for matching misconception
        for pattern, tag, feedback in cls.MISCONCEPTION_RULES:
            if re.search(pattern, lower, re.IGNORECASE):
                return PedagogicalAction.REMEDIATE, tag, feedback

        # Questions or concept exploration
        if any(w in lower for w in ("what", "how", "explain", "derive", "why", "define")):
            return PedagogicalAction.EXPLAIN, None, None

        # Student answering a check
        return PedagogicalAction.EVALUATE, None, None
