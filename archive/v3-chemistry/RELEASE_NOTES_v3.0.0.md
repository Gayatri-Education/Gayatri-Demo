# Gayatri Chemistry Tutor v3.0.0 — NCERT Adaptive Learning Platform

Welcome to the **v3.0.0 official release** of **Gayatri Chemistry Tutor**, an evidence-based, adaptive pedagogical tutoring platform designed specifically for senior secondary (CBSE Class 11/12) and entrance chemistry.

Unlike conventional chatbots that dump textbook solutions, Gayatri is a **Socratic cognitive tutor** running **100% offline on local hardware** using a specialized fine-tuned 3-Billion parameter Small Language Model (**`Gayatri-Tutor-v3`**).

---

## 📦 Download Packages

| Asset | Format | Size | SHA-256 Checksum | Description |
|---|---|---|---|---|
| **`Gayatri_Chemistry_Tutor_Portable_v3.0.0.zip`** | Portable ZIP | 1.99 GB | `2af6486a2a20aa7563bf80871dd0ac84fccb25b44f3c6ec9f25312d5cc9df15e` | **Recommended:** Extract and double-click `Gayatri_Chemistry_Tutor.exe`. Zero installation required, runs 100% offline. |
| **`Gayatri_Chemistry_Tutor_v3_Setup.exe`** | Windows Setup | 1.90 GB | `2384fecd852fa40d8d964c9359792b2e5559e544d70414c2251e04e6e9394d34` | Windows setup wizard that installs the app, creates Desktop/Start Menu shortcuts with the `gai3.ico` lotus icon, and adds an uninstaller. |
| **`Gayatri-Tutor-v3-Q4_K_M.gguf`** | GGUF Weights | 1.80 GB | `fa66d940d1279d844d43be9b6c45b5f9b22d5bce1eed901516394f1d6202abc3` | Standalone quantized 3B model weights for custom deployments (compatible with llama.cpp, LM Studio, and Ollama). |
| **`SHA256SUMS.txt`** | Checksums | 1 KB | — | Cryptographic SHA-256 integrity verification hashes. |
| **`EVALUATION_GUIDE.md`** | Testing Guide | 5 KB | `567a2d2c3c4091f1960310486b88e1ce8b962dcfff0faad0c82e9737a1af7bbe` | 6-step interactive evaluator checklist to test adaptive learning on your laptop. |

---

## 🌟 Key Highlights & Architectural Capabilities

1. **Evidence-Based Socratic Scaffolding (`EXPLAIN` Mode):**
   - Implements a structured 4-tier pedagogical scaffold: Everyday Analogy $\to$ NCERT Definition $\to$ Mathematical Formulation ($\Delta U = q + w$) $\to$ Reflective Comprehension Check.
2. **Misconception Diagnosis Without Answer Leakage (`EVALUATE` Mode):**
   - Pinpoints conceptual errors (e.g., IUPAC expansion work sign confusion) and dynamically adjusts mastery scores (-5%) while **strictly preserving the Anti-Answer Leakage invariant** (never giving away the final numerical solution).
3. **5-Tier Scaffolded Hint Ladder (`HINT` Mode):**
   - Delivers graduated conceptual nudges, allowing students to bridge conceptual gaps independently without spoon-feeding answers.
4. **Learning Dependency Graph (LDG) Prerequisite Traversal (`REMEDIATE` Mode):**
   - When students struggle repeatedly with advanced concepts, the tutor automatically backtracks along the prerequisite graph (e.g. from First Law to Internal Energy) to shore up foundational understanding.
5. **Interactive Student Progress Dashboard (DAG Visualizer):**
   - Visualizes chapter mastery bars, an interactive prerequisite dependency DAG roadmap, actionable smart study tips, and a real-time learning journey activity stream.
6. **Multi-Domain Breadth:**
   - Seamlessly transitions between Physical Chemistry (Thermodynamics, Kinetics) and Inorganic/Organic Chemistry (VSEPR molecular geometries, periodic trends).
7. **3-Layer Safety Guardrails:**
   - Input sanitization, prompt injection interception, strict topic boundary enforcement, and safe chemical laboratory hazard education.
8. **100% Offline Data Sovereignty:**
   - Runs strictly in `Local Only` mode. All conversations, student mastery records, and vector embeddings are stored locally in SQLite with **zero cloud egress**.

---

## 💻 System Requirements

- **Operating System:** Windows 10 (64-bit) or Windows 11 (64-bit)
- **Processor:** Intel Core i5 (8th Gen+) or AMD Ryzen 3000+ (4+ physical cores)
- **Memory (RAM):** 8 GB minimum (16 GB recommended)
- **Disk Space:** 5 GB free storage (SSD strongly recommended)
- **Graphics (GPU):** Optional (runs 100% on CPU; auto-detects Vulkan/CUDA if present)
- **Python / Dependencies:** **None required** (fully self-contained standalone binary)

---

## 🔍 How to Verify Integrity

Verify the cryptographic SHA-256 checksums using PowerShell:
```powershell
Get-FileHash Gayatri_Chemistry_Tutor_Portable_v3.0.0.zip -Algorithm SHA256
```
Compare the output against the values in `SHA256SUMS.txt`.

---
*Developed with pride by Gayatri Education.*
