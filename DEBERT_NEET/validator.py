from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Literal, Optional, Tuple

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

log = logging.getLogger("exam_pipeline")

LEVELS = ("Easy", "Medium", "Hard")
_DIFF_SCORE = {"Easy": 1.0, "Medium": 2.0, "Hard": 3.0}
TopicKey = Tuple[str, str]

@dataclass(frozen=True)
class Constraint:
    sno: int
    statement: str
    name: str
    implemented_in: str

CONSTRAINTS: List[Constraint] = [
    Constraint(
        1,
        "We could analyse the difficulty trends and repetition pattern. Giving the priority for these concepts might help in predicting accurate questions.",
        "Gowtham",
        "TopicPriorityModel: repetition score; difficulty slope and recency-weighted mix",
    ),
    Constraint(
        2,
        "Questions from important topics that haven't come in previous 2-3 years are more likely to come next year.",
        "Arijit",
        "TopicPriorityModel: overdue score (only for important topics absent for min..cutoff years)",
    ),
]

def print_constraints() -> None:
    print(f"{'S.no':<5}| {'Name':<8}| Statement")
    print("-" * 100)
    for c in CONSTRAINTS:
        print(f"{c.sno:<5}| {c.name:<8}| {c.statement}")
        print(f"{'':<5}| {'':<8}| -> {c.implemented_in}")

def _clean_rows(records: Iterable[dict]) -> List[Tuple[TopicKey, int, Optional[str]]]:
    rows = []
    for r in records:
        chapter = r.get("chapter")
        try:
            year = int(r.get("year"))
        except (TypeError, ValueError):
            continue
        if not isinstance(chapter, str) or not chapter.strip():
            continue
        subject = (r.get("subject") or "").strip()
        level = r.get("difficulty")
        level = level.strip().title() if isinstance(level, str) else None
        rows.append(((subject, chapter.strip()), year, level if level in _DIFF_SCORE else None))
    return rows

def _slope(year_means: Dict[int, float]) -> Optional[float]:
    if len(year_means) < 3:
        return None
    ys = sorted(year_means)
    return float(np.polyfit(ys, [year_means[y] for y in ys], 1)[0])

def _largest_remainder(weights: List[float], total: int) -> List[int]:
    s = float(sum(weights))
    if s <= 0 or total <= 0:
        return [0] * len(weights)
    quotas = [w / s * total for w in weights]
    out = [int(q) for q in quotas]
    order = sorted(range(len(weights)), key=lambda i: quotas[i] - out[i], reverse=True)
    for i in order[: total - sum(out)]:
        out[i] += 1
    return out

@dataclass
class TopicScore:
    key: TopicKey
    priority: float
    repetition: float
    overdue: float
    total_questions: int
    years_seen: int
    last_seen: int
    absent_years: int
    is_important: bool
    difficulty_slope: Optional[float]
    trend: str
    difficulty_mix: Dict[str, float]

@dataclass
class PlanRow:
    key: TopicKey
    n_questions: int
    difficulty_counts: Dict[str, int]
    priority: float

