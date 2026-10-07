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
    """Verifies runtime dependencies and configuration headlessly."""
    try:
        import PySide6.QtWidgets
        import PySide6.QtWebEngineWidgets
        import pydantic
        from central_platform.courses.service import CourseService
        from central_platform.rag.service import RAGService
        
        cs = CourseService()
        rag = RAGService()
        assert len(cs.list_courses()) >= 2
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