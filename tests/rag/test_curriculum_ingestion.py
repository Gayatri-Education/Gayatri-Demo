"""RAG Bring Your Curriculum and Document Ingestion Tests."""
import pytest
from pathlib import Path
from central_platform.rag.service import RAGService
from central_platform.rag.security import RAGSecuritySanitizer

def test_custom_curriculum_document_ingestion():
    rag = RAGService()
    fixture = Path("tests/fixtures/sample_control_systems.txt")
    assert fixture.exists()

    custom_course_id = "crs_custom_control"
    ok, msg, chunk_count = rag.ingest_document(fixture, custom_course_id)
    assert ok is True
    assert chunk_count >= 2

    results = rag.query("Routh Hurwitz stability criterion", custom_course_id, top_k=2)
    assert len(results) > 0
    assert results[0].course_id == custom_course_id
    assert "routh" in results[0].content.lower()

def test_ingestion_security_rejection(tmp_path):
    # Non-existent file
    ok, msg = RAGSecuritySanitizer.validate_upload(Path("non_existent_file.pdf"))
    assert ok is False
    assert "does not exist" in msg.lower()

    # Illegal extension on existing file
    bad_file = tmp_path / "malicious.exe"
    bad_file.write_text("dummy exe", encoding="utf-8")
    ok, msg = RAGSecuritySanitizer.validate_upload(bad_file)
    assert ok is False
    assert "not permitted" in msg

def test_sanitization_filename():
    assert RAGSecuritySanitizer.sanitize_filename("../../../etc/passwd") == "passwd"
    assert RAGSecuritySanitizer.sanitize_filename("C:\\Windows\\System32\\cmd.exe") == "cmd.exe"
    assert RAGSecuritySanitizer.sanitize_filename("valid_syllabus-2026.pdf") == "valid_syllabus-2026.pdf"