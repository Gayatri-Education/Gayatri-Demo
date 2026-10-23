# GAYATRI PLATFORM — POST-RELEASE ENGINEERING IMPROVEMENTS (v4.0.1)

**Completed:** 2026-10-23
**Scope:** Bridge threading & error contract, Socratic answer-leakage guardrail, packaging/tooling adoption, and CI automation.
**Companion doc:** [`UI_REFACTOR_v4.0.1.md`](UI_REFACTOR_v4.0.1.md) (frontend decomposition performed earlier in the same revision).

---

## 1. Problem Statement (Intern Review Findings)

The v4.0.0 release build was strong on *product* hardening (air-gapped execution, cryptographic
course containers, PE packaging) but had four engineering gaps that would surface during
institutional deployment or collaborative development:

1. **UI-thread blocking.** `BridgeFacade.sendQuery` executed RAG retrieval + response synthesis
   synchronously on the Qt main thread — every chat turn froze the window; curriculum indexing
   froze it much longer.
2. **Error leakage.** Slot exception handlers returned `str(exc)` straight to the web UI —
   raw internal traceback fragments as student-facing text.
3. **Dead pedagogical invariant.** Orchestrator turn step 4 ("Anti-Answer-Leakage Invariant
   Check") was a `pass` placeholder: the platform's core *Socratic* promise (never disclose
   final answers) had zero enforcement and zero tests.
4. **No build reproducibility or CI.** Loose `requirements.txt` ranges, no `pyproject.toml`,
   no `__init__` re-export contracts, strictly manual, zero-automation quality gates (no lint,
   no type check, no CI workflow).

## 2. Scope of Change Inventory

| File | Change |
|---|---|
| `app/bridge/facade.py` | Rewritten: async turn/ingestion workers on shared `QThreadPool`; signal delivery (`responseReady`, **new** `curriculumIngested`); unified error envelope; `process_turn_sync` headless twin |
| `app/ui/app.js` | JS moves to signal-driven protocol; "Gayatri is thinking…" state; friendly error rendering with correlation refs; ingestion status flows |
| `central_platform/tutor/guardrails.py` | **New:** phrase/card-gated final-answer redaction engine |
| `central_platform/tutor/orchestrator.py` | Step 4 `pass` → real enforcement of the anti-leak guardrail via answer redaction + warning logs |
| `tests/tutor/test_guardrails.py` | **New:** 10 tests covering extraction precision, redaction, exemption, orchestrator integration |
| `tests/release/test_headless_smoke.py` | Updated to `process_turn_sync` contract; **plus 2 new tests** (async enqueue contract, error-mapping contract) |
| `pyproject.toml` | **New:** canonical packaging (setuptools, editable install), pytest `pythonpath`, ruff / mypy / coverage configs with documented baselines |
| `.github/workflows/ci.yml` | **New:** windows-latest × Python 3.12/3.13 → editable install → ruff → mypy → pytest + coverage artifact |
| `conftest.py` | De-mystified; import path resolution now owned by pytest config, shim kept defensively |
| 23 .py source files | Mechanical quality sweep (see §5): 271 ruff-autofixes + manual typing/enum fixes |

## 3. Workstream 1 — Async Bridge Protocol

### Before
`sendQuery(prompt, student) -> str` ran the full Socratic turn inline. The web page waited
on the slot return. Retrieval latency = UI freeze.

### After
```
JS sendQuery(text, student) ──▶ validation only ──▶ {"success": true, "queued": true, "ref": turn_ab12cd34}
                                   │
                                   ▼  QThreadPool worker (off UI thread)
                     orchestrator.process_turn(...) ──▶ anti-leak redaction (§5)
                                   │
                                   ▼  Qt queued signal (cross-thread safe)
JS bridge.responseReady(payload) ─▶ renderTutorResponse / renderChatError
```

- Compute-side unchanged: workers call the very same `TutorOrchestrator.process_turn`;
  `LearningStateManager` opens per-call SQLite connections, and BM25/semantic ranks are
  read-only at query time, so worker-thread execution is safe with no lock changes.
- **`curriculumIngested(str)`** is a new signal mirroring the same pattern for PDF/DOCX/TXT
  indexing, which is heavier than a turn and was the worst freeze: file-dialog interaction
  stays synchronous (cheap), indexing runs offline-worker, status text flows by signal.
