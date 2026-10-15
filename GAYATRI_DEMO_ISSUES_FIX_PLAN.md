# Gayatri Demo v4.0.0 — Issue Resolution and Release-Readiness Plan

**Target repository:** `Gayatri-Education/Gayatri-Demo`  
**Reviewed:** 2026-10-14  
**Purpose:** A phase-gated execution plan for a local AI coding agent. The agent must inspect, plan, implement, test, debug, and verify each phase before moving to the next. Do not close issues or claim production readiness from documentation changes alone.

---

## 0. Findings and release posture

The public open issues reveal several related, release-blocking failures. Treat the following as the current working inventory; re-fetch issue states and repository HEAD before starting because GitHub can change after this review.

| Issue | Finding | Priority | Status of evidence |
|---|---|---:|---|
| [#3 App fails to launch: missing `central_platform.models`](https://github.com/Gayatri-Education/Gayatri-Demo/issues/3) | Source startup fails during imports; issue comments report independent reproduction and 9 test collection errors | P0 | Independently reported reproduction; repository tree has no `central_platform/models` path |
| [#5 Release evidence contradicts current test result](https://github.com/Gayatri-Education/Gayatri-Demo/issues/5) | Evidence says 34/34 passed although the import test requires the missing package | P0 | Repo evidence doc and current tree contradict one another |
| [#2 Mastery increases for arbitrary input](https://github.com/Gayatri-Education/Gayatri-Demo/issues/2) | Mastery is reported to increase on ungraded/junk/wrong answers; topic mastery and weak topics do not update correctly | P0 | Detailed reproduction provided in issue body; current state file has a correctness branch but must be traced end-to-end and verified |
| [#9 Potential HTML injection](https://github.com/Gayatri-Education/Gayatri-Demo/issues/9) | `app/ui/index.html` uses `innerHTML` via `appendMsg()` and template interpolation in tutor/evidence content; cleaner does not remove markup | P0 | Static risk confirmed; runtime exploit not confirmed in report |
| [#4 v4.0.0 release assets missing](https://github.com/Gayatri-Education/Gayatri-Demo/issues/4) | Repo docs refer to v4.0.0 ZIP/installer, but the current Releases API shows v3.0.1 and v3.0.0 only | P0 | Release endpoint checked during review |
| [#10 SHA-256 mismatch](https://github.com/Gayatri-Education/Gayatri-Demo/issues/10) | `SHA256SUMS.txt` has `2563E9…F710`; release evidence says `490416…1C42` for the same ZIP | P0 | Both values visible in tracked files; actual ZIP unavailable to independently hash in this review |
| [#11 Duplicate checksum report](https://github.com/Gayatri-Education/Gayatri-Demo/issues/11) | Duplicate/near-duplicate of #10, body points back to #10 | P2 | Visible issue body is a duplicate pointer |
| [#7 Windows 7 UI blurry/banner/input unusable](https://github.com/Gayatri-Education/Gayatri-Demo/issues/7) | Unsupported/legacy OS/runtime behavior and layout/input problems reported at 1366×768 | P1 | User report; requires declared support decision and compatible-runtime test |
| [#8 Windows 7 Python not recognized](https://github.com/Gayatri-Education/Gayatri-Demo/issues/8) | Source launch instructions require Python but reviewer has no Python launcher; portable binary should not require system Python | P1 | User environment issue plus documentation/package mismatch |

### Confirmed cross-cutting observations

1. `central_platform/learning/state.py`, `central_platform/courses/service.py`, and tests import `central_platform.models.schema`, but the current default-branch tree has no `central_platform/models/` package. This is a structural blocker, not a dependency installation problem.
2. `requirements.txt` only declares PySide6, Pydantic, pytest, pypdf, and python-docx. Do not infer missing modules can be fixed by pip-installing a third-party package: `central_platform.models.schema` is an internal application module and needs to be restored or correctly relocated.
3. `README.md` claims standalone packaging and provides both portable/installer names; `GETTING_STARTED_GUIDE.md` says Windows 10/11 and also offers `python -m app.main` as an alternative. These must be clearly separated into a source-development path and a no-Python portable-release path.
4. `scripts/build_demo.py` computes `SHA256SUMS.txt` during a local build, but that alone does not ensure the tracked manifest, release evidence, and uploaded GitHub Release asset all describe the same exact bytes.
5. The current release evidence reports 34 passing tests. That claim must be regenerated from clean CI after the broken import path is fixed. Do not preserve stale passing counts.
6. UI says `Preview` for teacher/admin screens; test whether they are read-only sample views versus fully connected features. Don't relabel a sample dashboard as production functionality without backend persistence/authorization and end-to-end behavior.

**Release rule:** Keep v4.0.0 marked blocked until the app starts from a clean source checkout, the full test suite passes, security regression tests pass, an independently verified portable package is attached to a release, and support claims match tested environments.

---

## 1. Operating protocol for the local AI agent

The agent must follow this protocol for every phase below.

### 1.1 Before editing

- Fetch current issue statuses, comments, default branch, HEAD commit, repo tree, CI configuration, release assets, and the exact current files named in the issue.
- Create a dedicated branch such as `fix/v4-release-blockers` (or a phase-specific branch if the team requires isolated PRs). Never commit directly to `main` unless explicitly authorized by the maintainer.
- Run `git status`, record Python/platform versions, and preserve a baseline log of failing commands.
- Read related implementation and tests before writing a patch. Search all references and aliases before moving or recreating a package.
- Write a phase plan with: hypothesis, files expected to change, potential compatibility risks, test matrix, rollback strategy, and explicit pass/fail gates.

### 1.2 Implementation requirements

- Fix root causes. No placeholder functions, fake green tests, skipped assertions, swallowed exceptions, hard-coded “success,” or changed expected values solely to pass CI.
- Keep changes minimal and coherent. Add regression tests before or alongside each bug fix.
- Use typed schemas and explicit validation. Handle invalid input and filesystem/database errors with visible, actionable errors and logs that do not leak sensitive data.
- All UI data derived from users, imported documents, RAG cards, model responses, and filenames is untrusted.
- Test from a clean checkout and fresh virtual environment. Preserve full logs and exact command exit codes.

### 1.3 Phase gate template

At the end of every phase, create/update `docs/ISSUE_FIX_PROGRESS.md` with:

- Phase ID and date
- Issues addressed and their current links/state
- Files changed and why
- Tests added/modified
- Commands run, environment, result and exit code
- Remaining failures, risks and follow-up items
- Explicit gate decision: `PASS` or `BLOCKED`

**Move to the next phase only if every mandatory test for the current phase passes.** When tests fail, debug the failing implementation, add a regression test, re-run the smallest reproducer, then rerun the complete relevant suite. Do not mark a phase complete when a platform-specific test cannot run; mark it `BLOCKED` and document the alternative CI/manual environment required.

---

## 2. Phase 0 — Baseline, provenance, and reproducibility

**Issues:** #3, #5, #4, #10, #11 (foundation for all issues)  
**Goal:** Capture the real state of the current code and prevent a stale report from being mistaken for verification.

### Tasks

1. Record exact HEAD SHA and branch; fetch current issue bodies/comments and latest GitHub Releases API response.
2. Create a clean disposable environment using a supported Python version from the project policy. The repo documentation currently cites Windows 10/11; test Python versions actually supported by its Qt/Pydantic dependency constraints rather than assuming 3.13/3.14 compatibility.
3. Run, capturing output and exit codes:
   - `python --version`
   - `python -m pip --version`
   - `python -m pip install -r requirements.txt`
   - `python -m pytest -q`
   - `python -m pytest tests/unit/test_imports.py -vv`
   - `python -m app.main --version`
   - `python -m app.main --check-startup`
4. Save raw logs as CI artifacts or under an ignored local audit folder. Only commit a concise results summary, not machine-specific paths or sensitive environment data.
5. Verify `central_platform/models/schema.py` and `DEMO_RELEASE_CONTRACT.md` are truly absent at HEAD; don't assume a stale issue points at today's HEAD.
6. Identify all current test collection errors, including whether they share the missing schema import.

### Acceptance gate

- A reproducible baseline log exists.
- The real failing tests are known and categorized as collection/startup/runtime/package/release failures.
- Nothing has been “fixed” by altering test assertions or rewriting the evidence report.

---

## 3. Phase 1 — Restore the missing domain schema package and make startup deterministic

**Issues:** #3, #5  
**Priority:** P0 — blocking application and automated QA.

### Root-cause investigation

Many runtime modules import `central_platform.models.schema` and tests refer to these types:

- `Course`, `Module`, `RAGChunk`, `MasteryState`, `TutorResponse`
- `LearningEvent`, `PedagogicalAction` (also imported in learning-state tests)

Inspect every import and every constructor/accessor usage throughout `central_platform/`, `app/`, `tests/`, `demo_data/`, and packaging spec before implementing the module. Existing course JSON/card structures and the tutor orchestrator define the compatibility contract.

### Implementation steps

1. Restore the intended `central_platform/models/` Python package with `__init__.py` and `schema.py`, OR move the schema to a deliberate canonical module and update every import consistently. Prefer restoring the documented/imported canonical path unless repository history proves otherwise.
2. Implement schemas that faithfully model the real data: required and optional fields, stable ID conventions, enum values, nested course/module structures, prerequisite IDs, optional retrieval score, timestamps, event evaluation/correctness, mastery/topic maps, pedagogical actions, evidence cards and tutor responses.
3. Use Pydantic consistently with the installed version. Avoid mutable list/dict defaults shared across instances. Validate numeric ranges (mastery 0–1, score values and positive order where appropriate), required identifiers, and enum serialization.
4. Ensure persisted JSON/SQLite records can be read across upgrades; define defaults/migrations where an older row might lack a field. Schema validation errors should have a useful, non-sensitive message.
5. Update PyInstaller hidden imports and packaging data if the package layout changes. Do not add random dependencies to paper over an internal module that should exist in the repository.
6. Add smoke tests for constructing/serializing/deserializing each schema, including optional values and malformed records.

### Regression tests

- `tests/unit/test_imports.py` imports all public domain schemas and instantiates CourseService, RAGService, LearningStateManager and TutorOrchestrator.
- A schema contract test exercises the types actually produced/consumed by course loader, RAG loader, bridge, and tutor orchestrator.
- `python -m app.main --version` and `--check-startup` pass in clean environment.

### Acceptance gate

- No missing internal-module import remains.
- Full test collection completes with **zero collection errors**.
- The app imports and headless startup preflight works from the source ZIP/clean checkout.
- This is not yet a release-ready pass; later phases remain.

---

## 4. Phase 2 — Correct mastery updates and learning analytics

**Issues:** #2 (and the current `tests/unit/test_mastery_progress.py`)  
**Priority:** P0 — educational integrity defect.

### Root-cause trace

Follow the complete path:

`BridgeFacade.sendQuery()` → `TutorOrchestrator.process_turn()` → answer evaluation/misconception handling → `LearningEvent` correctness/module/topic assignment → `LearningStateManager.record_event()` → SQLite mastery rows → `getAnalytics()` → UI progress widgets.

Current `state.py` has branches for `correctness is True/False`, but the issue reports that the real event path does not reliably set correctness/module IDs or update topic analytics. Do not stop after confirming the state manager's isolated test passes: verify what the orchestrator actually emits.

### Implementation steps

1. Define the event contract clearly:
   - Question/introduction/clarification/ungraded prose: `correctness=None`; must not alter mastery upward or downward.
   - Evaluated correct response: `correctness=True` only after the evaluator has judged a rubric/answer, not because the turn completed.
   - Evaluated incorrect answer: `correctness=False` and an explanatory misconception if evidence supports it.
   - Don't infer correctness merely from a regex not matching a known misconception.
2. Make evaluator outcome explicit and traceable (e.g., evaluated/not-evaluated plus evidence/rubric result). If no reliable evaluator decision exists, keep the event ungraded. Avoid claiming semantic correctness if the system only detects a small list of known errors.
3. Assign canonical `module_id` and topic/concept identifiers on each event whenever the active course and retrieved card/topic identify them; preserve `None` when genuinely unknown instead of fabricating an ID.
4. Update overall mastery and per-topic mastery from evaluated outcomes only. Keep values bounded and stable. Make `weak_topics` derive from explicit configured thresholds and observed results; don't return an empty list forever.
5. Deduplicate repeated event IDs deterministically. Current `INSERT OR REPLACE` may permit replays to reapply mastery even if event row identity is unchanged; add exactly-once semantics/transactional checks so retrying a request cannot double-count progress.
6. Rework misconception history: bounded recent history, de-duplication policy, and removal/decay once the learner demonstrates successful remediation. Keep an audit trail separately if history must be retained.
7. Make every state change transactional. Ensure database writes and aggregate updates cannot diverge on exceptions. Add schema migration logic for the event table if adding `correctness`, `topic_id`, or metadata columns.
8. UI must render values from actual analytics responses instead of hardcoded initial values like `78%`, `85%`, static weak-topic lists, or static recommendations. Show a clear “Not enough evaluated answers yet” state rather than misleading numeric mastery.

### Required tests

- Junk/irrelevant inputs (`asdfgh qwerty`, `hello`) leave mastery unchanged.
- Ungraded conceptual question leaves mastery unchanged.
- Incorrect evaluated response does not increase mastery and recommends supported remediation.
- Correct evaluated answer increments the intended topic and overall mastery once.
- Same event ID replayed twice updates exactly once.
- Different module/topic outcomes affect the right course/topic only.
- Course A progress does not leak into Course B; different students remain isolated.
- Weak topics populate after threshold is crossed and can recover after successful remediation.
- Misconception history is bounded and stale/current resolved items follow defined policy.
- Analytics UI values update after a turn and survive process restart.

### Acceptance gate

- All above regression tests pass.
- No path increases mastery for an ungraded response.
- All mastery shown in the UI is backend-derived and demonstrably persisted.

---

## 5. Phase 3 — Secure all untrusted HTML and document/RAG rendering

**Issues:** #9  
**Priority:** P0 security blocker.

### Suspected sinks

- `app/ui/index.html`: `appendMsg()` calls `msg.innerHTML = formatMarkdown(text)`.
- `renderTutorResponse()` and evidence-card rendering may interpolate message/title/content in HTML templates.
- `central_platform/rag/cleaner.py` removes control characters/normalizes whitespace but does not sanitize/remove HTML; it is a text cleaner, not an HTML security boundary.

### Implementation steps

1. Inventory *all* dynamic rendering sinks in `app/ui/index.html` and every JavaScript asset. Search `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, template strings, event attributes, and unsafe URL interpolation.
2. For plain text, use `textContent` and DOM element creation. Don't convert model/user/doc content to HTML to preserve formatting.
3. If Markdown is a required feature, use a maintained Markdown parser plus a trusted HTML sanitizer configured to remove scriptable elements/attributes/protocols. Apply sanitization **after** Markdown conversion and at the rendering sink. If adding a dependency conflicts with fully offline operation, bundle and pin vetted local assets; otherwise implement only a restricted safe Markdown renderer that emits DOM nodes (no raw HTML support).
4. Render each field separately: create evidence-card nodes, set title/body using `textContent`, set only known class names, and avoid concatenating untrusted text into tag/attribute strings.
5. Do not rely on `DocumentCleaner` for browser safety. It can normalize extracted text, and optionally strip markup for retrieval quality, but UI sink protection is mandatory even when data passed through the cleaner.
6. Audit any `QWebChannel`-provided strings and URL/file-path inputs. Keep `SecureWebPage` navigation policy restrictive; don't introduce broader navigation privileges to make features work.
7. Add an explicit CSP or equivalent local-page policy where compatible with the Qt WebEngine/QWebChannel setup, after validating required local scripts and inline handlers. Prefer moving inline scripts/handlers into local assets if feasible. CSP is defense in depth, not a substitute for safe DOM APIs.

### Required regression tests

Test user messages, model responses, card titles/content, filenames and imported document snippets containing:

- `<script>...` payload
- `<img src=x onerror=...>` payload
- SVG with event handler
- closing tags and quote/attribute breakout strings
- `javascript:` links and malformed Markdown links
- Unicode/control characters and oversized content

Assert malicious markup is rendered as inert text or removed according to policy and does not create scriptable DOM nodes/events. Run the tests in the actual Qt WebEngine/browser test harness as well as any pure parsing unit test. Include safe Markdown regression tests to preserve bold/lists/code behavior if those features are retained.

### Acceptance gate

- No untrusted content reaches an unsafe HTML sink.
- Security regression tests fail against the old implementation and pass against the fix.
- Verify manually with a controlled local payload; no outbound network required.

---

## 6. Phase 4 — Fix source vs portable installation and Windows support policy

**Issues:** #7, #8 (and prevents repeat #3 confusion)  
**Priority:** P1.

### Product decision required

The current `GETTING_STARTED_GUIDE.md` declares **Windows 10 64-bit and Windows 11 64-bit** as supported. Do not advertise Windows 7 as supported without a tested, separately maintained build and runtime. Qt WebEngine/Chromium/Python dependency compatibility makes this a platform-level decision, not a CSS-only fix.

Use one of two explicit support choices:

**Option A — Recommended:** Windows 10/11 only. Show a clear, non-blocking preflight/error dialog on unsupported OS versions and keep the supported runtime matrix honest. Don't show a banner that obscures the interface after startup.

**Option B — Legacy OS support:** Create a separate legacy build profile using dependencies genuinely supporting Windows 7, pin compatible versions, validate WebEngine/Chromium and Python ABI support, threat-model end-of-support security risk, and run a physical/VM Windows 7 regression suite. Don't infer compatibility from source code rendering in a modern environment.

### Source launch path

1. Provide separate instructions: supported system prerequisites, Python installation from a trusted official source, ensure PATH/launcher, `python -m venv .venv`, activate, `python -m pip install --upgrade pip`, `python -m pip install -r requirements.txt`, `python -m app.main`.
2. Include Windows Command Prompt and PowerShell variants, quoting paths with spaces.
3. Add a preflight command that checks runtime version/dependencies and prints actionable guidance if Python is missing or unsupported. Docs cannot make a missing interpreter magically available; tell source-checkout users they need Python.
4. Portable/installer package must launch through the packaged executable without Python installed. Verify in a clean Windows VM without Python.

### UI scale/input

1. Reproduce at 1366×768, Windows scaling 100/125/150%, and supported Qt WebEngine versions.
2. Remove/relocate any banner so it never overlays the title bar, chat input or main content. Unsupported OS state should be a clear dialog/documentation, not hidden content.
3. Validate CSS/layout at 1366×768: title bar, sidebar, tab content, course grid, chat input, evidence drawer and mastery cards; no clipping/overlap. Consider scalable typography and contrast; avoid tiny fixed font sizes where legibility suffers.
4. Confirm input remains focusable and Enter/Send works. Current `user-select: none` on `body` should be tested for accessibility side effects; set text selection on chat/reading content and sensible keyboard focus styles.
5. Ensure browser/runtime deprecation banners are not confused with an app-created “Need Windows 10 or later” banner; identify which process emits it and document/fix the source appropriately.

### Tests

- Source setup from clean Windows 10/11 VM.
- Portable launch on the same VM with no Python installed.
- Unsupported OS path produces a clear message and does not imply support.
- If Option B: Windows 7 VM smoke test, text input, UI scale, course switch, query, evidence and file upload.
- Resolution/scaling screenshots or automated visual regression checkpoints.

### Acceptance gate

- Support policy is unambiguous and is consistent across README, getting-started guide, installer metadata and release notes.
- The supported end-user path requires no undocumented dependency installation.
- No UI content is obstructed at the supported minimum resolution.

---

## 7. Phase 5 — Fix release artifact availability and make checksums single-source-of-truth

**Issues:** #4, #10, #11, #5  
**Priority:** P0.

### Immediate rule

Do not invent a checksum or choose one of the conflicting values by preference. The actual built release bytes are authoritative. The GitHub Releases API observed during review contains v3.0.1 and v3.0.0 releases, not a v4.0.0 release with the documented assets.

### Implementation steps

1. After Phases 1–4 pass, build v4 from a clean commit using the documented build environment. Confirm PyInstaller and Inno Setup availability and version; fail the release job if required deliverables are missing rather than print a success-looking message.
2. Verify the actual portable ZIP and Setup EXE exist, are non-empty, can be listed/extracted/installed, and pass smoke tests after packaging.
3. Compute SHA-256 using the final exact output files. Generate all checksum files programmatically from those bytes; never hand-edit values. Do not use a local tracked ZIP checksum before its final archive bytes exist.
4. Generate `SHA256SUMS.txt`, package manifest, release evidence and release notes from one build metadata result (filename, size, hash, commit SHA, build timestamp, supported OS, Python/build tooling versions, test summary). Avoid duplicated hashes maintained manually in multiple places.
5. In CI, independently re-hash downloaded release assets and compare to generated manifest. Ensure the manifest itself includes only deliverables that were actually produced and will be published.
6. Ensure the release workflow fails if an installer was promised but is missing. Current `build_demo.py` treats absence of Inno Setup as informational; decide explicitly whether ZIP-only release is allowed and make both release notes and release automation reflect the decision.
7. Publish a `v4.0.0` Release with matching assets only after final acceptance. Use draft release validation first; verify each asset name, byte size, hash, and download URL after upload.
8. Don't republish v4.0.0 with different bytes under the same immutable identity if it has already shipped to users. If already public, publish a corrected version (`v4.0.1` or similar) and clearly supersede the invalid checksums/artifacts.
9. Replace stale release-evidence counts with a CI-generated artifact or exact run link. Evidence must state the commit tested and must not be copied forward after source changes.
10. Inspect `scripts/build_demo.py` for silent failures: catch and report full relevant stdout/stderr for package tooling; verify subprocess results; confirm expected EXE paths; ensure `zipfile.testzip()` returns `None`; verify the generated launcher target exists; ensure `SHA256SUMS.txt` includes every and only published artifact.
11. Confirm data files written during build (`demo_data/courses.dat`) are either intentionally tracked/generated from a stable source or generated in a temporary staging workspace. Avoid a build unexpectedly dirtying the developer's source tree without clear documentation.
12. Issue #11 is a duplicate report. Once the canonical checksum defect is fixed and verified, mark #11 as duplicate of #10 using GitHub's issue state/duplicate function if the maintainer confirms; don't let two reports be treated as two different checksum bugs.

### Required checks

- Archive exists, is readable, and `testzip()` is clean.
- Extract then launch the extracted app in a clean environment.
- Installer installs, launches, and uninstalls cleanly (when installer is published).
- SHA-256 independently recalculated on the final ZIP/EXE equals generated manifest values.
- README, release notes, evidence and release page refer to the exact same filenames and release version.
- CI attaches logs, versions, test report, manifest and build metadata.

### Acceptance gate

- Release download page actually contains the files advertised in documentation.
- One exact artifact has one verified checksum everywhere.
- Evidence corresponds to the published commit/artifacts, not to an older checkout.

---

## 8. Phase 6 — RAG, ingestion and UI error-path hardening

**Issues:** #9; regression prevention for the platform claims in README/release notes.

### Tasks

1. Review parser routing for PDF/DOCX/TXT/Markdown, invalid extensions, malformed documents, empty documents, oversized files, unsupported encodings and encrypted PDFs.
2. Check path validation and file upload rules (`RAGSecuritySanitizer`, `DocumentParserRouter`, `DocumentCleaner`, configuration constants). Prevent path traversal, symlink surprises where applicable, decompression bombs, giant paragraph allocation and extension/MIME mismatch.
3. Ensure ingestion reports exact counts and errors. No “successful” message when 0 usable chunks were created; do not partially mutate the index after a failure.
4. Confirm uploaded content is isolated to the selected course; switching course flushes conversational context and retrieval indices remain scoped. Test folder aliases vs canonical course IDs.
5. Test RAG loader failures. Invalid JSON currently appears to be logged and skipped in some paths; surface degraded-index warnings in health information instead of silently presenting the source as fully indexed.
6. Add index-health diagnostics: expected files, cards/chunks loaded per course, failed files, last index time for uploads, active course ID and retrieval result count.
7. Audit exception handling in `BridgeFacade` and JavaScript. Catch exceptions for user-friendly display while logging technical details locally; never silently convert failures into empty success objects.
8. Make no-evidence/low-confidence response explicit to the tutor. Don't display a green “Verified Grounded” tag unless the response has evidence from the active course and satisfies a documented grounding rule.

### Tests

- Upload known-good fixtures for PDF/DOCX/TXT/MD, then query by unique content.
- Empty/corrupt/oversized/invalid-format document returns visible failure with zero partial chunks.
- A document added to course A never appears in course B.
- Test `courses.dat` corruption and directory fallback; make fallback/degraded mode observable.
- UI shows distinct loading, success, warning, empty, and error states.

### Acceptance gate

- No silent ingestion/indexing failure.
- Scope isolation, upload constraints and honest grounding status have regression tests.

---

## 9. Phase 7 — CI, release verification, and honest documentation

**Issues:** #5, #4 and all regression blockers.

### CI requirements

1. Add/repair a CI workflow on pull requests and release tags that:
   - installs a pinned supported Python version and dependencies;
   - runs import/lint/type checks configured by the repo;
   - runs all unit, RAG, tutor, security, headless, packaging-spec and release tests;
   - produces JUnit/coverage logs where applicable;
   - runs security scanning and dependency review appropriate for an offline app;
   - builds the portable package and optional installer on a Windows runner;
   - launches packaged output in a smoke test and generates checksums/manifest;
   - publishes artifacts only after all blocking gates pass.
2. Require the full suite to run from a fresh environment. A test that only passes on the author's machine is not release evidence.
3. Ensure CI actually fails when any test errors; don't mask failure with `continue-on-error`, shell commands ending with `|| true`, skipped tests, or release scripts that ignore a non-zero exit code.
4. Pin or constrain dependencies to a tested range and avoid unconstrained Qt upgrades that silently change platform/runtime compatibility.
5. Test data migration against both an empty database and a database produced by the previous supported build.

### Documentation corrections

- `README.md`: label v4.0.0 status truthfully (not “verified release” while build assets/tests are missing); provide current source and official release URLs; show supported OS and distinguish packaged binary from source launch.
- `GETTING_STARTED_GUIDE.md`: dependencies required only for source development; portable/installer users must not need Python.
- `RELEASE_EVIDENCE_v4.0.0.md`: regenerate from CI after final commit; include exact commit, workflow link, environment, test results, asset hashes, and limitations. Never retain claims that cannot be reproduced.
- `RELEASE_NOTES_v4.0.0.md`: align package manifest and supported OS policy with the actual release. Remove unsupported statements such as “zero leakage guaranteed,” “100% air-gapped,” “verified” or “production” unless tests/evidence establish their precise scope.
- `DEMO_BASELINE.md`: correct obsolete/missing source repository or contract references; if they are intentionally private/moved, link to an accessible authoritative replacement and document provenance. Do not claim a commit was verified if it cannot be fetched by a reviewer.
- Create `docs/ISSUE_FIX_PROGRESS.md` and keep it current in every phase.

### Acceptance gate

- Main CI is green on the exact candidate commit.
- Evidence and documentation generated from that candidate commit and release build.
- Maintainer can independently reproduce the reported test summary.

---

## 10. Phase 8 — End-to-end product validation and final release decision

### Critical user journeys

Perform on a clean supported machine and packaged build, not only via mocked services:

1. Launch app with no Python installed (portable release); close and relaunch.
2. Enumerate courses and verify displayed course IDs/titles/module/card counts match the loaded data.
3. Switch from Engineering Mathematics to Digital Electronics and confirm prior messages/retrieval state do not cross over.
4. Ask a grounded question; inspect evidence card content, source IDs, course IDs and truthful confidence indicator.
5. Send ungraded/junk input and verify mastery does not increase.
6. Submit an evaluated wrong and then correct answer; verify topic and overall mastery updates as designed, persisted across restart and shown accurately.
7. Upload a valid course note and query its unique phrase. Upload empty/corrupt/oversized and malicious HTML test files; confirm safe, explicit behavior.
8. Inspect Teacher Copilot and Institution Admin screens. Label any remaining hard-coded or sample-only analytics as a preview and never market them as live functionality. If they are advertised as functional, test real event-backed data, authorization, persistence and failure states.
9. Run tests in normal/air-gapped mode and verify no unintended external requests. Do not call the application “air-gapped” solely because a source scan failed to find obvious URLs.
10. Install/update/uninstall packaged setup build and ensure student data is neither unexpectedly deleted nor left in an undocumented location.
11. Test minimum supported resolution and display scaling; test keyboard navigation/focus, multiline or long responses, error display, and high-contrast readability.
12. Verify files downloaded from GitHub Releases hash to the checksum manifest.

### Final go/no-go checklist

- [ ] All P0 issues fixed and verified against the current HEAD.
- [ ] No import/collection/startup errors.
- [ ] All mastery correctness regression tests pass.
- [ ] UI XSS/injection tests pass in the real rendering engine.
- [ ] Supported OS/runtime matrix verified.
- [ ] No system Python required for portable build.
- [ ] Release asset(s) exist and launch; installer is only advertised if it exists and has been tested.
- [ ] Checksums computed from final uploaded bytes and independently verified.
- [ ] CI test report and release evidence match the exact commit being published.
- [ ] All features described as functional are wired to real behavior; sample/preview behavior is plainly disclosed.
- [ ] Open issues are closed only after the fix commit and evidence are linked; duplicates are marked duplicate rather than silently forgotten.

If any mandatory box is unchecked, release state remains **NO-GO**. Document the reason and do not use phrases such as “production-ready,” “all tests passed,” “zero data egress,” or “fully functional” without evidence for the claim.

---

## 11. Suggested implementation order and commit structure

1. `test: capture release baseline and reproduce blockers` (only harness/logging/progress additions; don't soften tests)
2. `fix: restore platform schema models and startup imports`
3. `fix: evaluate learning events before mutating mastery`
4. `security: render tutor and imported content safely`
5. `fix: clarify source setup and supported Windows runtime`
6. `build: generate verified v4 release artifacts and checksums`
7. `test: enforce CI release gates and end-to-end smoke checks`
8. `docs: align release claims with verified build evidence`

Commit/PR each coherent phase. Do not merge a release-documentation-only PR as a substitute for the P0 code fixes.

---

## 12. Source links checked during preparation

- [Open issues](https://github.com/Gayatri-Education/Gayatri-Demo/issues)
- [Issue #2 — mastery bug](https://github.com/Gayatri-Education/Gayatri-Demo/issues/2)
- [Issue #3 — missing models/startup failure](https://github.com/Gayatri-Education/Gayatri-Demo/issues/3)
- [Issue #4 — missing release artifacts](https://github.com/Gayatri-Education/Gayatri-Demo/issues/4)
- [Issue #5 — release evidence mismatch](https://github.com/Gayatri-Education/Gayatri-Demo/issues/5)
- [Issue #7 — Windows 7 UI](https://github.com/Gayatri-Education/Gayatri-Demo/issues/7)
- [Issue #8 — Python setup](https://github.com/Gayatri-Education/Gayatri-Demo/issues/8)
- [Issue #9 — HTML injection](https://github.com/Gayatri-Education/Gayatri-Demo/issues/9)
- [Issue #10 — checksum mismatch](https://github.com/Gayatri-Education/Gayatri-Demo/issues/10)
- [Issue #11 — duplicate checksum report](https://github.com/Gayatri-Education/Gayatri-Demo/issues/11)
- [Current repository](https://github.com/Gayatri-Education/Gayatri-Demo)
- [Current GitHub Releases](https://github.com/Gayatri-Education/Gayatri-Demo/releases)
- [README](https://github.com/Gayatri-Education/Gayatri-Demo/blob/main/README.md)
- [Getting started guide](https://github.com/Gayatri-Education/Gayatri-Demo/blob/main/GETTING_STARTED_GUIDE.md)
- [Release evidence](https://github.com/Gayatri-Education/Gayatri-Demo/blob/main/RELEASE_EVIDENCE_v4.0.0.md)
- [Checksum manifest](https://github.com/Gayatri-Education/Gayatri-Demo/blob/main/SHA256SUMS.txt)

