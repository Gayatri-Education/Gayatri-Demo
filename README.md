# Gayatri — AI-Powered Adaptive Learning Platform

<div align="center">
  <img src="gai3.png" alt="Gayatri AI Logo" width="130" />
  <h3>Course-Independent Socratic Tutoring Grounded in Institution Knowledge</h3>
  <p><b>A Comprehensive Institutional Demonstration Release (v4.0.1)</b></p>
  <p><i>This project has been developed under Dbert Internship Program. (<a href="https://dbert.online">dbert.online</a>)</i></p>

  <p>
    <a href="#-whats-new-in-v401--engineering--trust-hardening"><img src="https://img.shields.io/badge/Release-v4.0.1%20Engineering%20Edition-e94560.svg" alt="Release v4.0.1" /></a>
    <img src="https://img.shields.io/badge/Inference-100%25%20Offline%20(Local)-success.svg" alt="100% Offline" />
    <img src="https://img.shields.io/badge/Security-Zero%20Data%20Egress-blue.svg" alt="Zero Data Egress" />
    <img src="https://img.shields.io/badge/Networking-Loopback%20(127.0.0.1)%20Only-teal.svg" alt="Loopback Only" />
    <img src="https://img.shields.io/badge/Trust-Microsoft%20Defender%20Clean-emerald.svg" alt="Defender Clean" />
  </p>
</div>

---

## 🌟 Executive Overview

**Gayatri is not merely a chatbot—it is an institution-grade adaptive learning platform.**

In higher education, generic cloud LLMs frequently fail students: they spoon-feed final answers, strip learners of cognitive struggle, leak sensitive data to the cloud, and lack grounding in university-specific curricula.

Gayatri solves this through localized, course-independent neural and symbolic intelligence:
- **Course-Agnostic Engine:** The core pedagogical orchestrator operates dynamically across distinct academic domains without hardcoded subject branches.
- **Strictly Scoped RAG Grounding:** Real-time retrieval matches only active course materials, guaranteeing zero cross-course data contamination.
- **Adaptive Socratic Pedagogy:** Guides students through analogies, graduated hints, and misconception diagnostics without premature answer disclosure.
- **Bring Your Curriculum:** Institutions can upload PDF, DOCX, or text notes to create instant custom knowledge sandboxes.
- **Absolute Data Sovereignty:** Operates 100% offline with strict loopback binding (`127.0.0.1`), zero telemetry, and zero cloud data egress.

---

## 🆕 What's New in v4.0.1 — Engineering & Trust Hardening

The pedagogical product behavior of v4.0.0 is unchanged; this revision hardens the runtime, the UI protocol, and the engineering practices. Full technical detail in [`docs/ENGINEERING_IMPROVEMENTS_v4.0.1.md`](docs/ENGINEERING_IMPROVEMENTS_v4.0.1.md).

| Change | What it means |
|---|---|
| **Non-blocking chat bridge** | Every tutor turn and curriculum ingestion runs on a Qt thread pool: the window never freezes, and the chat shows a live "Gayatri is thinking…" state. Results stream back over dedicated signals. |
| **Structured error envelopes** | Internal exceptions never reach the student UI. Errors surface as friendly messages with log-correlation references (`invalid_request` / `resource_missing` / `forbidden` / `internal_error`). |
| **Answer-leakage guardrail** | The platform's central Socratic promise — *never disclose the final answer* — is now enforced in code: during evaluation/remediation turns, card-sourced final answers are withheld with a guided reinterpretation, and 10 dedicated tests pin the invariant. |
| **Honest retrieval grounding** | Query-side stopword filtering eliminates fabricated grounding: off-course questions (e.g. *"what is microprocessor ?"* in Digital Electronics) no longer surface irrelevant cards as "grounded evidence." |
| **Guided discovery on misses** | When a query misses the knowledge base, the tutor enumerates the topics the course genuinely covers and points to the **Bring Curriculum** upload flow — no repetitive dead ends. |
| **Frontend decomposition** | 953-line monolithic `index.html` split into markup, `styles.css` (design tokens), and `app.js` — hardening-tested for injection safety. |
| **Canonical packaging + CI** | `pyproject.toml` (verified editable installs) and GitHub Actions CI on Windows runners: **ruff** lint, **mypy** type check, **pytest** with coverage — the full pipeline runs green locally with the same three commands. |

**Verification:** `ruff check .` → **mypy** → **pytest** — 105 tests (up from 83 in v4.0.0), all green. See [`docs/UI_REFACTOR_v4.0.1.md`](docs/UI_REFACTOR_v4.0.1.md) for the frontend split.