- **Headless twin contract:** `process_turn_sync(prompt, student)` is deliberately *not* a
  Slot — plain python method, same validation and same wire payload, used by pytest's
  headless smoke tests and any CLI-driven verification (QThreadPool deliveries require an
  event loop; pytest has none).
- **JS-side consequences** (`app/ui/app.js`): `sendMessage` now parks on
  `turnPending` + `setThinking(true)` ("Gayatri is thinking…" status, disabled Send button)
  and *resetting on signal receipt*; duplicate sends blocked & pending state; stale promise
  plumbing (`ret.then(...)`) deleted; `refreshAnalytics` now keyed by
  `res.course_id` — a sync correctness bug that the older promise path explicitly carried.

### Wire contract (frozen, documented)

| Message | Shape |
|---|---|
| Turn ack | `{"success": true, "queued": true, "ref": "turn_xxxxxxxx"}` |
| Turn result (signal) | `{"success": true, "session_id", "course_id", "action", "message", "grounded", "evidence_cards":[...], "misconception", "recommended_topic", "ref"}` |
| Ingest ack | `{"success": true, "queued": true, "ref", "filename"}` |
| Ingest result (signal) | `{"success", "cancelled", "message", "chunks_indexed", "filename", "ref"}` |
| Any error (ack/signal) | `{"success": false, "error": {"code", "message", "ref"}}` |

## 4. Workstream 2 — Error Envelope Contract

Every bridge boundary now funnels exceptions through one classifier:

| Exception | Code | Student-facing message |
|---|---|---|
| `JSONDecodeError`, `ValueError` | `invalid_request` | "The request could not be processed…" |
| `FileNotFoundError` | `resource_missing` | "A required resource is unavailable…" |
| `PermissionError` | `forbidden` | "Access was denied…" |
| anything else | `internal_error` | "Something went wrong…" |

- Every envelope carries `ref` (8-hex correlation id, immutable across ack/signal).
- `logger.exception(…, ref=…)` retains the full traceback in logs.
- **Tests assert the negative property too:** `"Traceback" not in message`.

## 5. Workstream 3 — Anti-Answer-Leakage Guardrail

Replaces the placeholder `pass` in turn step 4 with `central_platform/tutor/guardrails.py`:

- **Activation:** only `EVALUATE` / `REMEDIATE` events (the consultative turns). `EXPLAIN`
  inputs are *exempt by design*: it legitimately quotes card content verbatim
  (see `ai/adapters.py`), and masking it would destroy product behavior (covered by existing
  pedagogy tests, which all still pass — e.g., ""Socratic Comprehension Check"" flows).
- **Phrase-gated:** only explicit final-answer phrasings ("answer is X", "final answer: X",
  "value = X", "result should be X") match — bare equalities and truth-table statements
  ("output is 0", "A=0, B=1") are *never* treated as leaks. (Rationale: the knowledge-card
  corpus contains transform-pair tables and truth tables where 0/1 values are ubiquitous.)
- **Card-referenced:** a value only counts as leaked when the same phrase shape is present in
  a retrieved evidence card, so the tutor's own illustrative arithmetic stays intact.
- **Matched leaks are replaced** with
  `"[final answer withheld — compute it yourself and we'll verify your reasoning together]"`,
  and the enforcement is logged (`course_id`, action, redacted values).
- The guard runs *before* the `LearningEvent` snapshot, so persisted events carry the
  redacted text forever after.

Verification tests cover: extraction precision (truth-table noise immunity), single/multi redaction,
EXPLAIN exemption, student's-own-answer preservation, empty-corpus short-circuit, and the
orchestrator-integration cases (REMEDIATE masks a card answer; EXPLAIN quotes it freely).
Resulted in a fix of my own initial regex: `Final answer: 42` colon-label form was VALID
per design notes, but missing from the first draft pattern.

## 6. Workstream 4 — Packaging, Typecheck/Lint, and CI

### pyproject.toml (now canonical)
- setuptools packaging: **editable installs verified** via `pip install -e ".[dev]"` followed
  by `import app, central_platform, core` ✓ — replaces all `sys.path` shims for normal runs.
