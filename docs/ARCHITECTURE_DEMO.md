# GAYATRI DEMO v4.0.0 — ARCHITECTURE BOUNDARY & SUBSYSTEM DECOUPLING

## 1. Design Objective
The v4 demo showcases the Gayatri platform capabilities through a self-contained, offline-first application bundle without distributed cloud dependencies (Redis, Postgres clusters, cloud LLM APIs).

## 2. Reusable Subsystem Inventory from `Gayatri`

| Subsystem | Source in Gayatri | Implementation in Gayatri-Demo | Rationale |
|---|---|---|---|
| **Course Domain** | `central_platform/courses` | `central_platform/courses/service.py` | Multi-course lifecycle, offerings, and prerequisite trees. |
| **RAG Knowledge Engine** | `central_platform/rag` | `central_platform/rag/service.py` | Scoped BM25 card retriever, parser router, security sanitization. |
| **Tutor Orchestration** | `central_platform/tutor` | `central_platform/tutor/orchestrator.py` | 16-step turn lifecycle, anti-answer leakage, Socratic prompting. |
| **Adaptive Learning State** | `central_platform/learning` | `central_platform/learning/state.py` | Session persistence, cognitive mastery graphs, SQLite storage. |
| **Pedagogical Actions** | `central_platform/learning/actions` | `central_platform/learning/actions.py` | Misconception diagnosis, next-action evaluation (`EXPLAIN`, `CHECK`, `REMEDIATE`). |
| **Model / AI Adapter** | `central_platform/ai` | `central_platform/ai/adapters.py` | Offline SLM runtime with deterministic fallback engine. |
| **UI Presentation Shell** | `app/` | `app/` | PySide6 frameless window + QWebEngineView + QWebChannel bridge. |

## 3. Strict Boundary Rules
1. **Zero External Egress:** Local loopback socket binding (`127.0.0.1`) only.
2. **Deterministic Fallbacks:** If native AVX2 model inference is not available on test hardware, the AI adapter switches smoothly to the deterministic pedagogical rule engine without crashing.
3. **No Cross-Course Leakage:** RAG queries are explicitly filtered by `course_id`.
