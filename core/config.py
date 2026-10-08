"""Gayatri AI Platform — Core Configuration (v4.0.0 Multi-Course Demo)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Paths
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("GAYATRI_DATA_DIR", BASE_DIR / "data"))
DEMO_DATA_DIR = BASE_DIR / "demo_data"
COURSES_DIR = DEMO_DATA_DIR / "courses"
COURSES_CONTAINER_FILE = DEMO_DATA_DIR / "courses.dat"
UPLOADS_DIR = DEMO_DATA_DIR / "uploads"

# Application Metadata
APP_NAME = "Gayatri AI"
APP_VERSION = "4.0.0"
WINDOW_TITLE = "Gayatri — AI-Powered Adaptive Learning Platform"

# Window Geometry
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 650

# Networking Security (Strict Loopback Only)
LOOPBACK_HOST = "127.0.0.1"
API_PORT = 8000

# RAG Configuration
RAG_TOP_K = 3
RAG_MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

# Ingestion Constraints
MAX_CHUNKS_PER_DOCUMENT = 200
DEFAULT_CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Ensure data directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
