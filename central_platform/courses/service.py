"""Gayatri AI Platform - Course Service."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from central_platform.models.schema import Course, Module
from core.config import COURSES_DIR

logger = logging.getLogger("gayatri.central_platform.courses")

class CourseService:
    """Manages course catalogs, module dependencies, and course switching."""

    def __init__(self, courses_dir: Optional[Path] = None) -> None:
        self.courses_dir = courses_dir or COURSES_DIR
        self._courses: Dict[str, Course] = {}
        self.reload_courses()

    def reload_courses(self) -> None:
        """Loads all courses from the course data directory."""
        self._courses.clear()
        if not self.courses_dir.exists():
            return

        for course_folder in self.courses_dir.iterdir():
            if course_folder.is_dir():
                course_file = course_folder / "course.json"
                modules_file = course_folder / "modules.json"
                if course_file.exists():
                    try:
                        with open(course_file, "r", encoding="utf-8-sig") as f:
                            data = json.load(f)
                        
                        modules: List[Module] = []
                        if modules_file.exists():
                            with open(modules_file, "r", encoding="utf-8-sig") as mf:
                                mod_data = json.load(mf)
                                modules = [Module(**m) for m in mod_data]
                        
                        course = Course(
                            id=data["id"],
                            code=data.get("code", ""),
                            title=data["title"],
                            description=data.get("description", ""),
                            modules=modules,
                            is_active=data.get("is_active", True),
                            is_optional=data.get("is_optional", False)
                        )
                        # Index by both course id and folder name
                        self._courses[course.id] = course
                        if course_folder.name != course.id:
                            self._courses[course_folder.name] = course
                    except Exception as exc:
                        logger.error("Failed to load course from %s: %s", course_folder, exc)

    def list_courses(self, include_optional: bool = True) -> List[Course]:
        """Returns unique registered courses."""
        seen = set()
        unique = []
        for c in self._courses.values():
            if c.id not in seen:
                seen.add(c.id)
                if include_optional or not c.is_optional:
                    unique.append(c)
        return sorted(unique, key=lambda c: (c.is_optional, c.code))

    def get_course(self, course_id: str) -> Optional[Course]:
        """Retrieves a single course by its ID or folder name."""
        return self._courses.get(course_id)

    def get_modules(self, course_id: str) -> List[Module]:
        """Returns all modules for a course in curriculum order."""
        course = self.get_course(course_id)
        if not course:
            return []
        return sorted(course.modules, key=lambda m: m.order)