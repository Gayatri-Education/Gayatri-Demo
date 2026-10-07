"""Gayatri AI Platform — Logging Setup."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from core.config import DATA_DIR

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configures structured, non-PII, non-secret logging."""
    log_dir = DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "gayatri_demo.log"

    logger = logging.getLogger("gayatri")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers
    if not logger.handlers:
        c_handler = logging.StreamHandler(sys.stdout)
        f_handler = logging.FileHandler(str(log_file), encoding="utf-8")

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        c_handler.setFormatter(formatter)
        f_handler.setFormatter(formatter)

        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    return logger
