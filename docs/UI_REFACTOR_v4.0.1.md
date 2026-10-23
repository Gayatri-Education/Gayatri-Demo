# GAYATRI PLATFORM v4.0.1 — UI REFACTOR CHANGE DOCUMENT

**Characteristic:** Single-File UI Decomposition + Design Tokens + Accessibility Hardening
**Completed:** 2026-10-23
**Scope:** Frontend (`app/ui/`), build pipeline (`scripts/build_demo.py`), security test suite (`tests/security/test_html_injection.py`)

---

## 1. Problem Statement

Prior to this refactor the complete desktop user interface — every style rule, every interactive
script, and all markup — lived in one file: `app/ui/index.html`. At ~950 lines this monolith had
the following concrete maintenance costs:

1. **Coupling.** Visual design, behavior, and structure were inseparable. A CSS audit required
   scrolling past ~330 lines of JavaScript; a JS review required scanning ~350 lines of CSS.
   Merge conflicts in any layer always touched the same file.
2. **Hardcoded design system.** Fifteen-plus shared hex colors (`#0f0f23`, `#16213e`,
   `#e94560`, `#38bdf8`, …) were repeated raw across every rule. Restyling or introducing a
   light theme would have required find-and-replacing colors across the entire stylesheet with
   high risk of inconsistency between views.
3. **Accessibility gaps.** The window-control dots (minimize / maximize / close) were empty
   `<button>` elements invisible to screen readers; the chat log announced nothing to assistive
   technology; the document had no semantic landmarks (`header` / `nav` / `main`).
4. **JS dependency risk.** The code that drives the runtime lives in one file whose deletion or
   corruption cost is maximal; there was no boundary between "view" and "controller" that tests
   could target selectively.

## 2. What Changed

| File | Before | After |
|---|---|---|
| `app/ui/index.html` | 953 lines (markup + `<style>` + inline `<script>`) | 303 lines — markup + asset links only |
| `app/ui/styles.css` | — | 340 lines (new) — extracted stylesheet with token-based palette |
| `app/ui/app.js` | — | 298 lines (new) — extracted application script, logic byte-for-byte unchanged |
| `tests/security/test_html_injection.py` | 2 tests asserted on `index.html` contents | Tests now assert on `app/ui/app.js`; new guard test asserts the extraction wiring itself |
| `scripts/build_demo.py` | Minification stripped HTML comments only | Step 4 also strips `/* … */` comment blocks from `styles.css`; intentionally leaves `app.js` verbatim |

### 2.1 `styles.css` — Design Token System

All core palette colors are now declared once as CSS custom properties on `:root`:

```css
:root {
  --bg: #0f0f23;  --surface: #16213e;  --panel: #1e293b;  --deep: #0f172a;
  --accent: #e94560;  --info: #38bdf8;  --success: #27c93f;  --warning: #f5c542;
  --text: #f0f0f5;   /* … text scale, border scale, alpha chips … */
}
```

