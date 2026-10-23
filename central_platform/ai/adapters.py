"""Gayatri AI Platform — Model Provider Abstraction with Offline Pedagogical Engine (Hardened)."""
from __future__ import annotations

import logging

from central_platform.models.schema import PedagogicalAction, RAGChunk
from core.obfuscation import dec_str

logger = logging.getLogger("gayatri.central_platform.ai")

# Obfuscated pedagogical prompts and reflection templates (anti-reverse engineering protection)
_RAW_PROMPTS: dict[str, bytes] = {
    'nand_reflection': b"\x10\x06\x1eV\x0b_\xf2\xe8\xe7\xef\x82\xdd\xd8\xde\xcd\xff\xec\x9a\xbc\xc1\xa1\x81\x86\x88p+S9\x1d\x07\x1e\x15]-.q\x111\x16\x18\x00[\xc0\xa9\xad\xb7\xaf\x89\x8c\xc4\xd2\xa0\xbc\xef\xbf\xae\xc4\x9f\x9a\x9c h{alV^\x11WYf,:{#'4W\x19\xe4\xf8\xf6\xa5\x81\xfc\xc7\xd3\xcf\xa1\xad\xbd\xab\x85\xcb\xce\x82\x94b~1ujUY\x14O*,p>0\x13\t\x01\x0e\xe4\xec\xaf\xd8\xdc\xea\xef\x92\xd6\xb5\xb3\xbe\xa0\xa8\xc3\x88\x94\xc7",
    'demorgan_reflection': b'\x1f\x0c\x04\x02\x11\x1b\xe3\xff\xb4\xef\xd5\xc6\x90\xc4\xc9\xac\xb8\xb0\xb2\x84\x9b\xcf\x9f\x93${skAKBPPcb\x10xtF/]U\xa2\xc0\xf6\xb7\xfc\xca\xd8\xdb\x9a\xac\xbd\xbc\xa2\xfd\xaa\xa4\xa6\xd9bb.vpLYT\\\x13f%;,B\r\x1fW\x07\xea\xf9\xb3\xff\xd9\xd8\xdd\xd3\xce\xb7\xeb\xa6\xb1\x81\x93\xce\x82\x95wb1qqBDBR&<1;~\x0b\t\x14\x1b\xf5\xe1\xe0\xf8\xee\x9b',
    'laplace_reflection': b"\x0b\x0b\x13Q\x1c\x10\xe3\xfe\xb4\xef\xd0\xc8\xde\xc4\xd8\xaa\xbe\xbe\xb3\x8f\x8f\xcf\x97\xdd`n`pVFZ\\J&j86\x7f\x12\x04\x19\x1e\xa2\xfb\xf5\xe6\xeb\xcc\xde\xd6\x9a\xaa\xa6\xa0\xa1\xb4\x8a\x8c\xd2\x8dhb.fhB^T\x18P m 3\x07I\x03\x0e\r\xf1\xe9\xfe\xba\xc0\xdc\x8f\xc2\xd4\xa9\xae\xf2\xfd\x94\xc7\xd3\xd5\xcc'5",
    'generic_reflection': b'\x1f\x02\x04Q\x01\x10\xf3\xad\xe0\xe9\xc3\xca\xd5\x97\xca\xad\xa5\xa0\xfa\x92\x9c\x8a\x86\xd0fr?jTB^\x15I0#??\x7f\x12\x05\x11[\xe4\xe6\xe5\xf9\xfa\xc4\xd8\xda\xd5\xaf\xa9\xa3\xf6\xb9\x81\x8d\x9b\x97isgzr\x1c',
    'eval_fallback': b'\x14\x0c\x1dQ\x0f\x10\xf3\xe1\xf0\xbb\xdb\xc6\xc5\x97\xdf\xb5\xbc\xbf\xa3\xc1\x9c\x87\x9f\x8e$\x7f}9RBBTH&.q(-\t\x0f\x18\x1e\xef\xfa\xb0\xfe\xf0\x85\xd8\xdb\xd3\xb2\xe8\xbb\xb9\xad\x8d\x88\xcd',
    'math_ode_check': b'\x1b\n\x1c\x14\x16_\xa2\xd1\xf2\xe9\xc3\xca\xcb\xd3\xc7\xb8\xb7\xb7\xa2\x9c\xc8\xc4\xd6\xcf}+/9EyV\x11\x10c=99+F\x04\x07[\xf6\xe1\xf5\xb7\xf7\xcb\xd8\xd6\xdd\xb3\xa9\xbb\xbf\xb3\x83\xcb\x94\x98csag<\x07c\x19@\x16bat:\x0c\rP\x00\x16\xfc\xac\xf7\xf5\x81\xdf\xca\x96\xd0\xb1\xa7\xa6\xb0\x90\x8b\x97\xd5\x9el~y8lOIQHb+)w7\x11S',
    'math_laplace_check': b'\x0b\x0b\x0b\x05X\x16\xf5\xad\xb0\xc7\xcf\xc8\xc4\xdf\xdd\xa4\xa0\xa8\x96\x9c\xb4\x94\x93\xa3\x7fjfd|Z\n\x15K+/?x{\x15MJ[\xe3\xad\xbc\xb7\xff\xcb\xc8\x93\xcd\xa9\xad\xbd\xb3\xfd\x80\x84\x97\x8a sf|o\x03XTKK4$7/\x0b\x06\x1eW\x11\xf7\xe5\xf4\xf3\xcf\xc9\xdb\xd3\x82',
    'math_fourier_check': b'\x15\x05J\x10X\x19\xf3\xe3\xf7\xef\xcb\xc6\xde\x97\x9a\xa3\xe4\xab\xf3\xc5\xc8\x86\x85\xddkov9\x08\x03H\x1d\x11;cqe\x7fK\x0b\\\x03\xab\xad\xb9\xbb\xbe\xd2\xc4\xd2\xce\xe1\xa0\xae\xa6\xad\x81\x85\x81\xd9th.tpO\nEPZf.;(\x0b\x07\x15W\x1d\xea\xe9\xf5\xfc\xc8\xcb\xc6\xd3\xd3\xb0\xb8\xf2\xfd\x81\xb8\x80\xd1\xc3',
    'elec_bool_check': b'\x14\x0c\x1dQ\x0f\x10\xf3\xe1\xf0\xbb\xdb\xc6\xc5\x97\xcd\xac\xa1\xa3\xb6\x88\x8e\x96\xd6\x89ln2[OHBP]-j4 /\x14\x08\x07\x08\xeb\xe6\xfe\xb7\xba\xe4\x8c\x98\x9a\x80\x8a\xeb\xf6\xa8\x97\x82\x9c\x9e fbryAXPQ\\f,6(\r\x1b\x00\x03\x17\xea\xe2\xb3\xf6\xc0\xdf\xdc\x89',
    'elec_seq_check': b'\x0b\x0b\x0b\x05X\x16\xf5\xad\xe0\xf3\xc7\x89\xc0\xc5\xd7\xa8\xad\xa1\xa3\xc1\x87\x9f\x93\x8fe\x7f{vNFB\x15X*9%11\x05\x19\x1d\x14\xec\xa9\xf2\xf2\xea\xd2\xc9\xd6\xd4\xe1\xa9\xef\x9a\xb8\x92\x8e\x9e\xd4Sb`fuWCG]\x1f\n, 8\nI\x11\x19\x1a\xa5\xed\xfd\xba\xe4\xcc\xc8\xd3\x90\x90\xb9\xbb\xbe\x87\x82\x9c\x90\x98#L}qo\x0bkXT2v',
    'fallback_prefix': b'\x15C\x0b\x1cX\x1e\xe5\xf9\xfd\xed\xc7\xc5\xc9\x97\xd9\xb7\xa3\xa6\xb4\x85\x8d\x8b\xd6\x94j+83[DA@N0/\x0e,6\x12\x01\x11\x06\xa8\xa3\xbe\xb7\xcc\xc0\xcb\xd2\xc8\xa5\xa1\xa1\xb1\xfd\x9d\x84\x87\x8b v{pnZ\n^V\x1flo/.\x11\x0c\x02(\x0e\xf7\xe3\xfe\xea\xd5\xd5\x8d\x9c\x87\xe4\x87\xb7\xad\xc7\x94\xce\x90\x84sf~jz\x06Y\\^b*?%;E\x08\x16\x1c\xe8\xe6\xe6\xe2\xf4\xcb\xc5\xc1\x99\xa6\xae\xbc\xa6\xa8\xcd\xca\xb2\x97\x8aji4bM\\\x10TR$>:<\x18H\x18\x1e\x14\xe7\xe3\xb2\xea\xd0\xc2\xcd\xdc\xda\xaa\xa9\xf1\xad\xb1\x8f\x99\xd4\x94p)ufkDXZU/h69(C\x0fR\x15\xe9\xec\xeb\xb5\xe8\xcc\x8a\xc6\xd7\xcd\xad\xed\xa0\xb3\x90\x86\x85\x90\x96:',
}


