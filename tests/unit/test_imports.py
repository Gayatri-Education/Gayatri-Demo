"""Unit test verifying clean decoupled platform subsystem imports."""

def test_subsystem_imports():
    from core.config import APP_NAME, APP_VERSION
    assert APP_NAME == "Gayatri AI"
    assert APP_VERSION == "4.0.1"

    from central_platform.courses.service import CourseService
    from central_platform.learning.state import LearningStateManager
    from central_platform.rag.service import RAGService
    from central_platform.tutor.orchestrator import TutorOrchestrator

    cs = CourseService()
    rag = RAGService()
    sm = LearningStateManager()
    orch = TutorOrchestrator(cs, rag, sm)

    assert orch is not None
