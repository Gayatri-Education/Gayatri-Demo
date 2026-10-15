"""Gayatri AI Platform — Learning State Manager with SQLite Persistence."""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from central_platform.models.schema import LearningEvent, MasteryState
from core.config import DATA_DIR

logger = logging.getLogger("gayatri.central_platform.learning")


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
                    topic_id TEXT,
                    prompt TEXT,
                    response TEXT,
                    action TEXT,
                    misconception TEXT,
                    correctness INTEGER,
                    timestamp TEXT
                )
            """)

            # Migration: ensure topic_id and correctness exist in older databases
            cursor.execute("PRAGMA table_info(learning_events)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            if "topic_id" not in existing_cols:
                cursor.execute("ALTER TABLE learning_events ADD COLUMN topic_id TEXT")
            if "correctness" not in existing_cols:
                cursor.execute("ALTER TABLE learning_events ADD COLUMN correctness INTEGER")

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
                    topic_mastery=json.loads(row[1]) if row[1] else {},
                    weak_topics=json.loads(row[2]) if row[2] else [],
                    recent_misconceptions=json.loads(row[3]) if row[3] else [],
                    recommended_next_action=row[4] or "Continue guided practice"
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

            # Deduplication: exactly-once semantics for repeated event IDs
            cursor.execute("SELECT id FROM learning_events WHERE id = ?", (event.id,))
            if cursor.fetchone() is not None:
                logger.info("Event %s already recorded; skipping mastery re-application.", event.id)
                return

            correctness_val = 1 if event.correctness is True else (0 if event.correctness is False else None)
            topic_val = getattr(event, "topic_id", None) or event.module_id

            cursor.execute("""
                INSERT INTO learning_events 
                (id, student_id, course_id, module_id, topic_id, prompt, response, action, misconception, correctness, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id, event.student_id, event.course_id, event.module_id, topic_val,
                event.prompt, event.response, event.action.value, event.misconception, correctness_val, event.timestamp
            ))

            # Update mastery state dynamically
            current = self.get_mastery(event.student_id, event.course_id)
            topic_key = topic_val or "Fundamentals"

            if event.misconception:
                if event.misconception not in current.recent_misconceptions:
                    current.recent_misconceptions.append(event.misconception)
                # Bounded recent history (max 5)
                current.recent_misconceptions = current.recent_misconceptions[-5:]
                current.overall_mastery = max(0.1, round(current.overall_mastery - 0.05, 2))

                # Update topic mastery & weak topics
                t_score = current.topic_mastery.get(topic_key, 0.50)
                current.topic_mastery[topic_key] = max(0.1, round(t_score - 0.05, 2))
                if topic_key not in current.weak_topics:
                    current.weak_topics.append(topic_key)

                current.recommended_next_action = f"Remediate: {event.misconception}"

            elif event.correctness is True:
                current.overall_mastery = min(1.0, round(current.overall_mastery + 0.05, 2))

                # Update topic mastery
                t_score = current.topic_mastery.get(topic_key, 0.50)
                new_t_score = min(1.0, round(t_score + 0.05, 2))
                current.topic_mastery[topic_key] = new_t_score

                # Remediation recovery: remove from weak_topics if score recovers >= 0.50
                if new_t_score >= 0.50 and topic_key in current.weak_topics:
                    current.weak_topics.remove(topic_key)

                # Remediation decay: remove oldest misconception
                if current.recent_misconceptions:
                    current.recent_misconceptions.pop(0)

                current.recommended_next_action = "Advance to Next Topic" if current.overall_mastery >= 0.70 else "Continue guided practice"

            elif event.correctness is False:
                current.overall_mastery = max(0.1, round(current.overall_mastery - 0.05, 2))

                # Update topic mastery
                t_score = current.topic_mastery.get(topic_key, 0.50)
                new_t_score = max(0.1, round(t_score - 0.05, 2))
                current.topic_mastery[topic_key] = new_t_score

                if new_t_score < 0.45 and topic_key not in current.weak_topics:
                    current.weak_topics.append(topic_key)

                current.recommended_next_action = f"Review: {topic_key}"

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
