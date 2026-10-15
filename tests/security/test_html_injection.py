"""Security tests verifying that user input, RAG cards, and document content

cannot execute or inject malicious HTML/JavaScript (Issue #9 fix verification).
"""
from __future__ import annotations

import html
import re
from pathlib import Path


def escape_html(text: str) -> str:
    """Python reference equivalent to index.html escapeHTML function."""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def format_markdown_safe(text: str) -> str:
    """Python reference equivalent to index.html formatMarkdown function."""
    if not text:
        return ""
    safe = escape_html(text)
    safe = re.sub(r"^### (.*$)", r'<h4 style="margin: 8px 0 4px 0; color: #38bdf8; font-size: 14px;">\1</h4>', safe, flags=re.MULTILINE)
    safe = re.sub(r"^## (.*$)", r'<h3 style="margin: 10px 0 4px 0; color: #38bdf8; font-size: 15px;">\1</h3>', safe, flags=re.MULTILINE)
    safe = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"\*(.*?)\*", r"<em>\1</em>", safe)
    safe = safe.replace("\n", "<br>")
    return safe


def test_script_tags_are_escaped():
    payload = "<script>alert('xss')</script>"
    rendered = format_markdown_safe(payload)
    assert "<script>" not in rendered
    assert "</script>" not in rendered
    assert "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in rendered


def test_img_onerror_is_escaped():
    payload = '<img src=x onerror="alert(document.cookie)">'
    rendered = format_markdown_safe(payload)
    assert "<img" not in rendered
    assert "&lt;img" in rendered
    assert "&quot;" in rendered


def test_svg_onload_is_escaped():
    payload = '<svg onload=alert("pwned")>'
    rendered = format_markdown_safe(payload)
    assert "<svg" not in rendered
    assert "&lt;svg" in rendered


def test_javascript_protocol_is_escaped():
    payload = '<a href="javascript:alert(1)">Click Here</a>'
    rendered = format_markdown_safe(payload)
    assert "<a href=" not in rendered
    assert "&lt;a href=" in rendered


def test_nested_markdown_with_xss_payload():
    payload = "**<script>alert('nested')</script>**"
    rendered = format_markdown_safe(payload)
    # Markdown bold formatting is preserved
    assert rendered.startswith("<strong>")
    assert rendered.endswith("</strong>")
    # But the inner script tag is completely escaped
    assert "<script>" not in rendered
    assert "&lt;script&gt;alert(&#39;nested&#39;)&lt;/script&gt;" in rendered


def test_evidence_card_dom_rendering_in_index_html():
    index_html = Path("app/ui/index.html").read_text(encoding="utf-8")
    # Ensure innerHTML is NOT used for evidence card title/content
    assert "cDiv.innerHTML = `" not in index_html
    # Ensure textContent is used for card rendering
    assert "tDiv.textContent = card.title" in index_html
    assert "bDiv.textContent = card.content" in index_html


def test_escape_html_present_in_index_html():
    index_html = Path("app/ui/index.html").read_text(encoding="utf-8")
    assert "function escapeHTML(" in index_html
    assert "escapeHTML(text)" in index_html or "escapeHTML(str)" in index_html
