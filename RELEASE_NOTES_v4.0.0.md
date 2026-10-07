# GAYATRI PLATFORM v4.0.0 — MAJOR RELEASE NOTES

**Release Date:** 2026-10-08  
**Release Type:** Major Product Repositioning & Platform Demonstration  
**Target:** Universities, Engineering Colleges, and Higher Education Leadership  

---

## 🎯 Executive Release Summary

Gayatri v4.0.0 represents a major paradigm evolution from the earlier Chemistry-only v3.x releases. This release transitions Gayatri into an **institution-grade, course-independent adaptive learning platform**.

The objective of v4.0.0 is to prove to university vice-chancellors, deans, and IT heads that Gayatri can host arbitrary higher education curricula, ground its Socratic pedagogy strictly in institution-owned knowledge, and operate with complete offline privacy on standard Windows hardware.

---

## 🌟 What's New in v4.0.0

### 1. Course-Independent Socratic Engine
- **Decoupled Pedagogy:** Removed all subject-specific hardcoding from tutor logic.
- **Dynamic Context Binding:** The tutor orchestrator binds dynamically to any curriculum loaded into `demo_data/courses/`.
- **16-Step Closed-Loop Turn Lifecycle:** Enforces identity validation, scoped retrieval, misconception evaluation, and transactional learning state updates.

### 2. Multi-Course Curriculum Packages
- **Engineering Mathematics (MATH201):** Core engineering calculus, First-Order Differential Equations, Laplace Transforms, Fourier Series, and Linear Algebra.
- **Digital Electronics (EC202):** Number Systems, Boolean Algebra, Universal Gates, Combinational Logic, and Sequential Circuits.
- **Chemistry (CHEM101):** Repositioned as an optional legacy showcase dataset; no longer dominates product identity.

### 3. Isolated Scoped Knowledge Engine (RAG)
- **Course-Scoped Partitioning:** Guaranteed zero cross-course leakage. Engineering math queries retrieve strictly mathematical knowledge cards.
- **Sub-10ms Atomic Concept Retrieval:** High-performance in-memory BM25 ranker operating with zero vector-database overhead.
- **Evidence Drawer:** Transparently displays retrieved knowledge cards, confidence scores, and grounding verification tags to users.

### 4. Adaptive Misconception Diagnosis
- **Cognitive Diagnostics:** Identifies specific conceptual flaws (e.g. NAND logic inversion, De Morgan duality, Laplace initial conditions).
- **Anti-Answer-Leakage Invariant:** Guarantees that diagnostic feedback guides reasoning without revealing test solutions.
- **Mastery State Persistence:** Tracks real-time topic competencies and generates personalized next-action recommendations.

### 5. "Bring Your Curriculum" Ingestion Sandbox
- Upload lecture notes or syllabi in PDF, DOCX, TXT, or Markdown format.
- Real-time client validation, memory-bounded extraction, and live chunk indexing.

### 6. Institutional Visibility Previews
- **Teacher Copilot:** Class-level mastery heatmaps, cohort misconception alerts, and intervention tracking.
- **Institution Admin:** Course catalog management, knowledge indexing metrics, and air-gapped security status.

### 7. Security Hardening & Windows Antivirus Trust
- **Zero Telemetry / Air-Gapped:** Operates 100% offline with zero outbound network egress.
- **Strict Loopback Binding:** Local service binds exclusively to `127.0.0.1`, eliminating Windows Firewall prompts.
- **No Binary Packers:** Built with `upx=False` to prevent heuristic antivirus false positives.
- **Microsoft Defender Verified:** Clean scan completed on release distribution using `MpCmdRun.exe` (0 threats detected).

---

## 📦 Package Manifest

- `Gayatri_Adaptive_Learning_Platform_v4.0.0_Portable.zip` (Portable ZIP bundle)
- `Gayatri_Adaptive_Learning_Platform_v4.0.0_Setup.exe` (Inno Setup Installer)
- `SHA256SUMS.txt` (Cryptographic verification checksums)

---

## 🏛️ Provenance
Built from authoritative platform reference `Gayatri-Education/Gayatri` at commit `eee87194be0e69fa0f11923d2a59869f0f215816` adhering to `DEMO_RELEASE_CONTRACT.md` (SHA-256: `F1703332F2E19D590AA24D800B57F06870A7C5EEC522B51C9F94EA37B94A3BF8`).