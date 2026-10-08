"""Gayatri AI Platform — Automated High-Definition Captioned Demonstration Video Recorder.

Uses Playwright to choreograph a guided walkthrough across the platform:
1. Welcome & Vision (Institutional Architecture & Positioning)
2. Multi-Course Catalog (Engineering Mathematics & Digital Electronics)
3. Socratic AI Tutor with Live Grounded RAG & Evidence Drawer
4. Dynamic Course Switch & Socratic Misconception Remediation (NAND Logic Error)
5. Student Mastery Cognitive State Tracking
6. Teacher Copilot Preview & Cohort Health Alerts
7. Bring Your Curriculum Sandbox (Dynamic Ingestion)
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

# Ensure demo directory is at root of sys.path
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

    ui_path = PROJECT_ROOT / "app" / "ui" / "index.html"
    ui_url = ui_path.as_uri()

    print(f"[2/6] Launching Playwright Chromium (1920x1080 Full HD)...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--start-maximized"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(demo_video_dir),
            record_video_size={"width": 1920, "height": 1080}
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
        def caption(text: str, wait_s: float = 3.0):
            print(f"  [CAPTION] {text}")
            page.evaluate(f"setDemoCaption({json.dumps(text)})")
            time.sleep(wait_s)

        def type_prompt(selector: str, text: str, delay_ms: int = 35):
            page.click(selector)
            for char in text:
                page.keyboard.type(char)
                time.sleep(delay_ms / 1000.0)
            time.sleep(0.4)

        print("[4/6] Executing Choreographed Walkthrough Scenes...")

        # ── SCENE 1: Welcome & Vision ──
        caption("Gayatri AI (v4.0.0) — Developed under Dbert Internship Program (dbert.online)", 3.5)
        caption("Course-Independent Socratic Tutoring Grounded in Institution Knowledge", 3.0)
        caption("100% Offline Air-Gapped Operation with Zero Cloud Data Egress", 3.0)
        page.mouse.move(500, 350)
        time.sleep(0.8)
        page.mouse.move(900, 350)
        time.sleep(0.8)

        # ── SCENE 2: Multi-Course Catalog ──
        caption("Multi-Course Catalog: Engineering Mathematics & Digital Electronics", 2.5)
        page.click("button:has-text('Course Catalog')")
        time.sleep(1.5)
        page.mouse.move(450, 280)
        time.sleep(0.8)
        page.mouse.move(850, 280)
        time.sleep(0.8)
        caption("Selecting Active Course Context: Engineering Mathematics (MATH201)", 2.5)
        page.click("div.course-card:has-text('MATH201') button")
        time.sleep(1.5)

        # ── SCENE 3: Socratic AI Tutor & Math Query ──
        caption("Socratic AI Tutor: Strictly Scoped Grounded RAG with Zero Cross-Contamination", 3.0)
        page.click("button:has-text('Socratic AI Tutor')")
        time.sleep(1.5)

        caption("Student Query: Inquiring about First-Order ODEs and Integrating Factors", 2.0)
        type_prompt("#chatInput", "Explain first-order differential equations and integrating factor", 30)
        page.click("#chatSendBtn")
        time.sleep(2.0)

        caption("Retrieved Evidence Drawer: Real-time Grounding Cards & Textbook Citations", 3.5)
        page.mouse.move(1700, 300)
        time.sleep(1.0)
        page.mouse.move(1700, 500)
        time.sleep(1.5)

        # ── SCENE 4: Dynamic Course Switch & Misconception Remediation ──
        caption("Dynamic Course Switching: Switching to Digital Electronics (EC202)", 2.5)
        page.click("button:has-text('Course Catalog')")
        time.sleep(1.5)
        page.click("div.course-card:has-text('EC202') button")
        time.sleep(1.5)

        caption("Active Context Switched: Prior Context Flushed with Zero RAG Bleed", 2.5)
        caption("Misconception Diagnosis: Testing Student Logic Inversion on NAND Gates", 2.5)
        type_prompt("#chatInput", "For a NAND gate, the output is 0 when any input is 0", 30)
        page.click("#chatSendBtn")
        time.sleep(2.5)

        caption("Misconception Identified: NAND/NOR Logic Inversion Error Remediation", 3.5)
        page.mouse.move(800, 550)
        time.sleep(1.5)

        # ── SCENE 5: Student Mastery Tracking ──
        caption("Student Mastery: Tracking Cognitive States & Detected Misconceptions", 2.5)
        page.click("button:has-text('Student Mastery')")
        time.sleep(2.0)
        page.mouse.move(700, 180)
        time.sleep(1.0)
        page.mouse.move(1200, 180)
        time.sleep(1.5)

        # ── SCENE 6: Teacher Copilot Preview ──
        caption("Teacher Copilot: Cohort Analytics, Gap Heatmaps & Intervention Queue", 3.0)
        page.click("button:has-text('Teacher Copilot')")
        time.sleep(2.0)
        page.mouse.move(800, 380)
        time.sleep(1.5)

        # ── SCENE 7: Bring Your Curriculum Sandbox ──
        caption("Bring Your Curriculum: Instant Ingestion of Institution Notes into Air-Gapped RAG", 3.0)
        page.click("button:has-text('Bring Curriculum')")
        time.sleep(1.5)
        page.click("button:has-text('Load Sample Curriculum Document')")
        time.sleep(1.5)
        caption("Custom Curriculum Ingestion Succeeded: 3 Knowledge Chunks Indexed", 2.5)
        time.sleep(1.0)

        # ── SCENE 8: Wrap-up & Platform Governance ──
        caption("Gayatri AI v4.0.0 — Production-Ready Demonstration for Higher Education", 3.0)
        page.click("button:has-text('Welcome & Vision')")
        time.sleep(2.0)
        caption("Developed under Dbert Internship Program (dbert.online)", 3.5)
        time.sleep(1.0)

        print("[5/6] Finalizing Recording and Closing Browser...")
        page.evaluate("setDemoCaption('')")
        time.sleep(0.5)

        # Retrieve video path before closing context
        video_obj = page.video
        video_temp_path = video_obj.path() if video_obj else None

        context.close()
        browser.close()

    target_video = demo_video_dir / "gayatri_v4_platform_demo.webm"
    if video_temp_path and Path(video_temp_path).exists():
        if target_video.exists():
            target_video.unlink()
        shutil.move(video_temp_path, target_video)
        size_mb = target_video.stat().st_size / (1024 * 1024)
        print(f"[6/6] Demonstration Video Successfully Recorded!")
        print(f"  Target File: {target_video}")
        print(f"  File Size:   {size_mb:.2f} MB")
        return target_video
    else:
        # Check any webm in demo_video_dir
        webms = list(demo_video_dir.glob("*.webm"))
        if webms:
            newest = max(webms, key=lambda f: f.stat().st_mtime)
            if newest != target_video:
                if target_video.exists():
                    target_video.unlink()
                shutil.move(newest, target_video)
            size_mb = target_video.stat().st_size / (1024 * 1024)
            print(f"[6/6] Demonstration Video Successfully Recorded!")
            print(f"  Target File: {target_video}")
            print(f"  File Size:   {size_mb:.2f} MB")
            return target_video
        else:
            raise RuntimeError("No video file found in demo_video directory!")

if __name__ == "__main__":
    record_demo()