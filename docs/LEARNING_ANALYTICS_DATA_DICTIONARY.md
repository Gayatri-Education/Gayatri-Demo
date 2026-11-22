# Learning Analytics Data Dictionary

This note explains how the learner progress values returned by `LearningStateManager` are stored and updated. It helps analysts interpret the dashboard without treating heuristic progress values as formal assessment results.

## Data grain and storage

- A mastery record is keyed by `student_id` and `course_id`.
- Learning events are stored separately and keyed by event `id`.
- Replaying an event with an ID already stored does not apply its mastery update again.
- A topic is identified by `topic_id`; if absent, the event's `module_id` is used. If both are absent, updates use `Fundamentals`.

## Fields

| Field | Meaning |
|---|---|
| `overall_mastery` | A bounded heuristic progress score for one learner and course. It is initialized to 0.45 when no saved record exists and changes in 0.05 steps. |
| `topic_mastery` | A map from topic/module identifier to a bounded heuristic score. A previously unseen topic starts at 0.50. |
| `weak_topics` | Topics flagged for review after a misconception, or after an incorrect answer lowers the topic score below 0.45. A topic is removed after a correct answer raises its score to at least 0.50. |
| `recent_misconceptions` | A de-duplicated, ordered list of recent misconception labels, capped at five entries. A correct answer removes the oldest entry. |
| `recommended_next_action` | A guidance label derived from the most recently recorded event; it is not an independently measured outcome. |

## Update rules

1. If a misconception is present, overall mastery and the affected topic score each decrease by 0.05. The topic is flagged as weak and the action becomes `Remediate: <misconception>`.
2. Otherwise, a correct answer increases both scores by 0.05. The action becomes `Advance to Next Topic` when overall mastery reaches 0.70; otherwise it is `Continue guided practice`.
3. Otherwise, an incorrect answer decreases both scores by 0.05. The topic is flagged as weak if its resulting score is below 0.45, and the action becomes `Review: <topic>`.
4. If correctness is unknown, scores do not change and the action is `Continue guided practice`.

Both score types are clamped to 0.10–1.00. When an event contains both a misconception and a correctness value, the misconception rule takes precedence.

## Interpretation and limitations

- These values are rule-based progress indicators. They are **not** calibrated probabilities, exam marks, grades, or validated measures of learning.
- The 0.45 overall and 0.50 `Fundamentals` starting values are defaults returned when no saved mastery record exists; they do not represent observed learner performance.
- A 0.05 step is a product rule, not an estimate of statistical confidence or effect size.
- The dashboard exposes an individual learner/course state. Do not infer cohort performance, causal effects, or between-learner rankings from these fields alone.
- For analysis, retain event-level data and report the number of learners, courses, and evaluated events alongside any aggregate. Separate ungraded events from correct/incorrect outcomes.

## Source of truth

Update this note when behavior changes in `central_platform/learning/state.py` or the field schema in `central_platform/models/schema.py`.
