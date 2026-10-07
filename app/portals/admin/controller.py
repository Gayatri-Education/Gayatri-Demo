"""Gayatri AI Platform — Institution Admin Controller (Phase 7 Preview)."""
from __future__ import annotations

from typing import Any, Dict, List
from central_platform.courses.service import CourseService
from central_platform.rag.service import RAGService
from core.config import APP_VERSION, LOOPBACK_HOST

class AdminPortalController:
    """Provides institutional governance, course catalog status, and knowledge indexing overview."""

    def __init__(self, course_service: CourseService, rag_service: RAGService) -> None:
        self.course_service = course_service
        self.rag_service = rag_service

    def get_system_topology(self) -> Dict[str, Any]:
        courses = self.course_service.list_courses(include_optional=True)
        catalog_summary = []
        total_cards = 0

        for c in courses:
            card_count = self.rag_service.get_course_chunk_count(c.id)
            total_cards += card_count
            catalog_summary.append({
                "code": c.code,
                "title": c.title,
                "modules": len(c.modules),
                "indexed_cards": card_count,
                "status": "Active" if c.is_active else "Inactive",
                "is_optional": c.is_optional
            })

        return {
            "app_version": APP_VERSION,
            "deployment_mode": "Offline Air-Gapped",
            "binding": f"{LOOPBACK_HOST} (Strict Loopback Only)",
            "outbound_egress": "0.0 KB/s (Prohibited)",
            "total_courses": len(courses),
            "total_indexed_cards": total_cards,
            "courses": catalog_summary,
            "is_preview": True
        }