class TopicPriorityModel:
    def __init__(
        self,
        records: Iterable[dict],
        target_year: Optional[int] = None,
        half_life: float = 3.0,
        min_absent_years: int = 2,
        max_absent_years: int = 3,
        boost_cutoff_years: int = 5,
        importance_quantile: float = 0.5,
        w_repetition: float = 0.6,
        w_overdue: float = 0.4,
        trend_threshold: float = 0.05,
        min_topic_samples: int = 5,
    ):
        rows = _clean_rows(records)
        if not rows:
            raise ValueError("No usable records (need 'chapter' and 'year').")
        if w_repetition < 0 or w_overdue < 0 or (w_repetition + w_overdue) == 0:
            raise ValueError("Weights must be non-negative and not both zero.")

        self.all_years = sorted({y for _, y, _ in rows})
        self.target_year = target_year if target_year is not None else self.all_years[-1] + 1
        if self.target_year <= self.all_years[-1]:
            raise ValueError("target_year must be later than the latest year in the data.")

        wsum = w_repetition + w_overdue
        self.w_rep, self.w_over = w_repetition / wsum, w_overdue / wsum
        self.half_life = half_life
        self.min_absent, self.max_absent = min_absent_years, max_absent_years
        self.cutoff = boost_cutoff_years
        self.importance_quantile = importance_quantile
        self.trend_threshold = trend_threshold
        self.min_topic_samples = min_topic_samples

        self.by_topic: Dict[TopicKey, List[Tuple[int, Optional[str]]]] = {}
        for key, year, level in rows:
            self.by_topic.setdefault(key, []).append((year, level))

        self._scores = self._score_all()

    def _w(self, year: int) -> float:
        return 0.5 ** ((self.target_year - 1 - year) / self.half_life)

    def _year_means(self, entries: List[Tuple[int, Optional[str]]]) -> Dict[int, float]:
        buckets: Dict[int, List[float]] = {}
        for y, lvl in entries:
            if lvl:
                buckets.setdefault(y, []).append(_DIFF_SCORE[lvl])
        return {y: float(np.mean(v)) for y, v in buckets.items()}

    def _mix(self, entries: List[Tuple[int, Optional[str]]]) -> Optional[Dict[str, float]]:
        w = {lvl: 0.0 for lvl in LEVELS}
        n = 0
        for y, lvl in entries:
            if lvl:
                w[lvl] += self._w(y)
                n += 1
        total = sum(w.values())
        if n < self.min_topic_samples or total == 0:
            return None
        return {lvl: w[lvl] / total for lvl in LEVELS}

    def _trend_label(self, slope: Optional[float]) -> str:
        if slope is None:
            return "unknown"
        if slope > self.trend_threshold:
            return "harder"
        if slope < -self.trend_threshold:
            return "easier"
        return "stable"

    def _score_all(self) -> Dict[TopicKey, TopicScore]:
        all_entries = [e for v in self.by_topic.values() for e in v]
        overall_slope = _slope(self._year_means(all_entries))
        overall_mix = self._mix(all_entries) or {"Easy": 1 / 3, "Medium": 1 / 3, "Hard": 1 / 3}

        totals = {k: len(v) for k, v in self.by_topic.items()}
        max_total = max(totals.values())
        importance_cut = float(np.quantile(list(totals.values()), self.importance_quantile))

        weighted = {k: sum(self._w(y) for y, _ in v) for k, v in self.by_topic.items()}
        max_weighted = max(weighted.values())
        n_years = len(self.all_years)

        scores: Dict[TopicKey, TopicScore] = {}
        for key, entries in self.by_topic.items():
            years_seen = {y for y, _ in entries}
            last_seen = max(years_seen)
            absent = self.target_year - last_seen - 1

            repetition = 0.5 * weighted[key] / max_weighted + 0.5 * len(years_seen) / n_years

            important = totals[key] >= importance_cut
            overdue = 0.0
            if important and self.min_absent <= absent <= self.cutoff:
                overdue = min(1.0, absent / self.max_absent) * (totals[key] / max_total)

            slope = _slope(self._year_means(entries))
            if slope is None:
                slope = overall_slope
            mix = self._mix(entries) or overall_mix

            scores[key] = TopicScore(
                key=key,
                priority=self.w_rep * repetition + self.w_over * overdue,
                repetition=repetition,
                overdue=overdue,
                total_questions=totals[key],
                years_seen=len(years_seen),
                last_seen=last_seen,
                absent_years=absent,
                is_important=important,
                difficulty_slope=slope,
                trend=self._trend_label(slope),
                difficulty_mix=mix,
            )
        return scores

    def rank(self) -> List[TopicScore]:
        return sorted(self._scores.values(), key=lambda s: (-s.priority, s.key))

    def priority_of(self, subject: Optional[str], chapter: str) -> Optional[float]:
        s = self._scores.get(((subject or "").strip(), chapter.strip()))
        if s is None:
            s = next((v for k, v in self._scores.items() if k[1] == chapter.strip()), None)
        return None if s is None else s.priority

    def plan(self, total_questions: int) -> List[PlanRow]:
        scored = [s for s in self.rank() if s.priority > 0]
        counts = _largest_remainder([s.priority for s in scored], total_questions)
        rows = []
        for s, n in zip(scored, counts):
            if n == 0:
                continue
            dc = dict(zip(LEVELS, _largest_remainder([s.difficulty_mix[l] for l in LEVELS], n)))
            rows.append(PlanRow(s.key, n, dc, s.priority))
        return rows

