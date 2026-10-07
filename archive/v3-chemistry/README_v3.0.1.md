# Gayatri Chemistry Tutor — Production SLM Edition

<div align="center">
  <img src="gai3.png" alt="Gayatri AI Logo" width="130" />
  <h3>An Evidence-Driven, 100% Offline Socratic AI Chemistry Tutor</h3>
  <p><b>Democratizing high-caliber 1:1 personalized education for Senior Secondary & Entrance Chemistry (NCERT Aligned)</b></p>

  <p>
    <a href="#-download-packages"><img src="https://img.shields.io/badge/Release-v3.0.1%20Production%20SLM-6366f1.svg" alt="Release v3.0.1" /></a>
    <img src="https://img.shields.io/badge/Inference-100%25%20Offline%20(CPU)-success.svg" alt="100% Offline" />
    <img src="https://img.shields.io/badge/Privacy-Zero%20Data%20Egress-blue.svg" alt="Zero Data Egress" />
    <img src="https://img.shields.io/badge/Syllabus-NCERT%20Class%2011%20%26%2012-orange.svg" alt="NCERT Class 11 and 12" />
    <img src="https://img.shields.io/badge/RAM%20Footprint-%3C%20850%20MB-purple.svg" alt="Low RAM Footprint" />
    <img src="https://img.shields.io/badge/Architecture-0.5B%20Socratic%20SLM-teal.svg" alt="Socratic SLM" />
  </p>
</div>

---

## 🌟 Vision & Mission

Education is most effective when it is **interactive, encouraging, and Socratic**. Yet millions of students prepare for board and entrance examinations without access to dedicated, patient, 1-on-1 tutoring.

Generic AI chatbots fail in education because they **spoon-feed final numerical answers**, depriving learners of the cognitive struggle necessary to master chemistry. Furthermore, existing cloud AI systems demand costly subscription fees, constant internet connectivity, and compromise student privacy.

**Gayatri Chemistry Tutor** solves this paradigm through localized neural intelligence:
- **Pure Socratic Pedagogy:** Never reveals final solutions prematurely; guides students through analogies, targeted questions, and misconception remediation.
- **Zero Digital Divide:** Runs 100% offline on standard consumer hardware (including school laptops with 8 GB RAM) without requiring internet or expensive GPUs.
- **Absolute Data Sovereignty:** Student chats, mastery records, and cognitive progress remain strictly on the local machine with zero telemetry or cloud egress.

---

## ⚡ Technical Highlights & Benchmark Specifications

### 🧠 1. Socratic Pre-Training & Alignment
- **Domain Specialization:** Fine-tuned on **2,500 curated Socratic dialogue trajectories** specifically calibrated to the NCERT/CBSE senior secondary chemistry syllabus.
- **5 Pedagogical Pillars Hardcoded in Model Weights:**
  1. **`EXPLAIN` Mode:** 4-tier scaffolding (Everyday Intuition $\to$ Formal Definition $\to$ Mathematical Law $\to$ Comprehension Check).
  2. **`QUESTION` Mode:** Calibrated numerical and conceptual problem posing.
  3. **`EVALUATE` Mode:** Real-time misconception diagnosis governed by the **Anti-Answer-Leakage Invariant** (diagnoses physical reasoning errors without giving away numerical answers).
  4. **`HINT` Mode:** Graduated 5-tier directional nudges.
  5. **`REMEDIATE` Mode:** Dynamic prerequisite backtracking along the curriculum dependency graph.