---

## 📚 Included Demonstration Curricula

| Course Code | Course Title | Modules Included | Knowledge Scope | Status |
|---|---|---|---|---|
| **MATH201** | **Engineering Mathematics** | 4 Modules (ODEs, Laplace, Fourier, Linear Algebra) | 30+ Concept Cards & Formulas | **Primary Core** |
| **EC202** | **Digital Electronics** | 4 Modules (Number Systems, Boolean, Logic Gates, Flip-Flops) | 35+ Concept Cards & Truth Tables | **Primary Core** |
| **CHEM101** | **Senior Secondary Chemistry** | 2 Modules (Thermodynamics, Molecular Bonding) | Legacy NCERT Concept Cards | *Optional Showcase* |

---

## 🎥 Captioned Demonstration Walkthroughs

Three dedicated, high-definition (720p HD) demonstration videos with on-screen dynamic captions are provided for different institutional stakeholders:

---

### 1. 🎓 Core Platform & Adaptive Learner Walkthrough
*Designed for academic evaluators, curriculum committees, and students.*

<div align="center">
  <img src="demo_video/gayatri_demo_preview.gif" alt="Gayatri Platform Demonstration Walkthrough" width="100%" style="border-radius: 8px; border: 1px solid #334155;" />
  <p>
    <b>Course-Independent Socratic Tutoring & Scoped RAG Grounding</b><br>
    🎬 <a href="demo_video/gayatri_v4_platform_demo.webm"><b>View High-Definition Video (WebM — 3.89 MB)</b></a> | 
    ⬇️ <a href="https://raw.githubusercontent.com/Gayatri-Education/Gayatri-Demo/main/demo_video/gayatri_v4_platform_demo.webm"><b>Direct Raw Download</b></a> |
    ⚙️ <a href="scripts/record_demo_video.py"><b>Recording Script</b></a>
  </p>
</div>

- **Key Highlights:** Real-time ODE inquiry, Retrieved Evidence Drawer citations, dynamic course switching to Digital Electronics with instant memory flush, and detection & remediation of the *NAND/NOR Logic Inversion Error*.

---

### 2. 👩‍🏫 Teacher Copilot & Faculty Walkthrough
*Designed for educators, professors, teaching assistants, and department heads.*

<div align="center">
  <img src="demo_video/gayatri_teacher_preview.gif" alt="Gayatri Teacher Copilot Walkthrough" width="100%" style="border-radius: 8px; border: 1px solid #334155;" />
  <p>
    <b>Classroom Intelligence, Cohort Health & Student Intervention Queue</b><br>
    🎬 <a href="demo_video/gayatri_teacher_demo.webm"><b>View High-Definition Video (WebM — 3.22 MB)</b></a> | 
    ⬇️ <a href="https://raw.githubusercontent.com/Gayatri-Education/Gayatri-Demo/main/demo_video/gayatri_teacher_demo.webm"><b>Direct Raw Download</b></a> |
    ⚙️ <a href="scripts/record_teacher_demo.py"><b>Recording Script</b></a>
  </p>
</div>

- **Key Highlights:** Class-level mastery tracking (42 students, 74.2% average), automated cohort misconception alerts (28% struggling with logic duality), student triage roster (identifying learners needing review before exams), Socratic anti-cheating scaffolding, and faculty note ingestion into local RAG.

---

### 3. 🏛️ Institution, School & Organization Governance Walkthrough
*Designed for university leadership, school boards, deans, CIOs, and compliance officers.*

<div align="center">
  <img src="demo_video/gayatri_institution_preview.gif" alt="Gayatri Institution Administration Walkthrough" width="100%" style="border-radius: 8px; border: 1px solid #334155;" />
  <p>
    <b>Air-Gapped Topology, Data Sovereignty & Enterprise Knowledge Oversight</b><br>
    🎬 <a href="demo_video/gayatri_institution_demo.webm"><b>View High-Definition Video (WebM — 3.47 MB)</b></a> | 
    ⬇️ <a href="https://raw.githubusercontent.com/Gayatri-Education/Gayatri-Demo/main/demo_video/gayatri_institution_demo.webm"><b>Direct Raw Download</b></a> |
    ⚙️ <a href="scripts/record_institution_demo.py"><b>Recording Script</b></a>
  </p>
</div>

- **Key Highlights:** 100% Offline Air-Gapped Topology, strict loopback (`127.0.0.1`), zero outbound telemetry, multi-department course boundary enforcement, Microsoft Defender Clean PE binaries, and complete FERPA/DPDP data sovereignty.

---

## 🚀 Key Demonstration Flows

