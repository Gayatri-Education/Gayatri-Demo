"""Gayatri AI Platform — Automated Institution & Organization Demo Video Recorder.

Produces:
1. demo_video/gayatri_institution_demo.webm (< 5 MB, 1280x720 HD, captioned)
2. demo_video/gayatri_institution_preview.gif (~1 MB animated GIF preview)
"""
from __future__ import annotations

import json
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

def record_institution_demo():
    print("[1/6] Initializing Backend Services for Institution Demo...")
    course_service = CourseService()
    rag_service = RAGService()
    state_manager = LearningStateManager()
    orchestrator = TutorOrchestrator(course_service, rag_service, state_manager)

    demo_video_dir = PROJECT_ROOT / "demo_video"
    demo_video_dir.mkdir(parents=True, exist_ok=True)

    snapshots_dir = demo_video_dir / "snapshots_institution"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    snapshot_paths = []

    ui_path = PROJECT_ROOT / "app" / "ui" / "index.html"
    ui_url = ui_path.as_uri()

    print("[2/6] Launching Playwright Chromium (1280x720 HD)...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(demo_video_dir),
            record_video_size={"width": 1280, "height": 720}
        )

        page = context.new_page()

        # Expose backend functions
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

        print("[3/6] Navigating to Platform Interface...")
        page.goto(ui_url)
        page.wait_for_load_state("networkidle")
        time.sleep(1.0)

        def caption(text: str, wait_s: float = 2.5):
            print(f"  [CAPTION] {text}")
            page.evaluate(f"setDemoCaption({json.dumps(text)})")
            time.sleep(wait_s)

        def snap(name: str):
            p = snapshots_dir / f"{len(snapshot_paths)+1:02d}_{name}.png"
            page.screenshot(path=str(p))
            snapshot_paths.append(p)

        print("[4/6] Executing Institution, School & Organization Walkthrough...")

        # ── SCENE 1: Institutional Intro ──
        caption("🏛️ Gayatri Institutional Governance — Air-Gapped Adaptive Learning", 2.8)
        caption("Developed under Dbert Internship Program (dbert.online)", 2.4)
        caption("Engineered for Higher Education, School Networks & Large Organizations", 2.4)
        snap("institution_intro")

        # ── SCENE 2: Institution Admin & Topology ──
        caption("Navigating to Institution Administration & Governance Portal", 2.0)
        page.click("button:has-text('Institution Admin')")
        time.sleep(1.5)
        snap("institution_admin_dashboard")

        caption("Deployment Topology: 100% Offline Air-Gapped with Loopback (127.0.0.1) Only", 2.8)
        page.mouse.move(600, 240)
        time.sleep(1.0)

        caption("Data Sovereignty: Absolute Zero External Telemetry and Zero Cloud Egress", 2.6)
        page.mouse.move(850, 180)
        time.sleep(1.0)

        # ── SCENE 3: Registered Course Repositories & Isolation ──
        caption("Multi-Course Catalog Oversight: Mathematics, Electronics & Science", 2.6)
        page.mouse.move(600, 420)
        time.sleep(1.5)
        snap("course_repositories_table")
        caption("Strict Boundary Enforcement: Zero Cross-Department Knowledge Contamination", 2.6)

        # ── SCENE 4: Security & Regulatory Compliance ──
        caption("Compliance Posture: Microsoft Defender Verified PE Executables (No UPX)", 2.8)
        page.mouse.move(1100, 180)
        time.sleep(1.2)
        snap("compliance_security")

        # ── SCENE 5: Multi-Department Course Catalog ──
        caption("Departmental Curriculum Hierarchy: Inspecting Modular Course Structures", 2.4)
        page.click("button:has-text('Course Catalog')")
        time.sleep(1.5)
        snap("department_catalog")
        page.mouse.move(450, 300)
        time.sleep(0.8)
        page.mouse.move(850, 300)
        time.sleep(0.8)

        # ── SCENE 6: Bring Your Curriculum (Institutional Knowledge Base) ──
        caption("Institutional Knowledge Management: Ingesting Custom Handouts & Syllabi", 2.6)
        page.click("button:has-text('Bring Curriculum')")
        time.sleep(1.2)
        snap("curriculum_sandbox_institution")
        page.click("button:has-text('Load Sample Curriculum Document')")
        time.sleep(1.5)
        caption("Enterprise Ingestion Complete: Atomic Grounding Cards Indexed in Local SQLite", 2.6)

        # ── SCENE 7: Dual-Role Visibility (Faculty & Student Insights) ──
        caption("Multi-Role Visibility: Faculty Cohort Analytics & Real-Time Student Triage", 2.5)
        page.click("button:has-text('Teacher Copilot')")
        time.sleep(1.5)
        snap("faculty_visibility")

        caption("Student Mastery: Transparent Trajectory Tracking with Zero Model Hallucination", 2.5)
        page.click("button:has-text('Student Mastery')")
        time.sleep(1.5)
        snap("student_trajectory_institution")

        # ── SCENE 8: Executive Wrap-Up ──
        caption("Gayatri AI (v4.0.0) Institutional Release — Production-Ready & Air-Gapped", 2.8)
        page.click("button:has-text('Welcome & Vision')")
        time.sleep(1.2)
        caption("Developed under Dbert Internship Program (dbert.online)", 3.0)
        snap("institution_final_summary")

        print("[5/6] Finalizing Recording and Closing Browser...")
        page.evaluate("setDemoCaption('')")
        time.sleep(0.5)

        video_obj = page.video
        video_temp_path = video_obj.path() if video_obj else None

        context.close()
        browser.close()

    target_video = demo_video_dir / "gayatri_institution_demo.webm"
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
    print(f"  Institution Video: {target_video}")
    print(f"  Video Size:        {video_size_mb:.2f} MB")

    print("[6/6] Generating Institution Animated GIF Preview...")
    target_gif = demo_video_dir / "gayatri_institution_preview.gif"
    if snapshot_paths:
        frames = []
        for p in snapshot_paths:
            img = Image.open(p).convert("RGB")
            img = img.resize((960, 540), Image.Resampling.LANCZOS)
            img_q = img.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
            frames.append(img_q)

        frames[0].save(
            str(target_gif),
            save_all=True,
            append_images=frames[1:],
            duration=2200,
            loop=0,
            optimize=True
        )
        gif_size_mb = target_gif.stat().st_size / (1024 * 1024)
        print(f"  Institution GIF:   {target_gif}")
        print(f"  GIF Size:          {gif_size_mb:.2f} MB")
        shutil.rmtree(snapshots_dir, ignore_errors=True)

    print("\n[SUCCESS] Institution Demo Video & Preview GIF Produced!")
    return target_video, target_gif

if __name__ == "__main__":
    record_institution_demo()