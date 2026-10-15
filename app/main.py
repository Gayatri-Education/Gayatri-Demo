"""Gayatri AI Platform — Application Main Entry Point."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure demo directory is at root of sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import APP_NAME, APP_VERSION, WINDOW_TITLE
from core.logging_setup import setup_logging

logger = setup_logging()

def check_startup() -> bool:
    """Verifies runtime dependencies, platform policy, and configuration headlessly."""
    try:
        # 1. Python version verification
        if sys.version_info < (3, 10):
            sys.stderr.write(
                f"Startup check failed: Python {sys.version_info.major}.{sys.version_info.minor} is unsupported. "
                "Gayatri AI requires Python 3.10 or higher for source execution.\n"
            )
            return False

        # 2. Operating system warning
        if sys.platform == "win32":
            try:
                win_ver = sys.getwindowsversion()
                if win_ver.major < 10:
                    logger.warning(
                        "Unsupported legacy OS detected: Windows %s.%s. "
                        "Official support requires Windows 10 or Windows 11 (64-bit). "
                        "Running on Windows 7/8 may cause Chromium deprecation warnings and rendering issues.",
                        win_ver.major, win_ver.minor
                    )
            except Exception:
                pass

        # 3. Core dependencies and platform services
        import PySide6.QtWidgets
        import PySide6.QtWebEngineWidgets
        import pydantic
        from central_platform.courses.service import CourseService
        from central_platform.learning.state import LearningStateManager
        from central_platform.rag.service import RAGService
        from central_platform.tutor.orchestrator import TutorOrchestrator
        
        cs = CourseService()
        rag = RAGService()
        sm = LearningStateManager()
        orch = TutorOrchestrator(cs, rag, sm)

        assert len(cs.list_courses()) >= 2
        assert orch is not None
        return True
    except Exception as exc:
        sys.stderr.write(f"Startup check failed: {exc}\n")
        return False

def main() -> None:
    # CLI Flags
    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"Gayatri AI v{APP_VERSION}")
        sys.exit(0)

    if "--check-startup" in sys.argv:
        if check_startup():
            print("[OK] Gayatri AI startup verification passed.")
            sys.exit(0)
        else:
            print("[ERROR] Startup verification failed.")
            sys.exit(1)

    # Windows AppUserModelID
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("gayatri.adaptive.learning.platform.v4")
        except Exception:
            pass

    from PySide6.QtWidgets import QApplication
    from app.windows.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(WINDOW_TITLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()