- `pythonpath = ["."]` for pytest ≥ 7.
- Tool baselines are *documented tolerances*, not excuses:
  - ruff: `E402` (path-shim imports in main/conftest), `E501` (long display strings) and
    a `per-file-ignores` exemption for `app/main.py` `UP036` — that check *is* the friendly
    CLI guard for users launching with an old interpreter; static analysis just sees a
    redundant `requires-python` check.
  - mypy: pragmatic global flags (no-implicit-optional, check-untyped-defs on) with a docs
    note that the overrides table is the place for future module exceptions.

### Adoption & repairs (behavior-verified unchanged)
- **271 ruff autofixes** applied safely: deleted 55 unused imports, sorted 42 import blocks,
  modernized annotations (`typing.Dict/List` → builtins, `X | None`), stripped 21
  missing-EOFs/whitespace noise, etc. — suite stays green.
- **Manual, real fixes:** `zip(..., strict=True)` in the container keystream XOR (B905),
  a shadowed local `modules` in `CourseService` (`no-redef`) that could *legitimately*
  confuse fallback-path loading, python-accurate typed comprehensions for the obfuscated
  rubric decoders (moved to module level after learning — the hard way — that class-body
  comprehensions cannot see the class's own name), a teacher-portal aggregation literal typing,
  and a defensive `course is None` guard in `switchCourse` (mypy surfaced it: `get_course`
  can genuinely return `None` even though the pre-check makes it rare, the invariant is now
  self-consistent).
- **PySide6 enums scoped** (`Qt.WindowType.FramelessWindowHint`, `Qt.ContextMenuPolicy.NoContextMenu`,
  `Qt.MouseButton.LeftButton`) — the 6.6+ modern API and mypy-clean.

### .github/workflows/ci.yml
Windows-latest × Python {3.12, 3.13}, per matrix: editable install (packaging validation),
`ruff check`, `mypy`, `pytest --cov`, coverage artifact upload. `QT_QPA_PLATFORM=offscreen`
for headless-QT-safe runners; `concurrency` cancels superseded pushes.

## 7. Verification evidence

| Gate | Command | Result |
|---|---|---|
| Lint | `python -m ruff check .` | **All checks passed!** |
| Types | `python -m mypy` | **Success: no issues found in 37 source files** |
| Tests | `python -m pytest --cov --cov-report=term` | **95 passed, 1 skipped** (skip = pre-existing build-gated golden scenario) |
| Coverage (new) | same | 71.8% total; `tutor/orchestrator.py` **100%**, `tutor/guardrails.py` 94.3% |
| Packaging | `pip install -e ".[dev]"` + import check | **Success** |

Historical context: the complete suite grew from 83 (UI-refactor rework) → 95 with 12 new tests
(10 guardrails + 2 async/error-contract smoke additions).

## 8. Known Limitations & Follow-Ups (Early-Access Baseline)

1. **Type-coverage**: `rag/service.py` (71.8%) and `rag/semantic.py` (72.7%) hold the largest
   untested gulfs: the pure-`numpy` fallback retriever and the ingest path with real email
   extraction — both need pytest fixtures with synthetic PDFs/DOCX → candidate for next sprint.
2. `core/logging_setup.py` shows 0% since nothing imports-then-exercises it under pytest —
   trivial foreach-test candidates.
3. **Window controls:** the frameless-window drag/min/max/close slots remain main-thread
   bound — fine for a single-frameless window; worth revisiting only if multiple windows
   or QML-based chrome ever appear.
4. **Guardrail recall at corpus scale:** the current knowledge-card corpus exposes fewer
   phrase-marked answers than the synthetic tests assume; the phrase rules are deliberately
   conservative (recall traded for zero false positives). Stress-accuracy with a larger
   corpus (NCERT-style answer sheets) once an ingestion stress-test corpus exists.

## 9. Addendum: Post-Verification Fixes (Bridge ACK + Retrieval Honesty)

Two independent bugs found by live-app testing after the async bridge rollout.
The visible symptoms overlapped — one question produced a De Morgan answer of
questionable relevance *plus* the standalone fallback message ("Gayatri desktop
runtime connection required…") — so both were originally misattributed to a
single `sendMessage` defect. The correct, verified picture:

### 9.1 Double render — Promise-resolved STRING ack (JS)

**Symptom:** every send rendered the real Socratic answer *and* stacked the
offline fallback bubble; the evidence drawer then showed 0 cards.

**Root cause (two layers):**
1. QWebChannel resolves `@Slot(result=str)` invocations as **Promises**
   (qwebchannel.js, Qt ≥ 6.5). The first patch added `ack.then(processAck)`
   but `processAck` still branched on plain-object fields (`ack.success`,
   `ack.queued`). The Promise resolves with the **raw JSON string** the Python
   slot returned — a string matches none of the object-shape branches — so the
   "unexpected shape" tail still scheduled `simulateResponse` after 300 ms.
2. The standalone fallback message ("runtime connection required…") was also
   reachable from the connected-bridge path, which is dishonest: the bridge
   demonstrably works at that point.

**Fix (`app/ui/app.js`):** `normalizeAck(raw)` maps *everything* (object,
string, Promise resolution, undefined) to a decoded object before branching;
all malformed/unknown shapes surface `renderChatError` (friendly envelope).
`simulateResponse` is reserved strictly for the no-runtime `else` branch.
A `turnDelivered` flag guards the fast-turn race (signal arrives before the
ack is processed; the queued-ack branch must not re-enter "thinking").

### 9.2 "Same answer whatever I write" — stopword-noise grounding (RAG)

**Symptom:** the De Morgan card (plus 2–3 neighbors) was retrieved for *any*
question-shaped prompt, e.g. *"what is microprocessor ?"* in Digital
Electronics, so every reply quoted the same generic material.

**Root cause (measured):** BM25 had **no query-side stopword handling**.
Reproduction: `bm25.query("what is microprocessor ?")` scored the De Morgan
card **0.5175** and two neighbors 0.49 / 0.36 — entirely through the ubiquitous
tokens "what"/"is" (IDF ≈ 0 but repeated term frequencies accumulate),
while the actual content word "microprocessor" matched nothing. Because the
0.05 noise floor was breached, `RAGService.query` returned cards, the turn was
labeled `grounded=True`, and the synthesizer wove the irrelevant card into an
answer — fabricated grounding. A correct content query legitimately ranked
De Morgan first (cosine 0.298), which made the two cases indistinguishable.

**Fix (`central_platform/rag/service.py`):** query-side stopword filter
(`_QUERY_STOPWORDS`, Lucene-style list) applied in `BM25Retriever.query`.
Corpus indexing statistics are untouched. Behavior now measured:

| Query | Before | After |
|---|---|---|
| `what is microprocessor ?` (DE) | De Morgan card, grounded | **[]** — honest "not in course material" |
| `quantum entanglement basics` (DE) | arbitrary cards | **[]** |
| `explain de morgan theorem` | De Morgan (1st) | De Morgan (1st) — unchanged |
| `how does nand gate work` | NAND (rank 2) | **NAND (1st)** |

Off-course questions now yield `grounded=False` with no evidence cards instead
of irrelevant quotes.

### 9.3 Guided discovery on ungrounded turns

After both fixes, a *third* UX issue surfaced in live feedback: when a query
genuinely misses the corpus (the demo Digital Electronics course contains only
4 cards: De Morgan's theorems, universal logic gates, adders, flip-flops), the
tutor honestly refuses grounding — but every refusal read as the *same*
template line, which again felt like "one default answer whatever I write."

**Fix:** ungrounded replies now end with a discovery guide generated from the
course's actual corpus:

```
What this course currently draws on:
- De Morgan's Theorems and Boolean Duality
- Universal Logic Gates (NAND and NOR)
- Half Adders and Full Adders in Combinational Arithmetic
- Edge-Triggered Flip-Flops and Sequential State Elements
```

plus an invitation to index own material via **Bring Curriculum**.

Implementation: `RAGService.get_course_topic_titles()` (new), orchestrator
passes `available_topics` to `SocraticInferenceEngine` only when
`evidence_cards` is empty (grounded turns untouched), and the adapter's
fallback branch renders the guide. Regression:
`tests/tutor/test_pedagogy.py::test_ungrounded_turn_guides_toward_available_topics`
+ `test_get_course_topic_titles_exposes_corpus`.

### 9.4 Regression locks

- `tests/unit/test_ui_script_protocol.py` (6 tests): ack normalization,
  guarded re-park, `turnDelivered` wiring, duplicate-send guard, and the
  fallback-reachability contract (fallback only outside the bridge).
- `tests/rag/test_hybrid_rag.py::test_question_shaped_offcourse_prompt_returns_no_fabricated_grounding`:
  pins the measured before/after table above.

— End of document —
