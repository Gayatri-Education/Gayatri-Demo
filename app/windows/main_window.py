"""Gayatri AI Platform — Frameless Main Window with WebEngine & WebChannel."""
from __future__ import annotations

import sys
from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow

from app.bridge.facade import BridgeFacade
from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager
from central_platform.rag.service import RAGService
from central_platform.tutor.orchestrator import TutorOrchestrator
from core.config import BASE_DIR, WINDOW_HEIGHT, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_TITLE, WINDOW_WIDTH

class SecureWebPage(QWebEnginePage):
    """Enforces navigation boundary: local and loopback assets only."""
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        scheme = url.scheme()
        if scheme in ("file", "qrc", "data"):
            return True
        if scheme in ("http", "https") and url.host() in ("127.0.0.1", "localhost"):
            return True
        return False

class MainWindow(QMainWindow):
    """Frameless modern window hosting the Gayatri UI."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        # Set App Icon
        icon_path = BASE_DIR / "gai3.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Initialize Services
        self.course_service = CourseService()
        self.rag_service = RAGService()
        self.state_manager = LearningStateManager()
        self.orchestrator = TutorOrchestrator(self.course_service, self.rag_service, self.state_manager)

        # Setup WebEngine & Secure Page
        self.web_view = QWebEngineView()
        self.web_page = SecureWebPage()
        self.web_page.setBackgroundColor(QColor("#0f0f23"))
        self.web_view.setPage(self.web_page)
        self.setCentralWidget(self.web_view)

        # Setup WebChannel and Bridge
        self.channel = QWebChannel()
        self.bridge = BridgeFacade(
            course_service=self.course_service,
            rag_service=self.rag_service,
            orchestrator=self.orchestrator,
            state_manager=self.state_manager,
            window=self
        )
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # Load UI
        ui_file = BASE_DIR / "app" / "ui" / "index.html"
        self.web_view.load(QUrl.fromLocalFile(str(ui_file)))

        # Drag Window Support
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()