class SocraticInferenceEngine:
    """Provides high-quality, course-grounded Socratic explanations and remediation."""

    @staticmethod
    def _prompt(key: str) -> str:
        return dec_str(_RAW_PROMPTS[key])

    @classmethod
    def generate_socratic_response(
        cls,
        course_title: str,
        user_prompt: str,
        action: PedagogicalAction,
        evidence_cards: list[RAGChunk],
        misconception_feedback: str | None = None,
        evaluation_feedback: str | None = None,
        available_topics: list[str] | None = None
    ) -> str:
        """Generates grounded Socratic pedagogical responses with protected prompts.

        ``available_topics`` is set by the orchestrator on ungrounded turns:
        the reply then enumerates the topics the course genuinely covers so a
        missed query becomes guided discovery instead of a generic dead end.
        """
        if action == PedagogicalAction.REMEDIATE and misconception_feedback:
            resp = [
                f"### ⚠️ Misconception Identified in **{course_title}**\n\n",
                f"{misconception_feedback}\n\n",
                "**Socratic Reflection Question:**\n"
            ]
            if "NAND" in misconception_feedback:
                resp.append(cls._prompt("nand_reflection"))
            elif "De Morgan" in misconception_feedback:
                resp.append(cls._prompt("demorgan_reflection"))
            elif "Laplace" in misconception_feedback:
                resp.append(cls._prompt("laplace_reflection"))
            else:
                resp.append(cls._prompt("generic_reflection"))
            return "".join(resp)

        if action == PedagogicalAction.EVALUATE and evaluation_feedback:
            resp = [
                f"### 💡 Pedagogical Evaluation in **{course_title}**\n\n",
                f"{evaluation_feedback}\n\n",
                "**Next Step:**\n"
            ]
            if evidence_cards:
                resp.append(f"Refer to **{evidence_cards[0].title}** for deeper principles.")
            else:
                resp.append(cls._prompt("eval_fallback"))
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
                resp.append(cls._prompt("math_ode_check"))
            elif "Laplace" in primary_card.title:
                resp.append(cls._prompt("math_laplace_check"))
            elif "Fourier" in primary_card.title:
                resp.append(cls._prompt("math_fourier_check"))
            elif "Boolean" in primary_card.title or "Gates" in primary_card.title:
                resp.append(cls._prompt("elec_bool_check"))
            elif "Sequential" in primary_card.title or "Flip" in primary_card.title:
                resp.append(cls._prompt("elec_seq_check"))
            else:
                resp.append(f"How does this concept directly apply to problem-solving in {course_title}?")
            return "".join(resp)

        # Fallback when no direct knowledge cards matched
        template = cls._prompt("fallback_prefix")
        message = template.format(course_title=course_title, user_prompt=user_prompt)
        if available_topics:
            topic_lines = "\n".join(f"- {title}" for title in available_topics)
            message += (
                "\n\n**What this course currently draws on:**\n"
                f"{topic_lines}\n\n"
                "Ask about any of these — or bring your own material with "
                "**Bring Curriculum** and I will index it against these questions."
            )
        return message
