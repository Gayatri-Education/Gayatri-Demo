# GAYATRI PLATFORM v4.0.0 — UX & SCREEN SPECIFICATION

## 1. Executive Product Positioning

- **Product Title:** Gayatri — AI-Powered Adaptive Learning Platform
- **Core Positioning:** Course-independent Socratic tutoring grounded in institution-defined knowledge.
- **Audience:** Higher education institutes, engineering college deans, faculty, and academic directors.
- **Branding Invariant:** Must NEVER be positioned as a subject-specific (e.g., Chemistry-only) tool. The platform is inherently multi-course and curriculum-agnostic.

---

## 2. Design System & Visual Foundation

- **Primary Background:** `#0f0f23` (Deep Midnight Obsidian)
- **Secondary Surface:** `#16213e` (Card / Navigation Chrome)
- **Accent Primary:** `#e94560` (Vibrant Coral / Gayatri Flame)
- **Accent Secondary:** `#4e54c8` (Deep Royal Indigo)
- **Success Tone:** `#27c93f` (Grounded / Verified Emerald)
- **Warning Tone:** `#f5c542` (Misconception Amber)
- **Text Primary:** `#f0f0f5` (High Contrast White)
- **Text Secondary:** `#9ca3af` (Subtle Muted Slate)
- **Typography:** `Segoe UI`, system-ui, -apple-system, sans-serif

---

## 3. Screen Flows & Experience Architecture

### Screen A — Welcome & Platform Positioning
- Hero banner with official Gayatri crest and headline: **"AI-Powered Adaptive Learning Platform"**.
- Value propositions highlighted:
  1. *Course Independence:* Adaptable across STEM and humanities curricula.
  2. *Institutional Knowledge:* Real-time RAG grounding in university materials.
  3. *Adaptive Pedagogy:* Socratic tutoring with cognitive misconception diagnosis.
- CTAs: `Enter Demo (Guided Showcase)` and `Explore Sandbox`.

### Screen B — Mode Selection
- **Guided Showcase:** Curated 7-step interactive walkthrough demonstrating the full educational narrative.
- **Explore Sandbox:** Unrestricted exploratory environment allowing custom prompts, course switches, and custom document uploads.

### Screen C — Course Selector
- Dual Primary Course Cards:
  1. **Engineering Mathematics (MATH201):** Differential Equations, Laplace Transforms, Fourier Series, Linear Algebra.
  2. **Digital Electronics (EC202):** Number Systems, Boolean Algebra, Logic Gates, Sequential Circuits.
- Optional 3rd Card: **Chemistry (CHEM101)** (explicitly badged as "Optional Legacy Showcase").
- Metadata on each card: active modules count, knowledge card count, AI tutor status.

### Screen D — Course Overview & Curriculum Map
- Unit breakdown and prerequisite dependency graph visualization.
- Learner mastery summary for selected course.
- CTA: `Start Socratic Tutoring`.

### Screen E — Interactive Tutor Chat
- Multi-turn conversation container with rich markdown, LaTeX/math formatting ($...$, $$...$$).
- Strict Socratic pedagogy: avoids immediate answer dumps; offers intuitive analogies and graduated hints.

### Screen F — RAG / Grounding Evidence Drawer
- Slide-out drawer displaying:
  - Source document and module name.
  - Retrieved knowledge card snippets and confidence score.
  - Grounding status badge: `Verified Grounded` or `General Reasoning`.

### Screen G — Adaptive Learning & Misconception Remediation
- Dynamic feedback module when student demonstrates a cognitive gap.
- Breaks down the root misconception, offers targeted remediation, and poses a follow-up comprehension check.

### Screen H — Course Switching Transition
- Real-time course switcher in navigation header.
- Immediate actions on switch:
  1. Flushes active conversation memory and RAG context cache.
  2. Swaps curriculum syllabus and knowledge scope.
  3. Prohibits cross-course retrieval leakage.

### Screen I — Student Progress Dashboard
- Mastery radar / progress bars by topic.
- Cognitive strengths and identified weakness list.
- Recommended next study action.

### Screen J — Teacher Copilot Preview
- Class-level performance heatmap and mastery distribution.
- Alerts on common cohort misconceptions.
- Actionable intervention recommendations for faculty.

### Screen K — Institution / Admin Preview
- Course catalog management and enrollment overview.
- Knowledge base indexing status and health metrics.

### Screen L — "Bring Your Curriculum" Upload Sandbox
- Drag-and-drop file upload for PDF, DOCX, TXT.
- Real-time client validation, memory-bounded extraction, and live chunk indexing.
- Immediate query test sandbox against uploaded document.