### 1. Course Independence & Context Isolation
Switch seamlessly from **Engineering Mathematics** to **Digital Electronics**. The tutor immediately updates its curriculum context and knowledge retrieval scope. Mathematical queries in Digital Electronics return 0 math cards, guaranteeing complete domain separation.

### 2. Adaptive Misconception Remediation
Test Gayatri with common student reasoning errors (e.g., *"For a NAND gate, the output is 0 when any input is 0"*). Rather than marking the answer wrong and revealing the test solution, Gayatri diagnoses the exact reasoning flaw (*NAND/NOR Logic Inversion Error*), explains the underlying principle, and presents a targeted Socratic reflection question.

### 3. Bring Your Curriculum (Document Ingestion Sandbox)
Upload custom syllabus notes or lecture handouts (PDF/DOCX/TXT). The platform extracts, sanitizes, and indexes atomic knowledge cards in under 5 seconds, making them immediately queryable by the Socratic tutor.

### 4. Institutional Visibility Previews
- **Teacher Copilot:** Inspect class-wide performance heatmaps, cohort misconception alerts, and targeted intervention recommendations.
- **Institution Admin:** View course catalog topology, knowledge base indexing health, and air-gapped security compliance metrics.

---

## 📦 Release Artifacts & Execution Paths

- **Supported OS:** Windows 10 (64-bit) & Windows 11 (64-bit). Legacy Windows 7/8 is unsupported.

| Deliverable | Description | Checksum (SHA-256) |
|---|---|---|
| `Gayatri_Adaptive_Learning_Platform_v4.0.0_Setup.exe` | **Recommended:** Standalone Windows installer (**No Python required**). Self-contained single executable setup. | `D114903E06CFBFAF997736AE4CF071D37C1A73F8A3349D729F4F4897FA3643F0` |
| `Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip` | Standalone portable bundle (**No Python required**). Double-click `Gayatri_Launcher.bat` or `Gayatri.exe`. | `DB5A9FF381F097847CB88C828AE32431078C9C5657F8E301413000F758EBB886` |
| Developer Source Checkout | Requires Python 3.10+, pip dependencies. Follow [`GETTING_STARTED_GUIDE.md`](GETTING_STARTED_GUIDE.md) to run `python -m app.main`. Repository HEAD tracks **v4.0.1** (engineering revision; see [What's New](#-whats-new-in-v401--engineering--trust-hardening)). | GitHub Repository HEAD |

---

## 🛡️ Security, Privacy & Anti-Reverse Engineering Posture

- **Microsoft Defender Verified:** Clean scan completed on release distribution using `MpCmdRun.exe` (0 threats detected).
- **No Binary Packers (No UPX):** Standard PE executables prevent heuristic antivirus false positives.
- **Compiled PE Runtime:** All application logic is compiled into standalone native PE binaries; zero loose Python `.py` source code files are included in the distribution bundle.
- **Encapsulated Binary Curriculum Container:** Institutional syllabi, knowledge cards, and concept graphs are compiled and compressed into an obfuscated binary container (`courses.dat`), eliminating raw JSON card exposure.
- **Bytecode Stripping (-OO):** Python docstrings, assertions, and symbol annotations are stripped during release compilation.
- **Loopback Only:** Internal communication binds strictly to `127.0.0.1`, avoiding Windows Defender Firewall prompts.
- **SmartScreen Transparency:** New releases accumulate publisher reputation over time. Verify hashes via `SHA256SUMS.txt`.
- Complete audit report available in [`docs/SECURITY_AND_TRUST.md`](docs/SECURITY_AND_TRUST.md).

---

## 🎓 Program Attribution & Release Reference

This project has been developed under the **Dbert Internship Program** ([dbert.online](https://dbert.online)).

- **Authoritative Release Contract:** `DEMO_RELEASE_CONTRACT.md` (Commit: `eee87194be0e69fa0f11923d2a59869f0f215816`)
- **Release Documentation:** See [`RELEASE_NOTES_v4.0.0.md`](RELEASE_NOTES_v4.0.0.md) and [`INSTITUTION_DEMO_GUIDE.md`](INSTITUTION_DEMO_GUIDE.md).
- **v4.0.1 Engineering Change Record:** [`docs/ENGINEERING_IMPROVEMENTS_v4.0.1.md`](docs/ENGINEERING_IMPROVEMENTS_v4.0.1.md) (root-cause analyses and measured evidence) and [`docs/UI_REFACTOR_v4.0.1.md`](docs/UI_REFACTOR_v4.0.1.md).
- **Demonstration Walkthrough Video:** Available in [`demo_video/`](demo_video/).