def _normalize_key(text: str) -> str:
    text = re.sub(r"[^\w\s]", "", text.lower())
    return re.sub(r"\s+", " ", text).strip()

def _coerce_bool(value) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        s = value.strip().lower()
        if s in {"true", "yes", "1"}:
            return True
        if s in {"false", "no", "0"}:
            return False
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    return None

def _extract_json_object(text: str, required_key: str) -> Optional[dict]:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[1]

    decoder = json.JSONDecoder()
    found: Optional[dict] = None
    pos = 0
    while True:
        start = text.find("{", pos)
        if start == -1:
            break
        try:
            obj, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            pos = start + 1
            continue
        if isinstance(obj, dict) and required_key in obj:
            found = obj
        pos = max(end, start + 1)
    return found

class MCQQuestionSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(..., min_length=10)
    option_a: str = Field(..., min_length=1)
    option_b: str = Field(..., min_length=1)
    option_c: str = Field(..., min_length=1)
    option_d: str = Field(..., min_length=1)
    correct_option: str
    explanation: Optional[str] = Field(None, min_length=10)
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"
    subject: Optional[str] = None
    chapter: Optional[str] = None
    year: Optional[int] = None
    source: str = Field(...,min_length = 1)

    @field_validator("correct_option")
    @classmethod
    def validate_choice(cls, value: str) -> str:
        clean = value.strip().upper()
        if clean not in {"A", "B", "C", "D"}:
            raise ValueError(f"correct_option must be A, B, C, or D. Got: {value!r}")
        return clean

    @field_validator("difficulty", mode="before")
    @classmethod
    def normalize_difficulty(cls, value):
        return value.strip().title() if isinstance(value, str) else value

    @field_validator("explanation", mode="before")
    @classmethod
    def blank_explanation_is_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def options(self) -> List[str]:
        return [self.option_a, self.option_b, self.option_c, self.option_d]

@dataclass
class DedupResult:
    status: Literal["duplicate", "unique", "skipped"]
    message: str

@dataclass
class ValidationReport:
    verdict: Literal["accept", "reject", "needs_judge"] = "accept"
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    question: Optional[MCQQuestionSchema] = None
    topic_priority: Optional[float] = None
    solver_prompt: Optional[str] = None
    judge_prompt: Optional[str] = None

