"""Regression tests for document parser failure diagnostics."""

import logging
import sys
from types import SimpleNamespace

from central_platform.rag.parsers import DocumentParserRouter


def test_pdf_parser_logs_failure_and_returns_empty_text(tmp_path, monkeypatch, caplog):
    pdf_path = tmp_path / "broken.pdf"
    pdf_path.write_bytes(b"not a valid pdf")

    def raise_pdf_error(_path):
        raise ValueError("invalid PDF structure")

    monkeypatch.setitem(
        sys.modules,
        "pypdf",
        SimpleNamespace(PdfReader=raise_pdf_error),
    )

    with caplog.at_level(logging.ERROR, logger="central_platform.rag.parsers"):
        result = DocumentParserRouter._parse_pdf(pdf_path)

    assert result == ""
    assert "Failed to parse PDF document" in caplog.text
    assert str(pdf_path) in caplog.text
    assert "invalid PDF structure" in caplog.text


def test_docx_parser_logs_failure_and_returns_empty_text(tmp_path, monkeypatch, caplog):
    docx_path = tmp_path / "broken.docx"
    docx_path.write_bytes(b"not a valid docx")

    def raise_docx_error(_path):
        raise ValueError("invalid DOCX package")

    monkeypatch.setitem(
        sys.modules,
        "docx",
        SimpleNamespace(Document=raise_docx_error),
    )

    with caplog.at_level(logging.ERROR, logger="central_platform.rag.parsers"):
        result = DocumentParserRouter._parse_docx(docx_path)

    assert result == ""
    assert "Failed to parse DOCX document" in caplog.text
    assert str(docx_path) in caplog.text
    assert "invalid DOCX package" in caplog.text
