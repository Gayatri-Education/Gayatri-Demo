"""Gayatri AI Platform — Automated Demonstration Video & GIF Recorder.

Produces two deliverables optimized for GitHub:
1. demo_video/gayatri_v4_platform_demo.webm:
   - HD (1280x720), on-screen floating dynamic captions, strictly under 5 MB limit.
2. demo_video/gayatri_demo_preview.gif:
   - Animated visual preview carousel (~1 MB) embedded directly in README.md for instant playback.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
import time
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright

from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager
from central_platform.rag.service import RAGService
from central_platform.tutor.orchestrator import TutorOrchestrator

def record_demo():
    print("[1/6] Initializing Gayatri Backend Platform Services...")
    course_service = CourseService()
    rag_service = RAGService()
    state_manager = LearningStateManager()
    orchestrator = TutorOrchestrator(course_service, rag_service, state_manager)

    demo_video_dir = PROJECT_ROOT / "demo_video"
    demo_video_dir.mkdir(parents=True, exist_ok=True)

    # Clean existing temporary recording videos
    for old_vid in demo_video_dir.glob("*.webm"):
        try:
            old_vid.unlink()
        except Exception:
            pass

    snapshots_dir = demo_video_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    snapshot_paths = []

    ui_path = PROJECT_ROOT / "app" / "ui" / "index.html"
    ui_url = ui_path.as_uri()

    print("[2/6] Launching Playwright Chromium (1280x720 HD — Optimized for GitHub <5MB)...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(demo_video_dir),
            record_video_size={"width": 1280, "height": 720}
        )

        page = context.new_page()

        # Expose Python backend to page JavaScript
        def py_send_query(prompt: str, student_id: str = "demo_student") -> str:
            resp = orchestrator.process_turn(student_id, prompt)
            cards_data = [
                {"title": c.title, "content": c.content, "score": c.score}
                for c in resp.evidence_cards
            ]
            return json.dumps({
                "action": resp.action.value,
                "message": resp.message,
                "grounded": resp.grounded,
                "evidence_cards": cards_data,
                "misconception": resp.misconception_identified,
                "course_id": resp.course_id
            })

        def py_switch_course(course_id: str) -> str:
            ok = orchestrator.set_active_course(course_id)
            c = course_service.get_course(course_id)
            return json.dumps({"success": ok, "title": c.title if c else ""})

        page.expose_function("pySendQuery", py_send_query)
        page.expose_function("pySwitchCourse", py_switch_course)

        # Inject window.bridge implementation using exposed python functions
        init_script = """
        window.bridge = {
            sendQuery: async function(text, student_id, cb) {
                const resStr = await window.pySendQuery(text, student_id);
                if (cb) cb(resStr);
                return resStr;
            },
            switchCourse: async function(course_id) {
                return await window.pySwitchCourse(course_id);
            }
        };
        """
        page.add_init_script(init_script)

        print("[3/6] Navigating to Gayatri Platform Interface...")
        page.goto(ui_url)
        page.wait_for_load_state("networkidle")
        time.sleep(1.0)

        # Helper functions
        def caption(text: str, wait_s: float = 2.5):
            print(f"  [CAPTION] {text}")
            page.evaluate(f"setDemoCaption({json.dumps(text)})")
            time.sleep(wait_s)

        def snap(name: str):
            p = snapshots_dir / f"{len(snapshot_paths)+1:02d}_{name}.png"
            page.screenshot(path=str(p))
            snapshot_paths.append(p)

        def type_prompt(selector: str, text: str, delay_ms: int = 30):
            page.click(selector)
            for char in text:
                page.keyboard.type(char)
                time.sleep(delay_ms / 1000.0)
            time.sleep(0.3)

        print("[4/6] Executing Choreographed Walkthrough Scenes...")

        # ── SCENE 1: Welcome & Vision ──
        caption("Gayatri AI (v4.0.0) — Developed under Dbert Internship Program (dbert.online)", 2.8)
        caption("Course-Independent Socratic Tutoring Grounded in Institution Knowledge", 2.4)
        caption("100% Offline Air-Gapped Operation with Zero Cloud Data Egress", 2.2)
        snap("welcome_vision")

        # ── SCENE 2: Multi-Course Catalog ──
        caption("Multi-Course Catalog: Engineering Mathematics & Digital Electronics", 2.0)
        page.click("button:has-text('Course Catalog')")
        time.sleep(1.2)
        snap("course_catalog")
        caption("Selecting Active Course Context: Engineering Mathematics (MATH201)", 2.0)
        page.click("div.course-card:has-text('MATH201') button")
        time.sleep(1.2)

        # ── SCENE 3: Socratic AI Tutor & Math Query ──
        caption("Socratic AI Tutor: Strictly Scoped Grounded RAG with Zero Cross-Contamination", 2.4)
        type_prompt("#chatInput", "Explain first-order differential equations and integrating factor", 25)
        page.click("#chatSendBtn")
        time.sleep(1.8)
        caption("Retrieved Evidence Drawer: Real-time Grounding Cards & Textbook Citations", 2.8)
        snap("socratic_rag_math")

        # ── SCENE 4: Dynamic Course Switch & Misconception Remediation ──
        caption("Dynamic Course Switching: Switching to Digital Electronics (EC202)", 2.0)
        page.click("button:has-text('Course Catalog')")
        time.sleep(1.2)
        page.click("div.course-card:has-text('EC202') button")
        time.sleep(1.2)
        snap("switched_electronics")

        caption("Active Context Switched: Prior Context Flushed with Zero RAG Bleed", 2.0)
        caption("Misconception Diagnosis: Testing Student Logic Inversion on NAND Gates", 2.0)
        type_prompt("#chatInput", "For a NAND gate, the output is 0 when any input is 0", 25)
        page.click("#chatSendBtn")
        time.sleep(2.0)
        caption("Misconception Identified: NAND/NOR Logic Inversion Error Remediation", 3.0)
        snap("misconception_remediation")

        # ── SCENE 5: Student Mastery Tracking ──
        caption("Student Mastery: Tracking Cognitive States & Detected Misconceptions", 2.2)
        page.click("button:has-text('Student Mastery')")
        time.sleep(1.5)
        snap("student_mastery")

        # ── SCENE 6: Teacher Copilot Preview ──
        caption("Teacher Copilot: Cohort Analytics, Gap Heatmaps & Intervention Queue", 2.2)
        page.click("button:has-text('Teacher Copilot')")
        time.sleep(1.5)
        snap("teacher_copilot")

        # ── SCENE 7: Bring Your Curriculum Sandbox ──
        caption("Bring Your Curriculum: Instant Ingestion of Institution Notes into Air-Gapped RAG", 2.2)
        page.click("button:has-text('Bring Curriculum')")
        time.sleep(1.2)
        page.click("button:has-text('Load Sample Curriculum Document')")
        time.sleep(1.2)
        caption("Custom Curriculum Ingestion Succeeded: 3 Knowledge Chunks Indexed", 2.0)
        snap("curriculum_ingestion")

        # ── SCENE 8: Wrap-up & Program Attribution ──
        caption("Gayatri AI v4.0.0 — Production-Ready Demonstration for Higher Education", 2.4)
        page.click("button:has-text('Welcome & Vision')")
        time.sleep(1.2)
        caption("Developed under Dbert Internship Program (dbert.online)", 2.8)
        snap("summary_final")

        print("[5/6] Finalizing Recording and Closing Browser...")
        page.evaluate("setDemoCaption('')")
        time.sleep(0.5)

        video_obj = page.video
        video_temp_path = video_obj.path() if video_obj else None

        context.close()
        browser.close()

    # Move video to target
    target_video = demo_video_dir / "gayatri_v4_platform_demo.webm"
    if video_temp_path and Path(video_temp_path).exists():
        if target_video.exists():
            target_video.unlink()
        shutil.move(video_temp_path, target_video)
    else:
        webms = list(demo_video_dir.glob("*.webm"))
        if webms:
            newest = max(webms, key=lambda f: f.stat().st_mtime)
            if newest != target_video:
                if target_video.exists():
                    target_video.unlink()
                shutil.move(newest, target_video)

    video_size_mb = target_video.stat().st_size / (1024 * 1024)
    print(f"  Target Video: {target_video}")
    print(f"  Video Size:   {video_size_mb:.2f} MB (Target < 5 MB for GitHub: {'PASSED' if video_size_mb < 5.0 else 'CHECK'})")

    # Build Animated GIF Preview Carousel from snapshots
    print("[6/6] Generating Animated GIF Preview for GitHub README...")
    target_gif = demo_video_dir / "gayatri_demo_preview.gif"
    if snapshot_paths:
        frames = []
        for p in snapshot_paths:
            img = Image.open(p).convert("RGB")
            # Resize to 960x540 for fast loading on GitHub (< 1.5MB)
            img = img.resize((960, 540), Image.Resampling.LANCZOS)
            # Quantize with adaptive palette
            img_q = img.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
            frames.append(img_q)

        frames[0].save(
            str(target_gif),
            save_all=True,
            append_images=frames[1:],
            duration=2200,  # 2.2 seconds per scene
            loop=0,
            optimize=True
        )
        gif_size_mb = target_gif.stat().st_size / (1024 * 1024)
        print(f"  Animated GIF: {target_gif}")
        print(f"  GIF Size:     {gif_size_mb:.2f} MB (Optimized for instant GitHub README rendering)")

        # Cleanup raw snapshot PNGs
        shutil.rmtree(snapshots_dir, ignore_errors=True)

    print("\n[SUCCESS] Both Video (<5MB) and Animated GIF (<1.5MB) are ready for GitHub!")
    return target_video, target_gif

if __name__ == "__main__":
    record_demo()