class QuestionValidator:
    LENGTH_RATIO = 3.5
    MIN_LENGTH_GAP = 25
    _COMPOUND_RE = re.compile(
        r"\b(?:all|none)\s+of\s+the\s+above\b"
        r"|\bneither\s+of\s+the\s+above\b"
        r"|\bboth\s+\(?[a-d]\)?\s+and\s+\(?[a-d]\)?\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        processed_bank_path: Optional[str] = "data/Question_Bank/processed/questions.json",
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        similarity_threshold: float = 0.88,
        reject_compound_options: bool = True,
    ):
        self.embedding_model_name = embedding_model_name
        self.similarity_threshold = similarity_threshold
        self.reject_compound_options = reject_compound_options

        self.bank_path: Optional[Path] = Path(processed_bank_path) if processed_bank_path else None
        self.bank_questions: List[dict] = []
        self.bank_embeddings: Optional[np.ndarray] = None
        self._exact_keys: set = set()
        self.embedder = None

        self._load_bank()
        self._init_embedder()

    def _load_bank(self) -> None:
        if not self.bank_path:
            return
        if not self.bank_path.exists():
            return
        try:
            with open(self.bank_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            return

        if isinstance(data, dict):
            data = data.get("questions", [])
        self.bank_questions = [
            q for q in data if isinstance(q, dict) and isinstance(q.get("text"), str) and q["text"].strip()
        ]
        self._exact_keys = {_normalize_key(q["text"]) for q in self.bank_questions}

    def _init_embedder(self) -> None:
        if SentenceTransformer is None:
            return
        try:
            self.embedder = SentenceTransformer(self.embedding_model_name)
            self._embed_bank()
        except Exception as e:
            self.embedder = None
            self.bank_embeddings = None

    def _cache_path(self) -> Optional[Path]:
        if not self.bank_path:
            return None
        return self.bank_path.with_name(self.bank_path.name + ".emb.npz")

    def _read_cache(self, expected_count: int) -> Optional[np.ndarray]:
        cache = self._cache_path()
        if not cache or not cache.exists() or not self.bank_path or not self.bank_path.exists():
            return None
        try:
            with np.load(cache, allow_pickle=False) as d:
                if (
                    int(d["mtime_ns"]) == self.bank_path.stat().st_mtime_ns
                    and str(d["model"]) == self.embedding_model_name
                    and d["embeddings"].shape[0] == expected_count
                ):
                    return d["embeddings"]
        except Exception:
            pass
        return None

    def _write_cache(self, embeddings: np.ndarray) -> None:
        cache = self._cache_path()
        if not cache or not self.bank_path or not self.bank_path.exists():
            return
        try:
            np.savez(
                cache,
                embeddings=embeddings,
                mtime_ns=np.int64(self.bank_path.stat().st_mtime_ns),
                model=np.str_(self.embedding_model_name),
            )
        except OSError as e:
            pass

    def _embed_bank(self) -> None:
        if not self.bank_questions:
            return
        emb = self._read_cache(len(self.bank_questions))
        if emb is None:
            texts = [q["text"] for q in self.bank_questions]
            emb = np.asarray(
                self.embedder.encode(texts, normalize_embeddings=True, show_progress_bar=False),
                dtype=np.float32,
            )
            self._write_cache(emb)
        self.bank_embeddings = emb

    def validate_heuristics(self, q: MCQQuestionSchema) -> Tuple[bool, str]:
        options = q.options
        cleaned = [_normalize_key(o) for o in options]
        if len(set(cleaned)) < 4:
            return False, "Duplicate options detected within the question."

        if self.reject_compound_options:
            for label, opt in zip("ABCD", options):
                if self._COMPOUND_RE.search(opt):
                    return False, f"Option {label} is a compound option ('{opt}'); rewrite as a standalone option."

        lengths = [len(o) for o in options]
        correct_len = lengths[ord(q.correct_option) - ord("A")]
        avg_distractor = (sum(lengths) - correct_len) / 3.0
        if avg_distractor > 0 and correct_len > 0 and abs(correct_len - avg_distractor) >= self.MIN_LENGTH_GAP:
            if correct_len / avg_distractor > self.LENGTH_RATIO:
                return False, "Option giveaway: correct option is disproportionately longer than distractors."
            if avg_distractor / correct_len > self.LENGTH_RATIO:
                return False, "Option giveaway: correct option is disproportionately shorter than distractors."

        return True, "Passed heuristics."

    def check_duplicate(self, question_text: str) -> DedupResult:
        if _normalize_key(question_text) in self._exact_keys:
            return DedupResult("duplicate", "Exact duplicate of an existing question.")
        if self.embedder is None:
            return DedupResult("skipped", "Semantic dedup unavailable; only the exact-match check ran.")
        if self.bank_embeddings is None or len(self.bank_embeddings) == 0:
            return DedupResult("unique", "Bank is empty; nothing to compare against.")

        new_vec = self.embedder.encode([question_text], normalize_embeddings=True)
        sims = np.dot(self.bank_embeddings, np.asarray(new_vec, dtype=np.float32).T).flatten()
        idx = int(np.argmax(sims))
        score = float(sims[idx])
        if score >= self.similarity_threshold:
            return DedupResult(
                "duplicate",
                f"Near-duplicate of existing question (score {score:.2f}): '{self.bank_questions[idx]['text']}'",
            )
        return DedupResult("unique", f"Compared against {len(self.bank_questions)} questions (max similarity {score:.2f}).")

    def add_to_bank(self, q: MCQQuestionSchema) -> None:
        entry = q.model_dump()
        self._exact_keys.add(_normalize_key(q.text))
        if self.embedder is not None:
            vec = np.asarray(self.embedder.encode([q.text], normalize_embeddings=True), dtype=np.float32)
            self.bank_embeddings = vec if self.bank_embeddings is None else np.vstack([self.bank_embeddings, vec])
        self.bank_questions.append(entry)

    def build_llm_solver_prompt(self, q: MCQQuestionSchema) -> str:
        return f"""You are an expert exam solver for competitive exams.
Answer the following multiple-choice question.

Question: {q.text}
Option A: {q.option_a}
Option B: {q.option_b}
Option C: {q.option_c}
Option D: {q.option_d}

If the question is ambiguous, factually flawed, has no correct option, or has more than one defensible correct option, set "ambiguous" to true.

Respond with a single JSON object only (no markdown fences, no extra text):
{{"chosen_option": "<A, B, C or D>", "ambiguous": <true or false>, "reasoning": "<one or two sentences>"}}"""

    def build_llm_judge_prompt(self, q: MCQQuestionSchema) -> str:
        explanation = q.explanation or "(not provided)"
        return f"""You are a senior exam quality reviewer for competitive exams.
Evaluate the following multiple-choice question:

Question: {q.text}
Option A: {q.option_a}
Option B: {q.option_b}
Option C: {q.option_c}
Option D: {q.option_d}
Designated Correct Option: {q.correct_option}
Explanation: {explanation}

Evaluate against these strict criteria:
1. Is the question unambiguous and scientifically accurate?
2. Is there EXACTLY ONE unambiguous correct option among A, B, C, and D?
3. If an explanation is provided, does it logically support the designated option and rule out the others? (Skip this criterion if it is "(not provided)".)

Respond with a single JSON object only (no markdown fences, no extra text):
{{"is_valid": <true or false>, "rejection_reason": <null or "detailed reason">}}"""

    def validate_llm_judge_response(self, llm_response_text: str) -> Tuple[bool, Optional[str]]:
        obj = _extract_json_object(llm_response_text, "is_valid")
        if obj is None:
            return False, "Judge output failed JSON parsing."
        verdict = _coerce_bool(obj.get("is_valid"))
        if verdict is None:
            return False, f"Judge returned a non-boolean is_valid: {obj.get('is_valid')!r}"
        reason = obj.get("rejection_reason")
        if not verdict and not reason:
            reason = "Judge rejected the question without giving a reason."
        return verdict, reason

    def parse_solver_response(self, llm_response_text: str) -> Tuple[Optional[str], bool, Optional[str]]:
        obj = _extract_json_object(llm_response_text, "chosen_option")
        if obj is None:
            return None, False, None
        chosen = str(obj.get("chosen_option", "")).strip().upper()[:1]
        chosen = chosen if chosen in {"A", "B", "C", "D"} else None
        ambiguous = _coerce_bool(obj.get("ambiguous")) or False
        return chosen, ambiguous, obj.get("reasoning")

LLMCall = Callable[[str], str]

def run_pipeline(
    validator: QuestionValidator,
    raw_candidate: dict,
    llm: Optional[LLMCall] = None,
    add_on_accept: bool = True,
    priority_model: Optional[TopicPriorityModel] = None,
) -> ValidationReport:
    report = ValidationReport()

    try:
        q = MCQQuestionSchema(**raw_candidate)
    except ValidationError as err:
        report.verdict = "reject"
        report.reasons.append(f"Schema validation failed: {err}")
        return report
    report.question = q

    if priority_model is not None and q.chapter:
        report.topic_priority = priority_model.priority_of(q.subject, q.chapter)
        if report.topic_priority is None:
            report.warnings.append(f"Chapter '{q.chapter}' not found in historical data; no topic priority.")

    ok, msg = validator.validate_heuristics(q)
    if not ok:
        report.reasons.append(msg)

    dedup = validator.check_duplicate(q.text)
    if dedup.status == "duplicate":
        report.reasons.append(dedup.message)
    elif dedup.status == "skipped":
        report.warnings.append(dedup.message)

    if report.reasons:
        report.verdict = "reject"
        return report

    solver_prompt = validator.build_llm_solver_prompt(q)
    judge_prompt = validator.build_llm_judge_prompt(q)
    if llm is None:
        report.verdict = "needs_judge"
        report.solver_prompt, report.judge_prompt = solver_prompt, judge_prompt
        return report

    try:
        chosen, ambiguous, reasoning = validator.parse_solver_response(llm(solver_prompt))
        if chosen is None:
            report.reasons.append("Solver output could not be parsed.")
        elif ambiguous:
            report.reasons.append(f"Solver flagged the question as ambiguous/flawed: {reasoning}")
        elif chosen != q.correct_option:
            report.reasons.append(f"Answer-key mismatch: solver chose {chosen}, key says {q.correct_option}. Reasoning: {reasoning}")

        is_valid, reason = validator.validate_llm_judge_response(llm(judge_prompt))
        if not is_valid:
            report.reasons.append(f"Judge rejected: {reason}")
    except Exception as e:
        report.verdict = "needs_judge"
        report.warnings.append(f"LLM call failed: {e}")
        report.solver_prompt, report.judge_prompt = solver_prompt, judge_prompt
        return report

    if report.reasons:
        report.verdict = "reject"
        return report

    report.verdict = "accept"
    if add_on_accept:
        validator.add_to_bank(q)
    return report

def make_lm_studio_client(
    base_url: str = "http://localhost:1234/v1", model: str = "local-model", timeout: int = 120
) -> LLMCall:
    import urllib.request
    def call(prompt: str) -> str:
        payload = json.dumps(
            {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0}
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/chat/completions", data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)["choices"][0]["message"]["content"]
    return call

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a sample MCQ and view Topic Constraints.")
    parser.add_argument("--bank", default="data/Question_Bank/processed/questions.json")
    parser.add_argument("--judge", action="store_true", help="Run LLM checks against LM Studio.")
    parser.add_argument("--lm-url", default="http://localhost:1234/v1")
    parser.add_argument("--model", default="local-model")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("\n" + "="*50)
    print("TOPIC PRIORITY CONSTRAINTS (Step 2)")
    print("="*50)
    print_constraints()

    print("\n" + "="*50)
    print("VALIDATION PIPELINE TEST (Step 4)")
    print("="*50)

    validator = QuestionValidator(processed_bank_path=args.bank)
    llm = make_lm_studio_client(args.lm_url, args.model) if args.judge else None

    raw_candidate = {
        "text": "Which of the following cell organelles is the primary site of aerobic respiration (ATP synthesis)?",
        "option_a": "Endoplasmic reticulum",
        "option_b": "Mitochondria",
        "option_c": "Ribosome",
        "option_d": "Golgi apparatus",
        "correct_option": "B",
        "explanation": "Mitochondria are the powerhouses of the cell where ATP is produced via aerobic respiration.",
        "difficulty": "Easy",
        "subject": "Biology",
        "chapter": "Cell: The Unit of Life",
        "year": 2027,
        "source": "Validation Test",
    }

    report = run_pipeline(validator, raw_candidate, llm=llm)

    print(f"\nVerdict: {report.verdict.upper()}")
    for r in report.reasons:
        print(f"  ✗ {r}")
    for w in report.warnings:
        print(f"  ⚠ {w}")
    if report.verdict == "needs_judge":
        print("\n[NOTE] LLM Judge was skipped. Use --judge to run the full AI pass.")
        print("\nPrompt for the answer-blind solver pass:\n" + "-" * 44)
        print(report.solver_prompt)

    return {"accept": 0, "reject": 1, "needs_judge": 2}[report.verdict]

if __name__ == "__main__":
    sys.exit(main())
