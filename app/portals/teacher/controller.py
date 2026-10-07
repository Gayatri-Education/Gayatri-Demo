"""Gayatri AI Platform — Teacher Portal Controller (Phase 7 Preview)."""
from __future__ import annotations

from typing import Any, Dict, List
from central_platform.courses.service import CourseService
from central_platform.learning.state import LearningStateManager

class TeacherPortalController:
    """Provides class-level aggregated metrics, misconception alerts, and intervention queue."""

    def __init__(self, course_service: CourseService, state_manager: LearningStateManager) -> None:
        self.course_service = course_service
        self.state_manager = state_manager

    def get_cohort_summary(self, course_id: str = "crs_engg_math") -> Dict[str, Any]:
        """Returns synthetic class cohort health and performance breakdown."""
        course = self.course_service.get_course(course_id)
        title = course.title if course else "Course"

        # Synthetic demonstration cohort for faculty presentation
        synthetic_students = [
            {"id": "std_01", "name": "Aarav Sharma", "mastery": 0.82, "weak_area": "Laplace Derivatives", "status": "On Track"},
            {"id": "std_02", "name": "Diya Patel", "mastery": 0.64, "weak_area": "Inversion Laws", "status": "Needs Review"},
            {"id": "std_03", "name": "Rohan Iyer", "mastery": 0.91, "weak_area": "None", "status": "Excelling"},
            {"id": "std_04", "name": "Ananya Reddy", "mastery": 0.58, "weak_area": "Integrating Factors", "status": "Intervention Recommended"}
        ]

        avg_mastery = round(sum(s["mastery"] for s in synthetic_students) / len(synthetic_students), 3)

        return {
            "course_id": course_id,
            "course_title": title,
            "enrolled_count": 42,
            "active_now": 4,
            "average_mastery": avg_mastery,
            "cohort_gap": "Inversion Laws and Integration Boundaries",
            "students": synthetic_students,
            "alerts": [
                {
                    "severity": "medium",
                    "topic": "NAND/NOR Duality",
                    "affected_percentage": 28.5,
                    "action": "Assign 10-minute targeted review on universal gate duality before next lab session."
                }
            ],
            "is_preview": True
        }