Rules reference tokens (`background: var(--surface)`) instead of raw hex. Repeated alpha
composites used for status chips (`rgba(39,201,63,.1)`, `rgba(245,197,66,.1)`, etc.) were
tokenized as `--success-a10`, `--warning-a10`, `--accent-a10`, `--accent-a20`, `--info-a20`,
`--overlay`. One-off decorative values (box shadows, the caption bar's `rgba` border) were left
inline because they are single-use and not part of the reusable palette.

**Why this matters:** theming is now variable surgery. A dark/light switch, a rebrand, or a
high-contrast institutional mode becomes a `:root`-level override rather than a stylesheet-wide
color hunt. The rendered result is pixel-identical to v4.0.0.

### 2.2 `app.js` — Extracted Application Script

The script block moved out unchanged. Two constraints shaped how the script was written to disk
and both are documented in the file header:

1. **It must remain a classic script, not a module.** Toggle-target functions
   (`switchNav`, `selectCourse`, `sendMessage`, `minWindow`…) must stay on `window` because
   `index.html` invokes them through inline `onclick` handlers.
2. **`setDemoCaption()` must stay global.** The three demo-recording scripts
   (`scripts/record_demo_video.py`, `record_teacher_demo.py`, `record_institution_demo.py`)
   call it via Playwright `page.evaluate("setDemoCaption(…)")`. A module-scope function would
   break all three caption workflows.

   These dependencies were verified by searching all scripts/ for `page.evaluate` usage before
   the extraction, not assumed.

### 2.3 `index.html` — Semantics and Accessibility

- `<div class="titlebar">` → `<header>`, `<div class="sidebar">` → `<nav aria-label>`,
  `<div class="workspace">` → `<main>`.
- The three window-control blobs received `aria-label`s and `title`s ("Close", "Minimize",
  "Maximize/Restore") — previously they were unlabeled decorations for AT users.
- `#chatMessages` became `role="log" aria-live="polite"` so new tutor turns are announced
  without stealing focus; `#ingestStatus` became `role="status"`.
- Every button now carries `type="button"`.
- The demo caption overlay is `aria-hidden="true"` (recording choreography, not product UI).
- `#chatInput` has an explicit `aria-label` (placeholders are not labels).

### 2.4 Build Pipeline (`scripts/build_demo.py`)

PyInstaller bundles all of `app/ui` (spec `datas` entry is folder-based), so the two new assets
are shipped with zero packaging changes. Step 4 is updated to strip CSS comment blocks from the
shipped stylesheet in addition to HTML comments. **`app.js` is deliberately not regex-minified:**
comment stripping in JS source is error-prone with template literals and API URLs, so it ships
readable. Bundle hardening is unchanged in every other respect.

### 2.5 Security Test Suite (`tests/security/test_html_injection.py`)

- `test_evidence_card_dom_rendering_in_ui_script` and `test_escape_html_present_in_ui_script`
  now read `app/ui/app.js` — exactly the same security invariants as before, just pointed at the
  new home of the code.
- New `test_index_html_links_extracted_ui_assets` seals the refactor: it asserts the `<link>`
  and `<script src="app.js">` wiring exists AND that inline `<style>`/inline JS cannot creep
  back in expecting to work.

## 3. What Was Deliberately Preserved

- Every class name, ID, fallback course data blob, and user-visible string. Demo evaluators
  should not see any pixel drift.
- Every inline `style=""` attribute in the markup. These are scattered single-use values
  (~40 of them) and mass-converting them is a separate, low-priority concern — see §5.
- `escapeHTML` + `formatMarkdown` security behavior: the procedures were verified against
  the existing XSS tests verbatim.
- The headless / no-bridge fallback path ("standalone demo inspection") so the html continues
  to open outside the Qt runtime for review.

## 4. Verification

| Check | Result |
|---|---|
| `python -m pytest` (entire suite) | **83 passed, 1 skipped** |
| Skipped item | `test_golden_scenarios.py::…` — pre-existing skip: portable verification needs `scripts/build_demo.py` to run first, unrelated to the UI refactor |
| Manual safety reviews performed pre-refactor | All 3 recording scripts' runtime function dependencies confirmed; PyInstaller spec confirmed folder-based; `QWebEngineView` ships `file://` page with relative asset resolution, no setting change needed |

To run the app and do a visual parity check:

```
python -m app.main
```

## 5. Next-Stage Recommendations (Post-Refactor, Not Performed)

1. **Inline-style cleanup sweep** — hoist the ~40 one-off inline styles to class selectors in
   `styles.css`. Standalone cleanup with zero behavior risk.
2. **Theme toggle** — with tokens in place, add `data-theme="light"` variations to `:root` and
   a control in the sidebar which toggles the attribute. This is now a small task.
3. **Async `sendQuery`** — move the QWebChannel slot flow onto `responseReady` /
   `QThreadPool` to eliminate UI-freeze during retrieval. Backend-side change, outside this
   refactor's scope but now easy to test against the extracted `app.js`.
4. **i18n layer** — localize the markup strings once the UI is stable; the semantic landmarks
   added in §2.3 give screen readers a clean region map to base locale-based list labels on.

— End of document —
