"""Unit tests verifying Teacher and Admin portal controllers."""
import pytest
from app.portals.teacher.controller import TeacherPortalController
from app.portals.admin.controller import AdminPortalController
from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager
from central_platform.rag.service import RAGService

def test_teacher_portal_controller(tmp_path):
    cs = CourseService()
    sm = LearningStateManager(tmp_path / "test_teacher.sqlite")
    ctrl = TeacherPortalController(cs, sm)

    summary = ctrl.get_cohort_summary("crs_engg_math")
    assert summary["is_preview"] is True
    assert summary["course_id"] == "crs_engg_math"
    assert summary["enrolled_count"] == 42
    assert len(summary["students"]) > 0
    assert len(summary["alerts"]) > 0
    assert "average_mastery" in summary

def test_admin_portal_controller():
    cs = CourseService()
    rag = RAGService()
    ctrl = AdminPortalController(cs, rag)

    topo = ctrl.get_system_topology()
    assert topo["is_preview"] is True
    assert topo["app_version"] == "4.0.0"
    assert topo["deployment_mode"] == "Offline Air-Gapped"
    assert "127.0.0.1" in topo["binding"]
    assert topo["total_courses"] >= 2
    assert topo["total_indexed_cards"] >= 8