### 🔍 2. Sub-10ms Atomic Knowledge Retrieval (RAG)
- **Zero-VRAM Architecture:** Replaces heavy vector embedding models with lightweight, deterministic keyword and BM25 concept resolution.
- **Atomic Micro-Cards:** Structured curriculum cards (<75 tokens per card) providing factual NCERT grounding in **< 8 ms** retrieval time.
- **Coverage:** Chemical Thermodynamics (First Law, Hess's Law, Enthalpy, Entropy, Gibbs Free Energy), Chemical Bonding (VSEPR, Hybridisation, Molecular Geometry), and Periodic Trends.

### 💻 3. Real-World Hardware Benchmarks

| Performance Metric | Standard Student Laptop (8 GB RAM) | Desktop / Workstation (16 GB+ RAM) |
|---|---|---|
| **Target Processor** | Intel Core i3 / i5 (8th Gen+) or AMD Ryzen 3000 | Intel Core i7 / i9 or AMD Ryzen 5000+ |
| **Model Size on Disk** | **379.4 MB** (`Q4_K_M` 4-bit Medium quantization) | **379.4 MB** |
| **Active Inference RAM** | **~450 MB** | **~450 MB** |
| **Total App Footprint (GUI + WebEngine + Model)** | **~650 – 850 MB** total active memory | **~750 – 900 MB** total active memory |
| **Generation Latency (TTFT)** | **< 200 ms** to first streaming token | **< 120 ms** to first streaming token |
| **Streaming Speed** | **18 – 28 tokens / second** (smooth streaming) | **28 – 42 tokens / second** |
| **Application Cold Startup** | **< 2.4 seconds** (frameless animated splash) | **< 1.8 seconds** |
| **External Network Bandwidth** | **0.0 KB/s (Strictly Air-Gapped)** | **0.0 KB/s (Strictly Air-Gapped)** |

---

## 📦 Download Packages

| Asset | Format | File Size | Description |
|---|---|---|---|
| **[`Gayatri_Chemistry_Tutor_v3.0.1_Setup.exe`](https://github.com/Gayatri-Education/Gayatri-Tutor-ChemistryDemo/releases/download/v3.0.1/Gayatri_Chemistry_Tutor_v3.0.1_Setup.exe)** | Windows Installer | **511.7 MB** | **All-in-One Installer (Recommended):** Setup wizard with the fine-tuned 0.5B Socratic SLM model pre-bundled inside it! Installs to user directory, creates Desktop & Start Menu shortcuts with lotus branding, and includes an uninstaller. Zero separate model download needed. |
| **[`Gayatri_Chemistry_Tutor_Portable_v3.0.1.zip`](https://github.com/Gayatri-Education/Gayatri-Tutor-ChemistryDemo/releases/download/v3.0.1/Gayatri_Chemistry_Tutor_Portable_v3.0.1.zip)** | Portable ZIP | **577.7 MB** | **All-in-One Portable:** Extract to any folder or USB pen drive and run `Gayatri_Chemistry_Tutor.exe`. 100% self-contained with pre-bundled model and no registry footprint. |
| **[`Gayatri-Tutor-SLM-Q4_K_M.gguf`](https://github.com/Gayatri-Education/Gayatri-Tutor-ChemistryDemo/releases/download/v3.0.1/Gayatri-Tutor-SLM-Q4_K_M.gguf)** | Model Weights | **379.4 MB** | Standalone 0.5B Socratic SLM weights (for LM Studio, Ollama, or Python deployments). |
| **[`SHA256SUMS.txt`](https://github.com/Gayatri-Education/Gayatri-Tutor-ChemistryDemo/releases/download/v3.0.1/SHA256SUMS.txt)** | Checksums | 1 KB | Cryptographic SHA-256 integrity verification hashes. |
| **[`GETTING_STARTED_GUIDE.md`](GETTING_STARTED_GUIDE.md)** | User Guide | 5 KB | Quick start guide and 6 interactive hands-on learning exercises. |

---

## 🚀 1-Click Quick Start

1. Download **`Gayatri_Chemistry_Tutor_v3.0.1_Setup.exe`** (or the Portable ZIP).
2. Run the installer (or extract the portable ZIP).
3. Double-click the **`Gayatri Chemistry Tutor`** desktop shortcut.
4. The application launches immediately with the Socratic AI model pre-loaded!

> 💡 **For a guided walkthrough of the 6 core Socratic capabilities, read the [Getting Started & Hands-On Walkthrough Guide](GETTING_STARTED_GUIDE.md).**

---

## 🧪 Experience Socratic Adaptive Learning

Unlike conventional chatbots, Gayatri actively models your cognitive state:

```text
                  ┌─────────────────────────────────────────┐
                  │          Student Input / Answer         │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │      Deterministic Answer Evaluator     │
                  │ (Tolerance, Units, Chemical Conventions)│
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │        Pedagogical Learning Event       │
                  │   (Misconception Diagnosed? -5% Mastery)│
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │       Adaptive Policy & State Machine   │
                  │  (EXPLAIN ➔ QUESTION ➔ EVALUATE ➔ HINT) │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │        Socratic SLM Generation          │
                  │  (Atomic RAG Evidence + Anti-Leak Guard)│
                  └─────────────────────────────────────────┘
```

1. **Deductive Understanding Over Spoon-Feeding:** If you submit an incorrect calculation, Gayatri praises your physical reasoning, points out the misconception, and asks you to recalculate without revealing the answer.
2. **Prerequisite Backtracking:** If you struggle repeatedly with an advanced topic (e.g., First Law enthalpy calculations), the tutor shifts into `REMEDIATE` mode and backtracks along the prerequisite graph to foundational concepts (e.g., Internal Energy).
3. **Visual Mastery Roadmap:** The integrated student dashboard displays an interactive dependency DAG of senior secondary chemistry concepts, active focus areas, and spaced review recommendations.

---

## 🔒 Cryptographic Verification

Verify package integrity using PowerShell:
```powershell
Get-FileHash Gayatri_Chemistry_Tutor_v3.0.1_Setup.exe -Algorithm SHA256
```

| File Name | SHA-256 Integrity Hash |
|---|---|
| `Gayatri_Chemistry_Tutor_v3.0.1_Setup.exe` | `277a6341b659e12c6ec3933a6c65b1af68d1332c3b57c617c38340385637d2bf` |
| `Gayatri_Chemistry_Tutor_Portable_v3.0.1.zip` | `42d9fe33dc9cda38d3ff95dd52cbe7da7034fcbcdc4e1530b6246027ff8a87cf` |
| `Gayatri-Tutor-SLM-Q4_K_M.gguf` | `eb4d05df2bf3eb7405d24742ade2622fc3f98b4be2b75d92dc2c00339d2b952b` |
| `GETTING_STARTED_GUIDE.md` | `b2fc48634b0f65bae74caa027d9615d82ff11f732023753bafd406ef2da13628` |

---

## 💻 System Requirements

- **Operating System:** Windows 10 (64-bit) or Windows 11 (64-bit)
- **Processor:** Any dual-core or quad-core x64 CPU (Intel Core i3/i5/i7/i9 or AMD Ryzen)
- **RAM:** 4 GB minimum (8 GB recommended for optimal multi-tasking)
- **Disk Space:** ~650 MB free disk space (Application + Model combined)
- **GPU:** Optional (Native CPU inference with zero hardware acceleration required)
- **Python / Dependencies:** **None required** (Completely self-contained native binary)

---

<div align="center">
  <p><b>Gayatri Education</b></p>
  <p><i>Empowering Students • Advancing Socratic Pedagogy • Zero Cloud Dependency</i></p>
</div>
