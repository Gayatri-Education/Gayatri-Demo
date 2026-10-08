"""Gayatri AI Platform — Learning State Manager with SQLite Persistence."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from central_platform.models.schema import LearningEvent, MasteryState
from core.config import DATA_DIR

class LearningStateManager:
    """Tracks learner cognitive state, topic mastery, and learning trajectory."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or (DATA_DIR / "learner_state.sqlite")
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mastery (
                    student_id TEXT,
                    course_id TEXT,
                    overall_mastery REAL,
                    topic_mastery TEXT,
                    weak_topics TEXT,
                    recent_misconceptions TEXT,
                    recommended_action TEXT,
                    PRIMARY KEY(student_id, course_id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_events (
                    id TEXT PRIMARY KEY,
                    student_id TEXT,
                    course_id TEXT,
                    module_id TEXT,
                    prompt TEXT,
                    response TEXT,
                    action TEXT,
                    misconception TEXT,
                    timestamp TEXT
                )
            """)
            conn.commit()

    def get_mastery(self, student_id: str, course_id: str) -> MasteryState:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT overall_mastery, topic_mastery, weak_topics, recent_misconceptions, recommended_action FROM mastery WHERE student_id = ? AND course_id = ?",
                (student_id, course_id)
            )
            row = cursor.fetchone()
            if row:
                return MasteryState(
                    student_id=student_id,
                    course_id=course_id,
                    overall_mastery=row[0],
                    topic_mastery=json.loads(row[1]),
                    weak_topics=json.loads(row[2]),
                    recent_misconceptions=json.loads(row[3]),
                    recommended_next_action=row[4]
                )
            # Default initial state
            return MasteryState(
                student_id=student_id,
                course_id=course_id,
                overall_mastery=0.45,
                topic_mastery={"Fundamentals": 0.50},
                weak_topics=[],
                recent_misconceptions=[],
                recommended_next_action="Explore Core Concepts"
            )

    def record_event(self, event: LearningEvent) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO learning_events 
                (id, student_id, course_id, module_id, prompt, response, action, misconception, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id, event.student_id, event.course_id, event.module_id,
                event.prompt, event.response, event.action.value, event.misconception, event.timestamp
            ))

            # Update mastery state dynamically
            current = self.get_mastery(event.student_id, event.course_id)
            if event.misconception:
                if event.misconception not in current.recent_misconceptions:
                    current.recent_misconceptions.append(event.misconception)
                current.overall_mastery = max(0.1, round(current.overall_mastery - 0.05, 2))
                current.recommended_next_action = f"Remediate: {event.misconception}"
            elif event.correctness is True:
                current.overall_mastery = min(1.0, round(current.overall_mastery + 0.05, 2))
                current.recommended_next_action = "Advance to Next Topic"
            elif event.correctness is False:
                current.overall_mastery = max(0.1, round(current.overall_mastery - 0.05, 2))
                current.recommended_next_action = "Review the current topic"
            else:
                # Asking a question or submitting an ungraded response is not
                # evidence of learning. Keep mastery unchanged until an answer
                # has actually been evaluated.
                current.recommended_next_action = "Continue guided practice"

            cursor.execute("""
                INSERT OR REPLACE INTO mastery 
                (student_id, course_id, overall_mastery, topic_mastery, weak_topics, recent_misconceptions, recommended_action)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                current.student_id, current.course_id, current.overall_mastery,
                json.dumps(current.topic_mastery), json.dumps(current.weak_topics),
                json.dumps(current.recent_misconceptions), current.recommended_next_action
            ))
            conn.commit()
