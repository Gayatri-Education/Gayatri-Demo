"""Gayatri AI Platform — Automated Teacher & Faculty Demonstration Video Recorder.

Produces:
1. demo_video/gayatri_teacher_demo.webm (< 5 MB, 1280x720 HD, captioned)
2. demo_video/gayatri_teacher_preview.gif (~1 MB animated GIF preview)
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

def record_teacher_demo():
    print("[1/6] Initializing Backend Services for Teacher Demo...")
    course_service = CourseService()
    rag_service = RAGService()
    state_manager = LearningStateManager()
    orchestrator = TutorOrchestrator(course_service, rag_service, state_manager)

    demo_video_dir = PROJECT_ROOT / "demo_video"
    demo_video_dir.mkdir(parents=True, exist_ok=True)

    snapshots_dir = demo_video_dir / "snapshots_teacher"
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

        def type_prompt(selector: str, text: str, delay_ms: int = 30):
            page.click(selector)
            for char in text:
                page.keyboard.type(char)
                time.sleep(delay_ms / 1000.0)
            time.sleep(0.3)

        print("[4/6] Executing Teacher & Faculty Walkthrough Scenes...")

        # ── SCENE 1: Intro for Educators ──
        caption("👩‍🏫 Gayatri Teacher Copilot — Classroom Intelligence & Cohort Analytics", 2.8)
        caption("Developed under Dbert Internship Program (dbert.online)", 2.4)
        snap("teacher_intro")

        # ── SCENE 2: Teacher Copilot Dashboard ──
        caption("Navigating to Teacher Copilot & Cohort Health Dashboard", 2.0)
        page.click("button:has-text('Teacher Copilot')")
        time.sleep(1.5)
        snap("teacher_dashboard")

        caption("Real-Time Cohort Metrics: 42 Students, 74.2% Mastery, 3 Interventions Needed", 2.6)
        page.mouse.move(300, 240)
        time.sleep(0.8)
        page.mouse.move(600, 240)
        time.sleep(0.8)

        # ── SCENE 3: Cohort Misconception Alert ──
        caption("Cohort Misconception Alert: 28% Struggling with Logic Gate Duality", 2.8)
        page.mouse.move(600, 340)
        time.sleep(1.5)
        snap("cohort_alert")

        # ── SCENE 4: Student Intervention Queue ──
        caption("Student Intervention Queue: Triaging Struggling Learners Before Exams", 2.8)
        page.mouse.move(600, 480)
        time.sleep(1.5)
        snap("intervention_queue")

        # ── SCENE 5: Socratic Pedagogy In Action (Anti-Cheating Oversight) ──
        caption("Socratic Tutor Inspection: Zero Direct Answer Spoon-Feeding Guaranteed", 2.5)
        page.click("button:has-text('Socratic AI Tutor')")
        time.sleep(1.2)
        type_prompt("#chatInput", "Just give me the formula for integrating factor dy/dx + Py = Q", 25)
        page.click("#chatSendBtn")
        time.sleep(2.0)
        caption("Pedagogical Scaffolding: AI Prompts Student Reasoning with Guided Hint", 3.0)
        snap("socratic_scaffolding")

        # ── SCENE 6: Bring Your Curriculum (Faculty Handout Ingestion) ──
        caption("Faculty Curriculum Expansion: Uploading Course Notes into Local RAG", 2.4)
        page.click("button:has-text('Bring Curriculum')")
        time.sleep(1.2)
        snap("bring_curriculum_teacher")
        page.click("button:has-text('Load Sample Curriculum Document')")
        time.sleep(1.5)
        caption("Curriculum Synchronized: Knowledge Cards Instantly Indexed for Tutoring", 2.4)

        # ── SCENE 7: Faculty Wrap-up ──
        caption("Empowering Educators with Socratic Intelligence & Continuous Diagnosis", 2.6)
        page.click("button:has-text('Teacher Copilot')")
        time.sleep(1.5)
        caption("Gayatri AI (v4.0.0) Teacher Copilot — Dbert Internship Program", 2.8)
        snap("teacher_summary")

        print("[5/6] Finalizing Recording and Closing Browser...")
        page.evaluate("setDemoCaption('')")
        time.sleep(0.5)

        video_obj = page.video
        video_temp_path = video_obj.path() if video_obj else None

        context.close()
        browser.close()

    target_video = demo_video_dir / "gayatri_teacher_demo.webm"
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
    print(f"  Teacher Video: {target_video}")
    print(f"  Video Size:    {video_size_mb:.2f} MB")

    print("[6/6] Generating Teacher Animated GIF Preview...")
    target_gif = demo_video_dir / "gayatri_teacher_preview.gif"
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
        print(f"  Teacher GIF:   {target_gif}")
        print(f"  GIF Size:      {gif_size_mb:.2f} MB")
        shutil.rmtree(snapshots_dir, ignore_errors=True)

    print("\n[SUCCESS] Teacher Demo Video & Preview GIF Produced!")
    return target_video, target_gif

if __name__ == "__main__":
    record_teacher_demo()