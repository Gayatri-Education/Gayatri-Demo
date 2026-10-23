"""Gayatri AI Platform — Anti-Answer-Leakage Guardrails.

Implements the Socratic pedagogical invariant that the orchestrator's turn
lifecycle asserts in step 4: during evaluation and remediation turns the
feedback must teach the underlying principle and elicit the student's own
reasoning — it must never disclose the final numeric answer that the retrieved
knowledge card would give away.

Design constraints (deliberately narrow to avoid false positives):
1. Only EVALUATE and REMEDIATE turns are scanned. EXPLAIN turns intentionally
   quote recovered card content verbatim (see ai/adapters.py), so they are
   exempt.
2. Detection is phrase-gated: only explicit final-answer phrasings
   ("the answer is X", "final answer: X", "value = X", "result should be X",
   ...) are considered, NOT truth-table phrasings ("output is 0", "A=0, B=1"),
   because the card corpus legitimately contains truth tables and
   transform-pair tables where bare "0"/"1" values appear constantly.
3. Card-reference gated: a value is only treated as a leaked final answer if
   the same phrase appears in at least one retrieved evidence card. Numbers
   the tutor invented for its own worked example are not redacted.
"""
from __future__ import annotations

import re
from collections.abc import Sequence

from central_platform.models.schema import PedagogicalAction, RAGChunk

REDACTION_NOTICE = (
    "[final answer withheld — compute it yourself and we'll verify your reasoning together]"
)

# Explicit final-answer phrasings. Deliberately excludes bare "=" and
# "output is X" to protect truth-table and worked-example content (see docstring).
# Accepts both labeled (": 42", "= 42") and predicated ("is 42") forms.
ANSWER_PHRASE_PATTERN = re.compile(
    r"(?:(?:final\s+)?answer|result|value)\s*"
    r"(?:\s*:\s*|(?:is|should\s+be|will\s+be|was)\s+|=)\s*"
    r"[:~≈]?\s*([-+]?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)

DEFAULT_PROTECTED_ACTIONS: tuple[PedagogicalAction, ...] = (
    PedagogicalAction.EVALUATE,
    PedagogicalAction.REMEDIATE,
)


def normalize_number(raw: str) -> str | None:
    """Canonicalizes numeric strings so '42', '+42.0', and '042' compare equal."""
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    # Trim float noise; values beyond this precision never apply to coursework.
    return f"{round(value, 9)}"


def extract_card_final_answers(evidence_cards: Sequence[RAGChunk]) -> set[str]:
    """Extracts phrase-marked final-answer values from the evidence card corpus."""
    answers: set[str] = set()
    for card in evidence_cards:
        for match in ANSWER_PHRASE_PATTERN.finditer(card.content or ""):
            normalized = normalize_number(match.group(1))
            if normalized is not None:
                answers.add(normalized)
    return answers


def redact_leaked_answers(
    message: str,
    action: PedagogicalAction,
    evidence_cards: Sequence[RAGChunk],
    protected_actions: Sequence[PedagogicalAction] = DEFAULT_PROTECTED_ACTIONS,
) -> tuple[str, list[str]]:
    """Redacts final numeric answers sourced from the evidence corpus.

    Runs only for the protected Socratic actions; returns the (possibly
    cleaned) message plus the list of redacted (canonical) values so callers
    can log the enforcement event.
    """
    if action not in protected_actions or not message:
        return message, []
    protected_values = extract_card_final_answers(evidence_cards)
    if not protected_values:
        return message, []

    leaked: list[str] = []
    redacted_message = message
    for match in ANSWER_PHRASE_PATTERN.finditer(message):
        canonical = normalize_number(match.group(1))
        if canonical in protected_values:
            leaked.append(canonical)
            redacted_message = redacted_message.replace(match.group(0), REDACTION_NOTICE)
    return redacted_message, leaked
